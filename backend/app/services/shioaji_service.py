"""
Shioaji (Sinopac Securities) trading service.
Manages persistent Shioaji sessions and exposes trading operations.
All blocking Shioaji calls must be wrapped with asyncio.to_thread() at the route layer.
"""

import threading
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

try:
    import shioaji as sj
    _HAS_SHIOAJI = True
except ImportError:
    _HAS_SHIOAJI = False

logger = logging.getLogger(__name__)

SESSION_TIMEOUT_HOURS = 8


class ShioajiSession:
    def __init__(self, session_id: str, api, accounts: list, simulation: bool):
        self.session_id = session_id
        self.api = api
        self.accounts = accounts
        self.simulation = simulation
        self.created_at = datetime.now()
        self.last_used = datetime.now()

    def touch(self):
        self.last_used = datetime.now()

    @property
    def is_expired(self) -> bool:
        return datetime.now() - self.last_used > timedelta(hours=SESSION_TIMEOUT_HOURS)

    def account_info(self) -> list:
        result = []
        for acc in self.accounts:
            result.append({
                "account_id": getattr(acc, "account_id", str(acc)),
                "broker_id":  getattr(acc, "broker_id",  ""),
                "username":   getattr(acc, "username",   ""),
                "signed":     getattr(acc, "signed",     False),
            })
        return result


