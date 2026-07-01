/**
 * Client-side stock symbol search / autocomplete.
 *
 * Data is loaded lazily from static JSON assets in /public/data:
 *  - stocks-us.json:  [ [ticker, name], ... ]
 *  - stocks-tw.json:  [ [id, zhName, enName, market], ... ]  (market: "twse" | "tpex")
 *
 * Both files are fetched at most once and cached in-module.
 */

export type MarketType = "us" | "twse" | "tpex";

export interface StockItem {
  symbol: string;
  zh: string; // Chinese display name (for US == en)
  en: string; // English display name (may be "" for long-tail TW stocks)
  market: MarketType;
  pop: number; // popularity rank (lower = more prominent); from source file order
}

type UsRow = [string, string];
type TwRow = [string, string, string, string];

// Promise caches so concurrent callers share a single fetch.
let usPromise: Promise<StockItem[]> | null = null;
let twPromise: Promise<StockItem[]> | null = null;

async function loadUs(): Promise<StockItem[]> {
  if (!usPromise) {
    usPromise = fetch("/data/stocks-us.json")
      .then((r) => r.json() as Promise<UsRow[]>)
      .then((rows) =>
        rows.map(([symbol, name], i) => ({
          symbol,
          zh: name,
          en: name,
          market: "us" as MarketType,
          pop: i,
        }))
      )
      .catch((err) => {
        usPromise = null; // allow retry on next call
        throw err;
      });
  }
  return usPromise;
}

async function loadTw(): Promise<StockItem[]> {
  if (!twPromise) {
    twPromise = fetch("/data/stocks-tw.json")
      .then((r) => r.json() as Promise<TwRow[]>)
      .then((rows) =>
        rows.map(([symbol, zh, en, market], i) => ({
          symbol,
          zh,
          en,
          market: (market === "twse" ? "twse" : "tpex") as MarketType,
          pop: i,
        }))
      )
      .catch((err) => {
        twPromise = null;
        throw err;
      });
  }
  return twPromise;
}

/** Load (and cache) the list relevant to a market type. */
export async function loadStocks(market: MarketType): Promise<StockItem[]> {
  if (market === "us") return loadUs();
  const all = await loadTw();
  return all.filter((s) => s.market === market);
}

/** Display name for an item given the current locale, with graceful fallback. */
export function displayName(item: StockItem, locale: string): string {
  if (locale.startsWith("zh")) return item.zh || item.en || item.symbol;
  return item.en || item.zh || item.symbol;
}

export interface StockMatch extends StockItem {
  name: string; // pre-resolved display name for the given locale
}

/**
 * Rank stocks against a query.
 * Priority: exact symbol > symbol prefix > name prefix > name substring.
 */
export function rankStocks(
  items: StockItem[],
  query: string,
  locale: string,
  limit = 8
): StockMatch[] {
  const q = query.trim();
  if (!q) return [];
  const qUpper = q.toUpperCase();

  const scored: { item: StockItem; score: number }[] = [];
  for (const item of items) {
    const sym = item.symbol.toUpperCase();
    const name = displayName(item, locale);
    const nameUpper = name.toUpperCase();
    // Match against both localized name and the alternate-language name so a
    // Chinese query still hits in English UI and vice-versa.
    const altUpper = (locale.startsWith("zh") ? item.en : item.zh).toUpperCase();

    let score = -1;
    if (sym === qUpper) score = 0;
    else if (sym.startsWith(qUpper)) score = 1;
    else if (nameUpper.startsWith(qUpper) || altUpper.startsWith(qUpper)) score = 2;
    else if (sym.includes(qUpper)) score = 3;
    else if (nameUpper.includes(qUpper) || altUpper.includes(qUpper)) score = 4;

    if (score >= 0) scored.push({ item, score });
  }

  scored.sort((a, b) => {
    if (a.score !== b.score) return a.score - b.score;
    // Within the same relevance bucket, more prominent companies first.
    if (a.item.pop !== b.item.pop) return a.item.pop - b.item.pop;
    return a.item.symbol.localeCompare(b.item.symbol);
  });

  return scored.slice(0, limit).map(({ item }) => ({
    ...item,
    name: displayName(item, locale),
  }));
}

/** Convenience: load the market list then rank. */
export async function searchStocks(
  query: string,
  market: MarketType,
  locale: string,
  limit = 8
): Promise<StockMatch[]> {
  const items = await loadStocks(market);
  return rankStocks(items, query, locale, limit);
}

/** Resolve a single symbol's display name (used by the results page). */
export async function lookupStockName(
  symbol: string,
  market: MarketType,
  locale: string
): Promise<string | null> {
  if (!symbol) return null;
  const items = await loadStocks(market);
  const target = symbol.trim().toUpperCase();
  const found = items.find((s) => s.symbol.toUpperCase() === target);
  return found ? displayName(found, locale) : null;
}
