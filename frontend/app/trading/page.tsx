"use client";

import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { useLanguage } from "@/contexts/LanguageContext";
import { encrypt, decrypt } from "@/lib/crypto";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertTriangle, ArrowLeft, ExternalLink, RefreshCw, Wifi, WifiOff } from "lucide-react";

interface Quote {
  code: string; name: string; open: number; high: number; low: number;
  close: number; change: number; change_rate: number; volume: number;
  total_volume: number; bid_price: number; ask_price: number;
  limit_up: number | null; limit_down: number | null; reference: number | null;
  timestamp: string; simulation: boolean;
}

interface Position {
  code: string; name: string; direction: string; quantity: number;
  price: number; last_price: number; pnl: number; yd_quantity: number;
}

interface Trade {
  trade_id: string; code: string; action: string; price: number;
  quantity: number; deal_quantity: number; status: string;
  order_datetime: string | null; deals: { price: number; quantity: number; ts: string }[];
}

interface Balance { date: string; acc_balance: number; simulation: boolean; }

const SIDECAR_PORT = 21322;

async function apiFetch(path: string, opts: RequestInit = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

function statusBadge(status: string) {
  const map: Record<string, string> = {
    Filled: "bg-green-100 text-green-800",
    PartFilled: "bg-yellow-100 text-yellow-800",
    Submitted: "bg-blue-100 text-blue-800",
    PendingSubmit: "bg-gray-100 text-gray-700",
    Cancelled: "bg-red-100 text-red-700",
    Failed: "bg-red-200 text-red-900",
  };
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-medium ${map[status] ?? "bg-gray-100 text-gray-700"}`}>
      {status}
    </span>
  );
}

export default function TradingPage() {
  const { t } = useLanguage();
  const searchParams = useSearchParams();

  // Pre-fill from analysis result query params
  const prefilledTicker  = searchParams.get("ticker")  ?? "";
  const prefilledAction  = searchParams.get("action")  ?? "BUY";
  const prefilledPrice   = searchParams.get("price")   ?? "";

  // Sidecar server state (shioaji-pro-app)
  const [serverRunning,  setServerRunning]  = useState(false);
  const [serverStarting, setServerStarting] = useState(false);
  const [serverStopping, setServerStopping] = useState(false);
  const [serverError,    setServerError]    = useState("");

  // Connection state — sessionId starts null to avoid SSR/client hydration mismatch
  const [apiKey,        setApiKey]        = useState("");
  const [secretKey,     setSecretKey]     = useState("");
  const [simulation,    setSimulation]    = useState(true);
  const [sessionId,     setSessionId]     = useState<string | null>(null);
  const [hasSavedCreds, setHasSavedCreds] = useState(false);
  const [accounts,      setAccounts]      = useState<object[]>([]);
  const [connecting,    setConnecting]    = useState(false);
  const [connError,     setConnError]     = useState("");

  // Quote state
  const [quoteTicker, setQuoteTicker] = useState(prefilledTicker);
  const [quote,       setQuote]       = useState<Quote | null>(null);
  const [quoteError,  setQuoteError]  = useState("");
  const [fetchingQuote, setFetchingQuote] = useState(false);

  // Order state
  const [orderTicker,    setOrderTicker]    = useState(prefilledTicker);
  const [orderAction,    setOrderAction]    = useState<"BUY" | "SELL">(
    prefilledAction.toUpperCase() === "SELL" ? "SELL" : "BUY"
  );
  const [orderPrice,     setOrderPrice]     = useState(prefilledPrice);
  const [orderQty,       setOrderQty]       = useState("1");
  const [orderPriceType, setOrderPriceType] = useState("LMT");
  const [orderType,      setOrderType]      = useState("ROD");
  const [placingOrder,   setPlacingOrder]   = useState(false);
  const [orderMsg,       setOrderMsg]       = useState("");

  // Positions / orders / balance
  const [positions,       setPositions]       = useState<Position[]>([]);
  const [orders,          setOrders]          = useState<Trade[]>([]);
  const [balance,         setBalance]         = useState<Balance | null>(null);
  const [loadingData,     setLoadingData]     = useState(false);

  const isConnected = !!sessionId;

  // Persist session_id in localStorage
  useEffect(() => {
    if (sessionId) localStorage.setItem("shioaji_session_id", sessionId);
    else localStorage.removeItem("shioaji_session_id");
  }, [sessionId]);

  // Load saved credentials and session on mount (client-only to avoid hydration mismatch)
  useEffect(() => {
    (async () => {
      try {
        const encKey = localStorage.getItem("shioaji_api_key");
        const encSec = localStorage.getItem("shioaji_secret_key");
        if (encKey) { setApiKey(await decrypt(encKey)); setHasSavedCreds(true); }
        if (encSec) setSecretKey(await decrypt(encSec));
      } catch { /* ignore decryption errors */ }
      const stored = localStorage.getItem("shioaji_session_id");
      if (stored) setSessionId(stored);
    })();
  }, []);

  // Check sidecar server status on mount
  useEffect(() => {
    apiFetch("/api/shioaji-server/status")
      .then(d => setServerRunning(d.running && d.healthy))
      .catch(() => {});
  }, []);

  // ── Sidecar server management ─────────────────────────────────────────────

  const handleStartServer = async () => {
    if (!apiKey || !secretKey) { setServerError("Please enter API key and secret key below."); return; }
    setServerStarting(true); setServerError("");
    try {
      await apiFetch("/api/shioaji-server/start", {
        method: "POST",
        body: JSON.stringify({ api_key: apiKey, secret_key: secretKey, simulation }),
      });
      setServerRunning(true);
      localStorage.setItem("shioaji_api_key", await encrypt(apiKey));
      localStorage.setItem("shioaji_secret_key", await encrypt(secretKey));
      setHasSavedCreds(true);
    } catch (e: unknown) {
      setServerError(e instanceof Error ? e.message : String(e));
    } finally {
      setServerStarting(false);
    }
  };

  const handleStopServer = async () => {
    setServerStopping(true); setServerError("");
    try {
      await apiFetch("/api/shioaji-server/stop", { method: "POST" });
      setServerRunning(false);
    } catch (e: unknown) {
      setServerError(e instanceof Error ? e.message : String(e));
    } finally {
      setServerStopping(false);
    }
  };

  // Auto-fill order ticker/price from URL params
  useEffect(() => {
    if (prefilledTicker) { setOrderTicker(prefilledTicker); setQuoteTicker(prefilledTicker); }
    if (prefilledPrice)  setOrderPrice(prefilledPrice);
    if (prefilledAction) setOrderAction(prefilledAction.toUpperCase() === "SELL" ? "SELL" : "BUY");
  }, [prefilledTicker, prefilledPrice, prefilledAction]);

  // ── Connect / Disconnect ─────────────────────────────────────────────────

  const handleConnect = async () => {
    if (!apiKey || !secretKey) { setConnError("Please enter API key and secret key."); return; }
    setConnecting(true); setConnError("");
    try {
      const data = await apiFetch("/api/trading/connect", {
        method: "POST",
        body: JSON.stringify({ api_key: apiKey, secret_key: secretKey, simulation }),
      });
      setSessionId(data.session_id);
      setAccounts(data.accounts ?? []);
      localStorage.setItem("shioaji_api_key", await encrypt(apiKey));
      localStorage.setItem("shioaji_secret_key", await encrypt(secretKey));
      setHasSavedCreds(true);
    } catch (e: unknown) {
      setConnError(e instanceof Error ? e.message : String(e));
    } finally {
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!sessionId) return;
    try { await apiFetch(`/api/trading/connect/${sessionId}`, { method: "DELETE" }); }
    catch { /* ignore */ }
    setSessionId(null); setAccounts([]); setPositions([]); setOrders([]); setBalance(null);
  };

  // ── Quote ────────────────────────────────────────────────────────────────

  const fetchQuote = useCallback(async () => {
    if (!sessionId || !quoteTicker) return;
    setFetchingQuote(true); setQuoteError("");
    try {
      const data = await apiFetch(`/api/trading/quote/${quoteTicker}?session_id=${sessionId}`);
      setQuote(data);
    } catch (e: unknown) {
      setQuoteError(e instanceof Error ? e.message : String(e));
      if (String(e).includes("expired")) setSessionId(null);
    } finally { setFetchingQuote(false); }
  }, [sessionId, quoteTicker]);

  // ── Account data ─────────────────────────────────────────────────────────

  const fetchAccountData = useCallback(async () => {
    if (!sessionId) return;
    setLoadingData(true);
    try {
      const [pos, ord, bal] = await Promise.all([
        apiFetch(`/api/trading/positions?session_id=${sessionId}`),
        apiFetch(`/api/trading/orders?session_id=${sessionId}`),
        apiFetch(`/api/trading/balance?session_id=${sessionId}`),
      ]);
      setPositions(pos);
      setOrders(ord);
      setBalance(bal);
    } catch (e: unknown) {
      if (String(e).includes("expired")) setSessionId(null);
    } finally { setLoadingData(false); }
  }, [sessionId]);

  // ── Order placement ──────────────────────────────────────────────────────

  const handlePlaceOrder = async () => {
    if (!sessionId) return;
    const price = parseFloat(orderPrice);
    const qty   = parseInt(orderQty, 10);
    if (!orderTicker) { setOrderMsg("Please enter a ticker."); return; }
    if (isNaN(price) || price <= 0) { setOrderMsg("Please enter a valid price."); return; }
    if (isNaN(qty)   || qty   <= 0) { setOrderMsg("Please enter a valid quantity."); return; }

    setPlacingOrder(true); setOrderMsg("");
    try {
      const trade = await apiFetch("/api/trading/order", {
        method: "POST",
        body: JSON.stringify({
          session_id:  sessionId,
          ticker:      orderTicker,
          action:      orderAction,
          price,
          quantity:    qty,
          price_type:  orderPriceType,
          order_type:  orderType,
        }),
      });
      setOrderMsg(`✅ Order placed: ${trade.trade_id}`);
      await fetchAccountData();
    } catch (e: unknown) {
      setOrderMsg(`❌ ${e instanceof Error ? e.message : String(e)}`);
      if (String(e).includes("expired")) setSessionId(null);
    } finally { setPlacingOrder(false); }
  };

  const handleCancelOrder = async (tradeId: string) => {
    if (!sessionId) return;
    try {
      await apiFetch(`/api/trading/order/${tradeId}?session_id=${sessionId}`, { method: "DELETE" });
      await fetchAccountData();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  // ── Render ───────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-card">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center gap-4">
          <Link href="/analysis">
            <Button variant="ghost" size="sm"><ArrowLeft className="h-4 w-4 mr-1" /> Back</Button>
          </Link>
          <div className="flex-1">
            <h1 className="text-xl font-bold">{t.trading.title}</h1>
            <p className="text-sm text-muted-foreground">{t.trading.subtitle}</p>
          </div>
          <div className="flex items-center gap-2" suppressHydrationWarning>
            {isConnected
              ? <><Wifi className="h-4 w-4 text-green-500" /><Badge variant="outline" className="text-green-600">{t.trading.connected}</Badge></>
              : <><WifiOff className="h-4 w-4 text-gray-400" /><Badge variant="outline" className="text-gray-400">{t.trading.disconnected}</Badge></>
            }
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">

        {/* Taiwan-only notice */}
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{t.trading.twStockOnly}</AlertDescription>
        </Alert>

        {/* Always-visible credentials card */}
        <Card>
          <CardHeader>
            <CardTitle>{t.trading.connect}</CardTitle>
            <CardDescription>Sinopac Securities (永豐金) — used by both Pro Terminal and Simple Trading below</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Simulation toggle */}
            <div className="flex items-center gap-3 p-3 rounded-lg border">
              <Switch checked={simulation} onCheckedChange={setSimulation} id="simulation-toggle" />
              <div>
                <Label htmlFor="simulation-toggle" className="font-medium">{t.trading.simulation}</Label>
                <p className="text-xs text-muted-foreground">{t.trading.simulationDesc}</p>
              </div>
            </div>

            {!simulation && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription className="font-bold">{t.trading.liveWarning}</AlertDescription>
              </Alert>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <Label>{t.trading.apiKey}</Label>
                <Input
                  type="password"
                  placeholder={t.trading.apiKeyPlaceholder}
                  value={apiKey}
                  onChange={e => setApiKey(e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <Label>{t.trading.secretKey}</Label>
                <Input
                  type="password"
                  placeholder={t.trading.secretKeyPlaceholder}
                  value={secretKey}
                  onChange={e => setSecretKey(e.target.value)}
                />
              </div>
            </div>

            {hasSavedCreds && (
              <button
                type="button"
                className="text-xs text-muted-foreground underline hover:text-destructive"
                onClick={() => {
                  localStorage.removeItem("shioaji_api_key");
                  localStorage.removeItem("shioaji_secret_key");
                  setApiKey(""); setSecretKey(""); setHasSavedCreds(false);
                }}
              >
                Clear saved credentials
              </button>
            )}
          </CardContent>
        </Card>

        {/* Shioaji Pro Terminal card */}
        <Card className={serverRunning ? "border-blue-400 bg-blue-50/40 dark:bg-blue-950/20" : ""}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Shioaji Pro Terminal</CardTitle>
                <CardDescription>Full trading terminal — opens the sidecar&apos;s built-in dashboard (port {SIDECAR_PORT})</CardDescription>
              </div>
              {serverRunning
                ? <Badge className="bg-green-100 text-green-800 border-green-300">Server running · port 21322</Badge>
                : <Badge variant="outline" className="text-gray-500">Server stopped</Badge>
              }
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {serverError && (
              <Alert variant="destructive">
                <AlertDescription>{serverError}</AlertDescription>
              </Alert>
            )}
            {serverRunning ? (
              <div className="flex gap-3">
                <Button
                  className="flex-1 bg-blue-600 hover:bg-blue-700"
                  onClick={() => window.open(`http://localhost:${SIDECAR_PORT}`, "_blank")}
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Open Pro Terminal
                </Button>
                <Button variant="outline" onClick={handleStopServer} disabled={serverStopping}>
                  {serverStopping ? "Stopping…" : "Stop Server"}
                </Button>
              </div>
            ) : (
              <Button
                className="w-full"
                onClick={handleStartServer}
                disabled={serverStarting}
              >
                {serverStarting ? "Starting server — loading contracts, please wait (up to 60 s)…" : "Start Pro Terminal Server"}
              </Button>
            )}
          </CardContent>
        </Card>

        <div className="relative flex items-center gap-3">
          <div className="flex-1 border-t" />
          <span className="text-xs text-muted-foreground">or use simple trading below</span>
          <div className="flex-1 border-t" />
        </div>

        {/* Simple trading — connect button or connected tabs */}
        {!isConnected ? (
          <Card>
            <CardHeader>
              <CardTitle>Simple Trading</CardTitle>
              <CardDescription>Basic quote / order / positions via Python shioaji library</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {connError && (
                <Alert variant="destructive">
                  <AlertDescription>{connError}</AlertDescription>
                </Alert>
              )}
              <Button
                onClick={handleConnect}
                disabled={connecting}
                className="w-full"
                onKeyDown={e => e.key === "Enter" && handleConnect()}
              >
                {connecting ? t.trading.connecting : t.trading.connect}
              </Button>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Connected banner */}
            <div className="flex items-center justify-between p-3 rounded-lg border bg-green-50 dark:bg-green-950/20">
              <div className="text-sm">
                <span className="font-medium text-green-700 dark:text-green-400">{t.trading.connectSuccess}</span>
                {accounts.length > 0 && (
                  <span className="ml-2 text-muted-foreground">
                    {(accounts[0] as Record<string, string>).account_id}
                  </span>
                )}
                {simulation && <Badge className="ml-2 bg-yellow-100 text-yellow-800 border-yellow-300">SIM</Badge>}
              </div>
              <Button variant="outline" size="sm" onClick={handleDisconnect}>{t.trading.disconnect}</Button>
            </div>

            <Tabs defaultValue="quote">
              <TabsList className="grid grid-cols-4 w-full">
                <TabsTrigger value="quote">📈 {t.trading.quote}</TabsTrigger>
                <TabsTrigger value="order">🛒 {t.trading.placeOrder}</TabsTrigger>
                <TabsTrigger value="positions" onClick={fetchAccountData}>📊 {t.trading.positions}</TabsTrigger>
                <TabsTrigger value="orders" onClick={fetchAccountData}>📋 {t.trading.todayOrders}</TabsTrigger>
              </TabsList>

              {/* ── Quote tab ──────────────────────────────────────────── */}
              <TabsContent value="quote">
                <Card>
                  <CardHeader><CardTitle>{t.trading.quote}</CardTitle></CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex gap-2">
                      <Input
                        placeholder={t.trading.tickerInput}
                        value={quoteTicker}
                        onChange={e => setQuoteTicker(e.target.value.trim())}
                        onKeyDown={e => e.key === "Enter" && fetchQuote()}
                        className="max-w-xs"
                      />
                      <Button onClick={fetchQuote} disabled={fetchingQuote || !quoteTicker}>
                        <RefreshCw className={`h-4 w-4 mr-1 ${fetchingQuote ? "animate-spin" : ""}`} />
                        {t.trading.fetchQuote}
                      </Button>
                    </div>

                    {quoteError && <p className="text-sm text-destructive">{quoteError}</p>}

                    {quote && (
                      <div className="space-y-3">
                        <div className="flex items-baseline gap-3">
                          <span className="text-3xl font-bold">{quote.close}</span>
                          <span className={`text-lg font-medium ${quote.change >= 0 ? "text-green-600" : "text-red-600"}`}>
                            {quote.change >= 0 ? "+" : ""}{quote.change} ({quote.change_rate >= 0 ? "+" : ""}{quote.change_rate?.toFixed(2)}%)
                          </span>
                          <span className="text-sm text-muted-foreground">{quote.name} ({quote.code})</span>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                          {[
                            { label: "Open",         value: quote.open },
                            { label: "High",         value: quote.high },
                            { label: "Low",          value: quote.low },
                            { label: t.trading.volume, value: quote.total_volume?.toLocaleString() },
                            { label: t.trading.bidAsk, value: `${quote.bid_price} / ${quote.ask_price}` },
                            { label: t.trading.limitUp,   value: quote.limit_up },
                            { label: t.trading.limitDown, value: quote.limit_down },
                            { label: "Reference",    value: quote.reference },
                          ].map(({ label, value }) => (
                            <div key={label} className="rounded-lg border p-3">
                              <div className="text-xs text-muted-foreground">{label}</div>
                              <div className="font-medium">{value ?? "—"}</div>
                            </div>
                          ))}
                        </div>

                        <p className="text-xs text-muted-foreground">
                          {quote.timestamp}{quote.simulation && " · SIM"}
                        </p>

                        {/* Quick-fill order button */}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => { setOrderTicker(quote.code); setOrderPrice(String(quote.close)); }}
                        >
                          → Use in Order Form
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* ── Order tab ──────────────────────────────────────────── */}
              <TabsContent value="order">
                <Card>
                  <CardHeader>
                    <CardTitle>{t.trading.placeOrder}</CardTitle>
                    {simulation && <CardDescription className="text-yellow-600">Simulation mode — no real money</CardDescription>}
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-1">
                        <Label>Ticker</Label>
                        <Input
                          placeholder="e.g. 2330"
                          value={orderTicker}
                          onChange={e => setOrderTicker(e.target.value.trim())}
                        />
                      </div>

                      <div className="space-y-1">
                        <Label>{t.trading.action}</Label>
                        <div className="flex gap-2">
                          <Button
                            variant={orderAction === "BUY" ? "default" : "outline"}
                            className={orderAction === "BUY" ? "bg-green-600 hover:bg-green-700 flex-1" : "flex-1"}
                            onClick={() => setOrderAction("BUY")}
                          >{t.trading.buy}</Button>
                          <Button
                            variant={orderAction === "SELL" ? "default" : "outline"}
                            className={orderAction === "SELL" ? "bg-red-600 hover:bg-red-700 flex-1" : "flex-1"}
                            onClick={() => setOrderAction("SELL")}
                          >{t.trading.sell}</Button>
                        </div>
                      </div>

                      <div className="space-y-1">
                        <Label>{t.trading.price}</Label>
                        <Input
                          type="number" step="0.1" min="0"
                          placeholder="e.g. 500.0"
                          value={orderPrice}
                          onChange={e => setOrderPrice(e.target.value)}
                        />
                      </div>

                      <div className="space-y-1">
                        <Label>{t.trading.quantity} <span className="text-xs text-muted-foreground">({t.trading.quantityHint})</span></Label>
                        <Input
                          type="number" min="1" step="1"
                          value={orderQty}
                          onChange={e => setOrderQty(e.target.value)}
                        />
                      </div>

                      <div className="space-y-1">
                        <Label>{t.trading.priceType}</Label>
                        <Select value={orderPriceType} onValueChange={setOrderPriceType}>
                          <SelectTrigger><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="LMT">{t.trading.lmt}</SelectItem>
                            <SelectItem value="MKT">{t.trading.mkt}</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-1">
                        <Label>{t.trading.orderType}</Label>
                        <Select value={orderType} onValueChange={setOrderType}>
                          <SelectTrigger><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="ROD">{t.trading.rod}</SelectItem>
                            <SelectItem value="IOC">{t.trading.ioc}</SelectItem>
                            <SelectItem value="FOK">{t.trading.fok}</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    {orderMsg && (
                      <p className={`text-sm ${orderMsg.startsWith("✅") ? "text-green-600" : "text-destructive"}`}>
                        {orderMsg}
                      </p>
                    )}

                    <Button
                      onClick={handlePlaceOrder}
                      disabled={placingOrder}
                      className={`w-full ${orderAction === "BUY" ? "bg-green-600 hover:bg-green-700" : "bg-red-600 hover:bg-red-700"}`}
                    >
                      {placingOrder ? "Placing…" : `${t.trading.submitOrder} — ${orderAction === "BUY" ? t.trading.buy : t.trading.sell} ${orderTicker || "?"} ×${orderQty} @ ${orderPrice || "?"}`}
                    </Button>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* ── Positions tab ───────────────────────────────────────── */}
              <TabsContent value="positions">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle>{t.trading.positions}</CardTitle>
                    <Button variant="outline" size="sm" onClick={fetchAccountData} disabled={loadingData}>
                      <RefreshCw className={`h-4 w-4 ${loadingData ? "animate-spin" : ""}`} />
                    </Button>
                  </CardHeader>
                  <CardContent>
                    {positions.length === 0
                      ? <p className="text-muted-foreground text-sm">{t.trading.noPositions}</p>
                      : (
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Code</TableHead>
                              <TableHead>{t.trading.direction}</TableHead>
                              <TableHead className="text-right">{t.trading.posQuantity}</TableHead>
                              <TableHead className="text-right">{t.trading.avgCost}</TableHead>
                              <TableHead className="text-right">{t.trading.lastPrice2}</TableHead>
                              <TableHead className="text-right">{t.trading.unrealizedPnl}</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {positions.map(p => (
                              <TableRow key={p.code}>
                                <TableCell className="font-medium">{p.code}<span className="text-xs text-muted-foreground ml-1">{p.name}</span></TableCell>
                                <TableCell>
                                  <span className={p.direction === "Buy" ? "text-green-600" : "text-red-600"}>
                                    {p.direction === "Buy" ? t.trading.buy : t.trading.sell}
                                  </span>
                                </TableCell>
                                <TableCell className="text-right">{p.quantity}</TableCell>
                                <TableCell className="text-right">{p.price?.toFixed(2)}</TableCell>
                                <TableCell className="text-right">{p.last_price?.toFixed(2)}</TableCell>
                                <TableCell className={`text-right font-medium ${p.pnl >= 0 ? "text-green-600" : "text-red-600"}`}>
                                  {p.pnl >= 0 ? "+" : ""}{p.pnl?.toFixed(0)}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      )
                    }
                  </CardContent>
                </Card>

                {/* Balance */}
                {balance && (
                  <Card className="mt-4">
                    <CardContent className="pt-4 flex gap-6">
                      <div>
                        <div className="text-xs text-muted-foreground">{t.trading.accBalance}</div>
                        <div className="text-xl font-bold">NT$ {balance.acc_balance?.toLocaleString()}</div>
                      </div>
                      <div>
                        <div className="text-xs text-muted-foreground">{t.trading.asOf}</div>
                        <div className="text-sm">{balance.date}</div>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </TabsContent>

              {/* ── Orders tab ──────────────────────────────────────────── */}
              <TabsContent value="orders">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle>{t.trading.todayOrders}</CardTitle>
                    <Button variant="outline" size="sm" onClick={fetchAccountData} disabled={loadingData}>
                      <RefreshCw className={`h-4 w-4 ${loadingData ? "animate-spin" : ""}`} />
                    </Button>
                  </CardHeader>
                  <CardContent>
                    {orders.length === 0
                      ? <p className="text-muted-foreground text-sm">{t.trading.noOrders}</p>
                      : (
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>{t.trading.orderId}</TableHead>
                              <TableHead>Code</TableHead>
                              <TableHead>{t.trading.action}</TableHead>
                              <TableHead className="text-right">Price</TableHead>
                              <TableHead className="text-right">Qty</TableHead>
                              <TableHead className="text-right">{t.trading.dealQty}</TableHead>
                              <TableHead>{t.trading.orderStatus}</TableHead>
                              <TableHead></TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {orders.map(o => (
                              <TableRow key={o.trade_id}>
                                <TableCell className="font-mono text-xs">{o.trade_id.slice(0, 8)}…</TableCell>
                                <TableCell className="font-medium">{o.code}</TableCell>
                                <TableCell className={o.action === "Buy" ? "text-green-600" : "text-red-600"}>
                                  {o.action === "Buy" ? t.trading.buy : t.trading.sell}
                                </TableCell>
                                <TableCell className="text-right">{o.price}</TableCell>
                                <TableCell className="text-right">{o.quantity}</TableCell>
                                <TableCell className="text-right">{o.deal_quantity}</TableCell>
                                <TableCell>{statusBadge(o.status)}</TableCell>
                                <TableCell>
                                  {["Submitted", "PendingSubmit", "PartFilled"].includes(o.status) && (
                                    <Button
                                      variant="outline" size="sm"
                                      onClick={() => handleCancelOrder(o.trade_id)}
                                    >{t.trading.cancelOrder}</Button>
                                  )}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      )
                    }
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </>
        )}
      </div>
    </div>
  );
}
