from typing import Annotated

# 從特定供應商的模組匯入
from .local import get_YFin_data, get_finnhub_news, get_finnhub_company_insider_sentiment, get_finnhub_company_insider_transactions, get_simfin_balance_sheet, get_simfin_cashflow, get_simfin_income_statements, get_reddit_global_news, get_reddit_company_news
from .y_finance import get_YFin_data_online, get_stock_stats_indicators_window, get_balance_sheet as get_yfinance_balance_sheet, get_cashflow as get_yfinance_cashflow, get_income_statement as get_yfinance_income_statement, get_insider_transactions as get_yfinance_insider_transactions, get_fundamentals as get_yfinance_fundamentals
from .google import get_google_news
from .openai import get_stock_news_openai, get_global_news_openai, get_fundamentals_openai
from .alpha_vantage import (
    get_stock as get_alpha_vantage_stock,
    get_indicator as get_alpha_vantage_indicator,
    get_fundamentals as get_alpha_vantage_fundamentals,
    get_balance_sheet as get_alpha_vantage_balance_sheet,
    get_cashflow as get_alpha_vantage_cashflow,
    get_income_statement as get_alpha_vantage_income_statement,
    get_insider_transactions as get_alpha_vantage_insider_transactions,
    get_news as get_alpha_vantage_news
)
from .alpha_vantage_common import AlphaVantageRateLimitError

# FinMind 台灣股市資料供應商
from .finmind import (
    get_stock as get_finmind_stock,
    get_indicator as get_finmind_indicator,
    get_fundamentals as get_finmind_fundamentals,
    get_balance_sheet as get_finmind_balance_sheet,
    get_cashflow as get_finmind_cashflow,
    get_income_statement as get_finmind_income_statement,
    get_news as get_finmind_news,
    get_global_news as get_finmind_global_news,
    get_insider_sentiment as get_finmind_insider_sentiment,
    get_insider_transactions as get_finmind_insider_transactions,
    FinMindRateLimitError,
)

# 設定和路由邏輯
from .config import get_config

# 按類別組織的工具
TOOLS_CATEGORIES = {
    "core_stock_apis": {
        "description": "OHLCV 股價數據",
        "tools": [
            "get_stock_data"
        ]
    },
    "technical_indicators": {
        "description": "技術分析指標",
        "tools": [
            "get_indicators"
        ]
    },
    "fundamental_data": {
        "description": "公司基本面",
        "tools": [
            "get_fundamentals",
            "get_balance_sheet",
            "get_cashflow",
            "get_income_statement"
        ]
    },
    "news_data": {
        "description": "新聞 (公開/內部人士，原始/處理後)",
        "tools": [
            "get_news",
            "get_global_news",
            "get_insider_sentiment",
            "get_insider_transactions",
        ]
    }
}

VENDOR_LIST = [
    "local",
    "yfinance",
    "openai",
    "google",
    "alpha_vantage",
    "finmind",  # 台灣股市資料供應商
]

# 方法與其特定供應商實現的映射
VENDOR_METHODS = {
    # 核心股票 API
    "get_stock_data": {
        "alpha_vantage": get_alpha_vantage_stock,
        "yfinance": get_YFin_data_online,
        "local": get_YFin_data,
        "finmind": get_finmind_stock,  # 台股資料
    },
    # 技術指標
    "get_indicators": {
        "alpha_vantage": get_alpha_vantage_indicator,
        "yfinance": get_stock_stats_indicators_window,
        "local": get_stock_stats_indicators_window,
        "finmind": get_finmind_indicator,  # 台股技術指標/籌碼面
    },
    # 基本面數據
    "get_fundamentals": {
        "alpha_vantage": get_alpha_vantage_fundamentals,
        "openai": get_fundamentals_openai,
        "yfinance": get_yfinance_fundamentals,
        "finmind": get_finmind_fundamentals,  # 台股基本面
    },
    "get_balance_sheet": {
        "alpha_vantage": get_alpha_vantage_balance_sheet,
        "yfinance": get_yfinance_balance_sheet,
        "local": get_simfin_balance_sheet,
        "finmind": get_finmind_balance_sheet,  # 台股資產負債表
    },
    "get_cashflow": {
        "alpha_vantage": get_alpha_vantage_cashflow,
        "yfinance": get_yfinance_cashflow,
        "local": get_simfin_cashflow,
        "finmind": get_finmind_cashflow,  # 台股現金流量表
    },
    "get_income_statement": {
        "alpha_vantage": get_alpha_vantage_income_statement,
        "yfinance": get_yfinance_income_statement,
        "local": get_simfin_income_statements,
        "finmind": get_finmind_income_statement,  # 台股損益表
    },
    # 新聞數據
    "get_news": {
        "alpha_vantage": get_alpha_vantage_news,
        "openai": get_stock_news_openai,
        "google": get_google_news,
        "local": [get_finnhub_news, get_reddit_company_news, get_google_news],
        "finmind": get_finmind_news,  # 台股公告/法人動態
    },
    "get_global_news": {
        "openai": get_global_news_openai,
        "local": get_reddit_global_news,
        "finmind": get_finmind_global_news,  # 台股市場動態
    },
    "get_insider_sentiment": {
        "local": get_finnhub_company_insider_sentiment,
        "finmind": get_finmind_insider_sentiment,  # 台股法人情緒
    },
    "get_insider_transactions": {
        "alpha_vantage": get_alpha_vantage_insider_transactions,
        "yfinance": get_yfinance_insider_transactions,
        "local": get_finnhub_company_insider_transactions,
        "finmind": get_finmind_insider_transactions,  # 台股法人交易
    },
}