class ShioajiSessionManager:
    def __init__(self):
        self._sessions: Dict[str, ShioajiSession] = {}
        self._lock = threading.Lock()

    # ── session lifecycle ────────────────────────────────────────────────────

    def _cleanup_expired(self):
        with self._lock:
            expired = [sid for sid, s in self._sessions.items() if s.is_expired]
        for sid in expired:
            self.delete_session(sid)

    def get_session(self, session_id: str) -> ShioajiSession:
        self._cleanup_expired()
        with self._lock:
            sess = self._sessions.get(session_id)
        if sess is None:
            raise ValueError(f"Session '{session_id}' not found or expired. Please reconnect.")
        sess.touch()
        return sess

    def create_session(self, api_key: str, secret_key: str, simulation: bool = True) -> ShioajiSession:
        if not _HAS_SHIOAJI:
            raise RuntimeError("shioaji package not installed. Run: uv pip install shioaji")

        api = sj.Shioaji(simulation=simulation)
        try:
            accounts = api.login(
                api_key=api_key,
                secret_key=secret_key,
                fetch_contract=True,
                contracts_timeout=30000,
                subscribe_trade=True,
            )
        except Exception as e:
            raise RuntimeError(f"Shioaji login failed: {e}")

        session_id = str(uuid.uuid4())
        sess = ShioajiSession(session_id, api, accounts, simulation)
        with self._lock:
            self._sessions[session_id] = sess
        logger.info(f"[shioaji] session {session_id[:8]}… created, simulation={simulation}")
        return sess

    def delete_session(self, session_id: str):
        with self._lock:
            sess = self._sessions.pop(session_id, None)
        if sess:
            try:
                sess.api.logout()
            except Exception:
                pass
            logger.info(f"[shioaji] session {session_id[:8]}… disconnected")

    # ── market data ──────────────────────────────────────────────────────────

    def get_quote(self, session: ShioajiSession, ticker: str) -> dict:
        try:
            contract = session.api.Contracts.Stocks[ticker]
        except (KeyError, AttributeError, Exception):
            raise ValueError(
                f"Ticker '{ticker}' not found in Taiwan stock contracts. "
                "Shioaji only supports Taiwan stocks (TSE/OTC). Use a numeric code like '2330'."
            )

        snapshots = session.api.snapshots([contract])
        if not snapshots:
            raise RuntimeError(f"No snapshot data for {ticker}")

        snap = snapshots[0]
        return {
            "code":         snap.code,
            "name":         getattr(contract, "name", ticker),
            "open":         snap.open,
            "high":         snap.high,
            "low":          snap.low,
            "close":        snap.close,
            "change":       snap.change_price,
            "change_rate":  snap.change_rate,
            "volume":       snap.volume,
            "total_volume": snap.total_volume,
            "bid_price":    snap.buy_price,
            "ask_price":    snap.sell_price,
            "limit_up":     getattr(contract, "limit_up",   None),
            "limit_down":   getattr(contract, "limit_down", None),
            "reference":    getattr(contract, "reference",  None),
            "timestamp":    str(snap.ts),
            "simulation":   session.simulation,
        }

    # ── account ──────────────────────────────────────────────────────────────

    def get_balance(self, session: ShioajiSession) -> dict:
        try:
            balance = session.api.account_balance(session.api.stock_account)
            return {
                "date":        balance.date,
                "acc_balance": balance.acc_balance,
                "simulation":  session.simulation,
            }
        except Exception as e:
            raise RuntimeError(f"Failed to fetch balance: {e}")

    def get_positions(self, session: ShioajiSession) -> list:
        try:
            positions = session.api.list_positions(session.api.stock_account)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch positions: {e}")

        result = []
        for p in positions:
            try:
                contract = session.api.Contracts.Stocks[p.code]
                name = getattr(contract, "name", p.code)
            except Exception:
                name = p.code

            result.append({
                "code":        p.code,
                "name":        name,
                "direction":   p.direction.value,
                "quantity":    p.quantity,
                "price":       p.price,
                "last_price":  p.last_price,
                "pnl":         p.pnl,
                "yd_quantity": getattr(p, "yd_quantity", 0),
            })
        return result

    # ── orders ───────────────────────────────────────────────────────────────

    def place_order(
        self,
        session: ShioajiSession,
        ticker: str,
        action: str,
        price: float,
        quantity: int,
        price_type: str = "LMT",
        order_type: str = "ROD",
    ) -> dict:
        try:
            contract = session.api.Contracts.Stocks[ticker]
        except (KeyError, Exception):
            raise ValueError(f"Ticker '{ticker}' not found in Taiwan stock contracts")

        action_enum = sj.Action.Buy if action.upper() == "BUY" else sj.Action.Sell

        pt_map = {"LMT": sj.StockPriceType.LMT, "MKT": sj.StockPriceType.MKT}
        price_type_enum = pt_map.get(price_type.upper(), sj.StockPriceType.LMT)

        ot_map = {
            "ROD": sj.OrderType.ROD,
            "IOC": sj.OrderType.IOC,
            "FOK": sj.OrderType.FOK,
        }
        order_type_enum = ot_map.get(order_type.upper(), sj.OrderType.ROD)

        order = sj.StockOrder(
            action=action_enum,
            price=price,
            quantity=quantity,
            price_type=price_type_enum,
            order_type=order_type_enum,
            order_lot=sj.StockOrderLot.Common,
            account=session.api.stock_account,
        )

        try:
            trade = session.api.place_order(contract, order)
        except Exception as e:
            raise RuntimeError(f"Order placement failed: {e}")

        return _trade_to_dict(trade)

    def cancel_order(self, session: ShioajiSession, trade_id: str) -> dict:
        try:
            session.api.update_status(session.api.stock_account)
            trades = session.api.list_trades()
        except Exception as e:
            raise RuntimeError(f"Failed to fetch trades: {e}")

        target = next((t for t in trades if t.status.id == trade_id), None)
        if target is None:
            raise ValueError(f"Trade '{trade_id}' not found")

        try:
            result = session.api.cancel_order(target)
        except Exception as e:
            raise RuntimeError(f"Cancel failed: {e}")

        return _trade_to_dict(result)

    def list_orders(self, session: ShioajiSession) -> list:
        try:
            session.api.update_status(session.api.stock_account)
            trades = session.api.list_trades()
        except Exception as e:
            raise RuntimeError(f"Failed to fetch orders: {e}")
        return [_trade_to_dict(t) for t in trades]


# ── helpers ──────────────────────────────────────────────────────────────────

def _trade_to_dict(trade) -> dict:
    status = trade.status
    deals = [
        {"price": d.price, "quantity": d.quantity, "ts": str(d.ts)}
        for d in (getattr(status, "deals", None) or [])
    ]
    return {
        "trade_id":      status.id,
        "code":          trade.contract.code,
        "action":        trade.order.action.value,
        "price":         trade.order.price,
        "quantity":      trade.order.quantity,
        "deal_quantity": getattr(status, "deal_quantity", 0),
        "status":        status.status.value,
        "order_datetime": str(status.order_datetime) if getattr(status, "order_datetime", None) else None,
        "deals":         deals,
    }


# ── global singleton ──────────────────────────────────────────────────────────

shioaji_manager = ShioajiSessionManager()