def get_category_for_method(method: str) -> str:
    """獲取包含指定方法的類別。"""
    for category, info in TOOLS_CATEGORIES.items():
        if method in info["tools"]:
            return category
    raise ValueError(f"在任何類別中都找不到方法 '{method}'")

def get_vendor(category: str, method: str = None) -> str:
    """
    獲取數據類別或特定工具方法的已設定供應商。
    工具級別的設定優先於類別級別。
    """
    config = get_config()

    # 首先檢查工具級別的設定 (如果提供了方法)
    if method:
        tool_vendors = config.get("tool_vendors", {})
        if method in tool_vendors:
            return tool_vendors[method]

    # 回退到類別級別的設定
    return config.get("data_vendors", {}).get(category, "default")

def route_to_vendor(method: str, *args, **kwargs):
    """將方法調用路由到具有備援支援的適當供應商實現。"""
    category = get_category_for_method(method)
    vendor_config = get_vendor(category, method)

    # 處理以逗號分隔的供應商
    primary_vendors = [v.strip() for v in vendor_config.split(',')]

    if method not in VENDOR_METHODS:
        raise ValueError(f"不支援方法 '{method}'")

    # 獲取此方法所有可用供應商以進行備援
    all_available_vendors = list(VENDOR_METHODS[method].keys())
    
    # 建立備援供應商列表：主要供應商優先，然後是其餘供應商作為備援
    fallback_vendors = primary_vendors.copy()
    for vendor in all_available_vendors:
        if vendor not in fallback_vendors:
            fallback_vendors.append(vendor)

    primary_str = " → ".join(primary_vendors)
    fallback_str = " → ".join(fallback_vendors)
    print(f"[vendor] {method} - primary: [{primary_str}] | fallback order: [{fallback_str}]")

    results = []
    vendor_attempt_count = 0
    any_primary_vendor_attempted = False
    successful_vendor = None

    for vendor in fallback_vendors:
        if vendor not in VENDOR_METHODS[method]:
            if vendor in primary_vendors:
                print(f"[vendor] '{method}' not supported by '{vendor}', trying next")
            continue

        vendor_impl = VENDOR_METHODS[method][vendor]
        is_primary_vendor = vendor in primary_vendors
        vendor_attempt_count += 1

        if is_primary_vendor:
            any_primary_vendor_attempted = True

        vendor_type = "primary" if is_primary_vendor else "fallback"
        print(f"[vendor] trying {vendor_type} '{vendor}' for {method} (attempt {vendor_attempt_count})")

        if isinstance(vendor_impl, list):
            vendor_methods = [(impl, vendor) for impl in vendor_impl]
            print(f"[vendor] '{vendor}' has {len(vendor_methods)} implementations")
        else:
            vendor_methods = [(vendor_impl, vendor)]

        vendor_results = []
        for impl_func, vendor_name in vendor_methods:
            try:
                print(f"[vendor] calling {impl_func.__name__} from '{vendor_name}'...")
                result = impl_func(*args, **kwargs)
                vendor_results.append(result)
                print(f"[vendor] {impl_func.__name__} succeeded from '{vendor_name}'")

            except AlphaVantageRateLimitError as e:
                if vendor == "alpha_vantage":
                    print(f"[vendor] Alpha Vantage rate limit hit, falling back: {e}")
                continue
            except FinMindRateLimitError as e:
                if vendor == "finmind":
                    print(f"[vendor] FinMind rate limit hit, falling back: {e}")
                continue
            except Exception as e:
                error_type = type(e).__name__
                print(f"[vendor] {impl_func.__name__} from '{vendor_name}' failed ({error_type}): {e}")
                continue

        if vendor_results:
            results.extend(vendor_results)
            successful_vendor = vendor
            print(f"[vendor] '{vendor}' succeeded with {len(vendor_results)} result(s)")
            if len(primary_vendors) == 1:
                print(f"[vendor] stopping after successful '{vendor}' (single-vendor config)")
                break
        else:
            print(f"[vendor] '{vendor}' produced no results")

    if not results:
        print(f"[vendor] all {vendor_attempt_count} attempt(s) failed for '{method}'")
        raise RuntimeError(f"All vendor implementations failed for method '{method}'")
    else:
        print(f"[vendor] '{method}' completed with {len(results)} result(s) after {vendor_attempt_count} attempt(s)")

    # 如果只有一個結果，則返回單個結果，否則連接為字串
    if len(results) == 1:
        return results[0]
    else:
        # 將所有結果轉換為字串並連接
        return '\n'.join(str(result) for result in results)
