/**
 * Watchlist page — manage tracked tickers, sync with Google Sheet,
 * trigger AI analysis, and generate new candidates via screener + LLM.
 * Clicking a candidate card opens a detail modal with a full AI report.
 */
"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { format } from "date-fns";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useLanguage } from "@/contexts/LanguageContext";
import { api } from "@/lib/api";
import type { WatchlistItem, WatchlistStatus, WatchlistCandidate, CandidateDetail, ScreenerParams } from "@/lib/types";
import { DEFAULT_SCREENER_PARAMS } from "@/lib/types";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  RefreshCw,
  Plus,
  Trash2,
  BarChart2,
  ExternalLink,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  TrendingUp,
  TrendingDown,
  Minus,
  X,
  SlidersHorizontal,
  ChevronDown,
  ChevronUp,
  RotateCcw,
} from "lucide-react";

const MARKET_OPTIONS = [
  { value: "us", label: "US" },
  { value: "twse", label: "TWSE" },
  { value: "tpex", label: "TPEx" },
];

const REC_COLOR: Record<string, string> = {
  BUY: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300",
  SELL: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
  HOLD: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300",
};

const SIGNAL_STYLE: Record<string, string> = {
  BULLISH: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
  BEARISH: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
  NEUTRAL: "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300",
};

const SignalIcon = ({ signal }: { signal?: string }) => {
  if (signal === "BULLISH") return <TrendingUp className="w-3 h-3" />;
  if (signal === "BEARISH") return <TrendingDown className="w-3 h-3" />;
  return <Minus className="w-3 h-3" />;
};

// ── Screener Settings Panel ────────────────────────────────────────────────────

function ScreenerSettingsPanel({
  params,
  onChange,
  onReset,
  t,
}: {
  params: ScreenerParams;
  onChange: (p: Partial<ScreenerParams>) => void;
  onReset: () => void;
  t: any;
}) {
  const s = t.watchlist.candidates.settings;

  const NumberSlider = ({
    label, hint, value, min, max, step, unit, field,
  }: {
    label: string; hint: string; value: number; min: number; max: number;
    step: number; unit: string; field: keyof ScreenerParams;
  }) => (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <Label className="text-xs font-medium text-slate-700 dark:text-slate-300">{label}</Label>
        <span className="text-xs font-mono font-semibold text-blue-600 dark:text-blue-400 w-16 text-right">
          {typeof value === "number" ? value.toFixed(step < 1 ? 1 : 0) : value}{unit}
        </span>
      </div>
      <input
        type="range"
        min={min} max={max} step={step}
        value={value}
        onChange={(e) => onChange({ [field]: parseFloat(e.target.value) })}
        className="w-full h-1.5 rounded-full appearance-none bg-slate-200 dark:bg-slate-700
          [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3.5
          [&::-webkit-slider-thumb]:h-3.5 [&::-webkit-slider-thumb]:rounded-full
          [&::-webkit-slider-thumb]:bg-blue-500 [&::-webkit-slider-thumb]:cursor-pointer
          accent-blue-500"
      />
      <div className="flex justify-between text-[10px] text-slate-400">
        <span>{min}{unit}</span>
        <span className="text-slate-400 italic">{hint}</span>
        <span>{max}{unit}</span>
      </div>
    </div>
  );

  return (
    <div className="border border-slate-200 dark:border-slate-700 rounded-xl p-4 bg-slate-50 dark:bg-slate-800/50 space-y-5">
      {/* Stage 1 */}
      <div>
        <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3">
          {s.stage1}
        </p>
        <div className="space-y-4">
          <NumberSlider label={s.minPriceChange} hint={s.minPriceChangeHint}
            value={params.min_price_change_pct} min={0.5} max={10} step={0.5} unit="%" field="min_price_change_pct" />
          <NumberSlider label={s.minVolumeRatio} hint={s.minVolumeRatioHint}
            value={params.min_volume_ratio} min={1.0} max={5.0} step={0.1} unit="×" field="min_volume_ratio" />

          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <Label className="text-xs font-medium text-slate-700 dark:text-slate-300">{s.priceWeight}</Label>
              <div className="text-xs font-mono font-semibold text-right">
                <span className="text-blue-600 dark:text-blue-400">
                  price {(params.price_change_weight * 100).toFixed(0)}%
                </span>
                <span className="text-slate-400 mx-1">/</span>
                <span className="text-emerald-600 dark:text-emerald-400">
                  vol {((1 - params.price_change_weight) * 100).toFixed(0)}%
                </span>
              </div>
            </div>
            <input
              type="range" min={0.1} max={0.9} step={0.1}
              value={params.price_change_weight}
              onChange={(e) => onChange({ price_change_weight: parseFloat(e.target.value) })}
              className="w-full h-1.5 rounded-full appearance-none bg-slate-200 dark:bg-slate-700
                [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3.5
                [&::-webkit-slider-thumb]:h-3.5 [&::-webkit-slider-thumb]:rounded-full
                [&::-webkit-slider-thumb]:bg-blue-500 [&::-webkit-slider-thumb]:cursor-pointer
                accent-blue-500"
            />
            <p className="text-[10px] text-slate-400 italic">{s.priceWeightHint}</p>
          </div>

          {/* Universe toggles */}
          <div>
            <Label className="text-xs font-medium text-slate-700 dark:text-slate-300 block mb-2">{s.universe}</Label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <Switch checked={params.include_us} onCheckedChange={(v) => onChange({ include_us: v })} />
                <span className="text-xs text-slate-600 dark:text-slate-300">{s.includeUS}</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <Switch checked={params.include_tw} onCheckedChange={(v) => onChange({ include_tw: v })} />
                <span className="text-xs text-slate-600 dark:text-slate-300">{s.includeTW}</span>
              </label>
            </div>
          </div>

          <NumberSlider label={s.maxCandidates} hint={s.maxCandidatesHint}
            value={params.max_screener_candidates} min={5} max={50} step={5} unit="" field="max_screener_candidates" />
        </div>
      </div>

      {/* Stage 2 */}
      <div className="border-t border-slate-200 dark:border-slate-700 pt-4">
        <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3">
          {s.stage2}
        </p>
        <NumberSlider label={s.llmTopN} hint={s.llmTopNHint}
          value={params.llm_top_n} min={3} max={15} step={1} unit="" field="llm_top_n" />
      </div>

      {/* Reset */}
      <div className="flex justify-end">
        <Button variant="ghost" size="sm" onClick={onReset} className="text-xs gap-1.5 text-slate-400 hover:text-slate-600">
          <RotateCcw className="w-3 h-3" />{s.reset}
        </Button>
      </div>
    </div>
  );
}


// ── Candidate Detail Modal ─────────────────────────────────────────────────────

interface DetailModalState {
  open: boolean;
  ticker: string | null;
  candidate: WatchlistCandidate | null;
  detail: CandidateDetail | null;
  loading: boolean;
  error: string | null;
}

const DETAIL_CLOSED: DetailModalState = {
  open: false, ticker: null, candidate: null, detail: null, loading: false, error: null,
};

function CandidateDetailModal({
  state,
  onClose,
  onAdd,
  onDismiss,
  onOpenAnalysis,
  watchlistTickers,
  t,
}: {
  state: DetailModalState;
  onClose: () => void;
  onAdd: (ticker: string) => void;
  onDismiss: (ticker: string) => void;
  onOpenAnalysis: (ticker: string, market: string) => void;
  watchlistTickers: Set<string>;
  t: any;
}) {
  const ct = t.watchlist.candidates;
  const dt = ct.detail;
  const { candidate, detail, loading, error } = state;
  const ticker = state.ticker ?? "";
  const signal = detail?.signal ?? candidate?.signal ?? "NEUTRAL";
  const alreadyAdded = watchlistTickers.has(ticker);

  const priceChange = detail?.price_change_pct ?? candidate?.price_change_pct;
  const volRatio = detail?.volume_ratio ?? candidate?.volume_ratio;
  const rsi = detail?.rsi ?? candidate?.rsi;
  const changePos = (priceChange ?? 0) >= 0;

  return (
    <Dialog open={state.open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-2xl max-h-[85vh] flex flex-col p-0 gap-0">
        {/* Fixed header */}
        <DialogHeader className="px-6 pt-6 pb-4 border-b border-slate-100 dark:border-slate-800 shrink-0">
          <DialogTitle className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-xl text-blue-700 dark:text-blue-300">{ticker}</span>
            <span className="text-xs uppercase font-medium text-slate-400 dark:text-slate-500">
              {candidate?.market_type ?? detail?.market_type}
            </span>
            {signal && (
              <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full ${SIGNAL_STYLE[signal] ?? SIGNAL_STYLE.NEUTRAL}`}>
                <SignalIcon signal={signal} />
                {ct.signal[signal as keyof typeof ct.signal] ?? signal}
              </span>
            )}
          </DialogTitle>

          {/* Metrics bar */}
          <div className="flex flex-wrap gap-4 mt-2 text-sm">
            {priceChange != null && (
              <div>
                <span className="text-xs text-slate-400">{ct.priceChange} </span>
                <span className={`font-mono font-semibold ${changePos ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400"}`}>
                  {changePos ? "+" : ""}{priceChange.toFixed(2)}%
                </span>
              </div>
            )}
            {volRatio != null && (
              <div>
                <span className="text-xs text-slate-400">{ct.volRatio} </span>
                <span className="font-mono font-semibold text-slate-700 dark:text-slate-200">×{volRatio.toFixed(1)}</span>
              </div>
            )}
            {rsi != null && (
              <div>
                <span className="text-xs text-slate-400">{ct.rsi} </span>
                <span className={`font-mono font-semibold ${rsi < 30 ? "text-emerald-600 dark:text-emerald-400" : rsi > 70 ? "text-red-600 dark:text-red-400" : "text-slate-700 dark:text-slate-200"}`}>
                  {rsi.toFixed(0)}
                </span>
              </div>
            )}
            {detail?.current_price != null && (
              <div>
                <span className="text-xs text-slate-400">{dt.currentPrice} </span>
                <span className="font-mono font-semibold text-slate-700 dark:text-slate-200">{detail.current_price}</span>
              </div>
            )}
            {detail?.price_low_30d != null && detail?.price_high_30d != null && (
              <div>
                <span className="text-xs text-slate-400">{dt.range30d} </span>
                <span className="font-mono font-semibold text-slate-700 dark:text-slate-200">
                  {detail.price_low_30d} – {detail.price_high_30d}
                </span>
              </div>
            )}
          </div>
        </DialogHeader>

        {/* Scrollable report body */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {loading && (
            <div className="flex flex-col items-center justify-center py-16 gap-3 text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin text-amber-400" />
              <p className="text-sm font-medium">{dt.generating}</p>
              <p className="text-xs">{dt.generatingHint}</p>
            </div>
          )}

          {!loading && error && (
            <div className="py-10 text-center text-slate-400 text-sm">{error}</div>
          )}

          {!loading && !error && detail?.report_md && (
            <div className="prose prose-sm dark:prose-invert max-w-none
              prose-headings:text-slate-800 dark:prose-headings:text-slate-100
              prose-h2:text-base prose-h2:font-semibold prose-h2:mt-5 prose-h2:mb-2
              prose-p:text-slate-600 dark:prose-p:text-slate-300
              prose-table:text-xs prose-td:py-1 prose-th:py-1
              prose-table:border-collapse prose-td:border prose-td:border-slate-200
              dark:prose-td:border-slate-700 prose-th:border prose-th:border-slate-200
              dark:prose-th:border-slate-700 prose-th:bg-slate-50 dark:prose-th:bg-slate-800
              prose-strong:text-slate-800 dark:prose-strong:text-slate-100">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {detail.report_md}
              </ReactMarkdown>
            </div>
          )}

          {!loading && !error && detail && !detail.report_md && (
            <p className="py-10 text-center text-slate-400 text-sm">{dt.noReport}</p>
          )}
        </div>

        {/* Fixed footer */}
        <DialogFooter className="px-6 py-4 border-t border-slate-100 dark:border-slate-800 shrink-0">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => { onDismiss(ticker); onClose(); }}
            className="text-slate-400 hover:text-red-500 mr-auto"
          >
            <X className="w-3.5 h-3.5 mr-1" />
            {dt.dismiss}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onOpenAnalysis(ticker, candidate?.market_type ?? detail?.market_type ?? "us")}
          >
            <ExternalLink className="w-3.5 h-3.5 mr-1" />
            {dt.openFullAnalysis}
          </Button>
          {!alreadyAdded && (
            <Button
              size="sm"
              onClick={() => { onAdd(ticker); onClose(); }}
              className="gap-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              {dt.addToWatchlist}
            </Button>
          )}
          {alreadyAdded && (
            <span className="text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> {ct.alreadyInWatchlist}
            </span>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function WatchlistPage() {
  const { t } = useLanguage();
  const router = useRouter();
  const wt = t.watchlist;
  const ct = wt.candidates;

  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [status, setStatus] = useState<WatchlistStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [analyzingAll, setAnalyzingAll] = useState(false);
  const [analyzingTicker, setAnalyzingTicker] = useState<string | null>(null);
  const [toast, setToast] = useState<{ msg: string; ok: boolean } | null>(null);

  // Add form state
  const [newTicker, setNewTicker] = useState("");
  const [newMarket, setNewMarket] = useState("us");
  const [newNotes, setNewNotes] = useState("");
  const [adding, setAdding] = useState(false);

  // Market filter: "us" | "tw"
  const [marketFilter, setMarketFilter] = useState<"us" | "tw">("us");

  // Candidates state
  const [candidates, setCandidates] = useState<WatchlistCandidate[]>([]);
  const [generating, setGenerating] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [screenerParams, setScreenerParams] = useState<ScreenerParams>(DEFAULT_SCREENER_PARAMS);
  const [showSettings, setShowSettings] = useState(false);

  // Detail modal state
  const [detailModal, setDetailModal] = useState<DetailModalState>(DETAIL_CLOSED);

  const showToast = (msg: string, ok = true) => {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 3500);
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [itemsData, statusData, candidatesData] = await Promise.all([
        api.getWatchlist(),
        api.getWatchlistStatus().catch(() => null),
        api.getCandidates().catch(() => []),
      ]);
      setItems(itemsData);
      setStatus(statusData);
      setCandidates(candidatesData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTicker.trim()) return;
    setAdding(true);
    try {
      const item = await api.addToWatchlist(newTicker.trim().toUpperCase(), newMarket, newNotes);
      setItems((prev) => [...prev, item]);
      setNewTicker(""); setNewNotes("");
      showToast(`${item.ticker} added`);
    } catch (err: any) {
      showToast(err?.response?.data?.detail ?? "Failed to add ticker", false);
    } finally {
      setAdding(false);
    }
  };

  const handleRemove = async (ticker: string) => {
    if (!confirm(wt.removeConfirm.replace("{ticker}", ticker))) return;
    try {
      await api.removeFromWatchlist(ticker);
      setItems((prev) => prev.filter((i) => i.ticker !== ticker));
      showToast(`${ticker} removed`);
    } catch { showToast("Failed to remove", false); }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      const res = await api.syncWatchlistFromSheet();
      showToast(res.message || wt.syncDone);
      await load();
    } catch { showToast(wt.syncError, false); }
    finally { setSyncing(false); }
  };

  const handleAnalyzeAll = async () => {
    setAnalyzingAll(true);
    try {
      const res = await api.triggerWatchlistAnalysis();
      showToast(res.message || wt.analyzing);
    } catch { showToast("Failed to start analysis", false); }
    finally { setAnalyzingAll(false); }
  };

  const handleAnalyzeSingle = async (ticker: string) => {
    setAnalyzingTicker(ticker);
    try {
      const res = await api.triggerWatchlistAnalysis(ticker);
      showToast(res.message || wt.analyzing);
    } catch { showToast("Failed to start analysis", false); }
    finally { setAnalyzingTicker(null); }
  };

  const goToAnalysis = (ticker: string, market_type: string) =>
    router.push(`/analysis?ticker=${ticker}&market_type=${market_type}`);

  const fmtDate = (iso?: string) => {
    if (!iso) return wt.never;
    try { return format(new Date(iso), "MM-dd HH:mm"); }
    catch { return iso.slice(0, 16); }
  };

  // ── Candidate handlers ───────────────────────────────────────────────────────

  const handleGenerate = async () => {
    setGenerating(true);
    setSelected(new Set());
    setShowSettings(false);
    try {
      const result = await api.generateCandidates(screenerParams);
      setCandidates(result);
      if (result.length === 0) showToast("No candidates found — try relaxing the filters", false);
    } catch (err: any) {
      showToast(err?.response?.data?.detail ?? "Generation failed", false);
    } finally { setGenerating(false); }
  };

  const toggleSelect = (ticker: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(ticker) ? next.delete(ticker) : next.add(ticker);
      return next;
    });
  };

  const toggleSelectAll = () => {
    const visibleTickers = filteredCandidates.map((c) => c.ticker);
    const allVisible = visibleTickers.every((t) => selected.has(t));
    setSelected((prev) => {
      const next = new Set(prev);
      if (allVisible) visibleTickers.forEach((t) => next.delete(t));
      else visibleTickers.forEach((t) => next.add(t));
      return next;
    });
  };

  const handleAddSelected = async () => {
    if (selected.size === 0) return;
    try {
      const { added } = await api.addCandidatesToWatchlist(Array.from(selected));
      setCandidates((prev) => prev.filter((c) => !selected.has(c.ticker)));
      setSelected(new Set());
      showToast(ct.addedToast.replace("{n}", String(added.length)));
      if (added.length > 0) await load();
    } catch { showToast("Failed to add selected", false); }
  };

  const handleDismiss = async (ticker: string) => {
    try {
      await api.dismissCandidate(ticker);
      setCandidates((prev) => prev.filter((c) => c.ticker !== ticker));
      setSelected((prev) => { const n = new Set(prev); n.delete(ticker); return n; });
    } catch { showToast("Failed to dismiss", false); }
  };

  // Single-add from modal
  const handleAddOne = async (ticker: string) => {
    try {
      const candidate = candidates.find((c) => c.ticker === ticker);
      const { added } = await api.addCandidatesToWatchlist([ticker]);
      if (added.length > 0) {
        setCandidates((prev) => prev.filter((c) => c.ticker !== ticker));
        setSelected((prev) => { const n = new Set(prev); n.delete(ticker); return n; });
        showToast(ct.addedToast.replace("{n}", "1"));
        await load();
      }
    } catch { showToast("Failed to add", false); }
  };

  // Open detail modal — fetch report while modal is shown
  const handleCardClick = async (candidate: WatchlistCandidate) => {
    setDetailModal({ open: true, ticker: candidate.ticker, candidate, detail: null, loading: true, error: null });
    try {
      const detail = await api.getCandidateDetail(candidate.ticker);
      setDetailModal((prev) => ({ ...prev, detail, loading: false }));
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? ct.detail.noReport;
      setDetailModal((prev) => ({ ...prev, loading: false, error: msg }));
    }
  };

  const isTW = (mkt: string) => mkt === "twse" || mkt === "tpex";
  const matchesFilter = (mkt: string) => marketFilter === "us" ? mkt === "us" : isTW(mkt);

  const filteredItems = items.filter((i) => matchesFilter(i.market_type));
  const filteredCandidates = candidates.filter((c) => matchesFilter(c.market_type));

  const usCount = items.filter((i) => i.market_type === "us").length;
  const twCount = items.filter((i) => isTW(i.market_type)).length;
  const usCandCount = candidates.filter((c) => c.market_type === "us").length;
  const twCandCount = candidates.filter((c) => isTW(c.market_type)).length;

  const handleMarketSwitch = (mkt: "us" | "tw") => {
    setMarketFilter(mkt);
    setNewMarket(mkt === "us" ? "us" : "twse");
    setSelected(new Set());
  };

  const watchlistTickers = new Set(items.map((i) => i.ticker));
  const nextJob = status?.jobs?.find((j) => j.id === "daily_analysis");
  const syncJob = status?.jobs?.find((j) => j.id === "sheet_sync");

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-20 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg text-sm font-medium transition-all
            ${toast.ok
              ? "bg-emerald-50 text-emerald-800 border border-emerald-200 dark:bg-emerald-900/40 dark:text-emerald-200 dark:border-emerald-700"
              : "bg-red-50 text-red-800 border border-red-200 dark:bg-red-900/40 dark:text-red-200 dark:border-red-700"}`}>
          {toast.ok ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
          {toast.msg}
        </div>
      )}

      {/* Detail modal */}
      <CandidateDetailModal
        state={detailModal}
        onClose={() => setDetailModal(DETAIL_CLOSED)}
        onAdd={handleAddOne}
        onDismiss={handleDismiss}
        onOpenAnalysis={goToAnalysis}
        watchlistTickers={watchlistTickers}
        t={t}
      />

      {/* Header + market toggle */}
      <div className="mb-6 flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{wt.title}</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{wt.subtitle}</p>
        </div>

        {/* US / TWN tab toggle */}
        <div className="flex items-center rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden shrink-0 shadow-sm">
          {(["us", "tw"] as const).map((mkt) => {
            const active = marketFilter === mkt;
            const label = wt.marketSwitch[mkt];
            const wlCount = mkt === "us" ? usCount : twCount;
            const cdCount = mkt === "us" ? usCandCount : twCandCount;
            return (
              <button
                key={mkt}
                onClick={() => handleMarketSwitch(mkt)}
                className={`px-4 py-2 text-sm font-semibold flex items-center gap-2 transition-colors
                  ${active
                    ? "bg-blue-600 text-white"
                    : "bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700"
                  }`}
              >
                {label}
                <span className={`text-xs px-1.5 py-0.5 rounded-full font-mono
                  ${active
                    ? "bg-blue-500 text-blue-100"
                    : "bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400"
                  }`}>
                  {wlCount}
                  {cdCount > 0 && <span className="text-amber-400 ml-0.5">+{cdCount}</span>}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Status bar */}
      {status && (
        <div className="flex flex-wrap gap-3 mb-6 text-xs">
          <span className="flex items-center gap-1 text-slate-500 dark:text-slate-400">
            {status.sheets_configured ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> : <XCircle className="w-3.5 h-3.5 text-slate-400" />}
            {wt.statusSheets}{status.sheets_configured ? wt.connected : wt.notConfigured}
          </span>
          <span className="flex items-center gap-1 text-slate-500 dark:text-slate-400">
            {status.telegram_configured ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> : <XCircle className="w-3.5 h-3.5 text-slate-400" />}
            {wt.statusTelegram}{status.telegram_configured ? wt.connected : wt.notConfigured}
          </span>
          {nextJob?.next_run && (
            <span className="flex items-center gap-1 text-slate-500 dark:text-slate-400">
              <Clock className="w-3.5 h-3.5" />Next analysis: {fmtDate(nextJob.next_run)}
            </span>
          )}
          {syncJob?.next_run && (
            <span className="flex items-center gap-1 text-slate-500 dark:text-slate-400">
              <Clock className="w-3.5 h-3.5" />Next sync: {fmtDate(syncJob.next_run)}
            </span>
          )}
        </div>
      )}

      {/* Add ticker + action buttons */}
      <Card className="mb-6">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">{wt.addTicker}</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleAdd} className="flex flex-wrap gap-2 items-end">
            <div className="flex-1 min-w-[120px]">
              <Input placeholder={wt.tickerPlaceholder} value={newTicker}
                onChange={(e) => setNewTicker(e.target.value.toUpperCase())} className="font-mono" />
            </div>
            <Select value={newMarket} onValueChange={setNewMarket}>
              <SelectTrigger className="w-28"><SelectValue /></SelectTrigger>
              <SelectContent>
                {MARKET_OPTIONS.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
              </SelectContent>
            </Select>
            <div className="flex-1 min-w-[160px]">
              <Input placeholder={wt.notesPlaceholder} value={newNotes} onChange={(e) => setNewNotes(e.target.value)} />
            </div>
            <Button type="submit" disabled={adding || !newTicker.trim()} className="gap-1.5">
              <Plus className="w-4 h-4" />{wt.addTicker}
            </Button>
          </form>
          <div className="flex gap-2 mt-4 flex-wrap">
            <Button variant="outline" size="sm" onClick={handleSync} disabled={syncing || !status?.sheets_configured} className="gap-1.5">
              <RefreshCw className={`w-3.5 h-3.5 ${syncing ? "animate-spin" : ""}`} />
              {syncing ? wt.syncing : wt.syncFromSheet}
            </Button>
            <Button variant="outline" size="sm" onClick={handleAnalyzeAll} disabled={analyzingAll || items.length === 0} className="gap-1.5">
              <BarChart2 className="w-3.5 h-3.5" />{analyzingAll ? "Starting..." : wt.analyzeAll}
            </Button>
            <Button variant="ghost" size="sm" onClick={load} className="gap-1.5 ml-auto">
              <RefreshCw className="w-3.5 h-3.5" />{t.history?.refresh ?? "Refresh"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Watchlist table */}
      <Card className="mb-6">
        <CardContent className="p-0">
          {loading ? (
            <div className="py-16 text-center text-slate-400 text-sm">{t.common.loading}</div>
          ) : filteredItems.length === 0 ? (
            <div className="py-16 text-center text-slate-400 text-sm">{wt.empty}</div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-b border-slate-100 dark:border-slate-800">
                    <TableHead className="font-semibold">{wt.columns.ticker}</TableHead>
                    <TableHead className="font-semibold">{wt.columns.market}</TableHead>
                    <TableHead className="font-semibold hidden md:table-cell">{wt.columns.notes}</TableHead>
                    <TableHead className="font-semibold hidden lg:table-cell">{wt.columns.addedAt}</TableHead>
                    <TableHead className="font-semibold">{wt.columns.lastAnalyzed}</TableHead>
                    <TableHead className="font-semibold">{wt.columns.recommendation}</TableHead>
                    <TableHead className="font-semibold hidden sm:table-cell">{wt.columns.score}</TableHead>
                    <TableHead className="font-semibold text-right">{wt.columns.actions}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredItems.map((item) => {
                    const rec = (item.last_recommendation ?? "").toUpperCase();
                    return (
                      <TableRow key={item.id} className="border-b border-slate-50 dark:border-slate-800/50 hover:bg-slate-50 dark:hover:bg-slate-800/30">
                        <TableCell className="font-mono font-semibold text-blue-700 dark:text-blue-300">{item.ticker}</TableCell>
                        <TableCell>
                          <span className="text-xs uppercase font-medium text-slate-500 dark:text-slate-400">{item.market_type}</span>
                        </TableCell>
                        <TableCell className="hidden md:table-cell text-slate-500 dark:text-slate-400 text-xs max-w-[160px] truncate">
                          {item.notes || "—"}
                        </TableCell>
                        <TableCell className="hidden lg:table-cell text-xs text-slate-400">{fmtDate(item.added_at)}</TableCell>
                        <TableCell className="text-xs text-slate-400">
                          {item.last_analyzed_at ? fmtDate(item.last_analyzed_at) : wt.never}
                        </TableCell>
                        <TableCell>
                          {rec ? (
                            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${REC_COLOR[rec] ?? "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300"}`}>{rec}</span>
                          ) : <span className="text-slate-300 dark:text-slate-600">—</span>}
                        </TableCell>
                        <TableCell className="hidden sm:table-cell text-xs font-mono text-slate-500 dark:text-slate-400">
                          {item.last_score != null ? item.last_score.toFixed(1) : "—"}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-1">
                            <Button variant="ghost" size="icon" className="h-7 w-7 text-slate-400 hover:text-blue-600"
                              title={wt.goToAnalysis} onClick={() => goToAnalysis(item.ticker, item.market_type)}>
                              <ExternalLink className="w-3.5 h-3.5" />
                            </Button>
                            <Button variant="ghost" size="icon" className="h-7 w-7 text-slate-400 hover:text-emerald-600"
                              title={wt.analyze} onClick={() => handleAnalyzeSingle(item.ticker)} disabled={analyzingTicker === item.ticker}>
                              <BarChart2 className={`w-3.5 h-3.5 ${analyzingTicker === item.ticker ? "animate-pulse" : ""}`} />
                            </Button>
                            <Button variant="ghost" size="icon" className="h-7 w-7 text-slate-400 hover:text-red-500"
                              title={wt.remove} onClick={() => handleRemove(item.ticker)}>
                              <Trash2 className="w-3.5 h-3.5" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ── AI Candidates Panel ─────────────────────────────────────────────── */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-amber-500" />
                {ct.title}
              </CardTitle>
              <CardDescription className="text-xs mt-0.5">{ct.subtitle}</CardDescription>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSettings((v) => !v)}
                className="gap-1.5"
              >
                <SlidersHorizontal className="w-3.5 h-3.5" />
                {ct.settings.title}
                {showSettings ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </Button>
              <Button onClick={handleGenerate} disabled={generating} size="sm" className="gap-1.5">
                {generating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                {generating ? ct.generating : ct.generate}
              </Button>
            </div>
          </div>

          {/* Collapsible settings panel */}
          {showSettings && (
            <div className="mt-4">
              <ScreenerSettingsPanel
                params={screenerParams}
                onChange={(partial) => setScreenerParams((prev) => ({ ...prev, ...partial }))}
                onReset={() => setScreenerParams(DEFAULT_SCREENER_PARAMS)}
                t={t}
              />
            </div>
          )}
        </CardHeader>

        <CardContent>
          {generating && (
            <div className="py-10 text-center text-slate-400 text-sm space-y-2">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto text-amber-400" />
              <p>{ct.generating}</p>
            </div>
          )}

          {!generating && filteredCandidates.length === 0 && (
            <div className="py-10 text-center text-slate-400 text-sm">
              {candidates.length > 0
                ? `No ${marketFilter === "us" ? "US" : "Taiwan"} candidates — switch market or regenerate.`
                : ct.empty}
            </div>
          )}

          {!generating && filteredCandidates.length > 0 && (
            <>
              {/* Select-all + bulk add toolbar */}
              <div className="flex items-center justify-between mb-3">
                <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300 cursor-pointer select-none">
                  <Checkbox
                    checked={selected.size === filteredCandidates.length && filteredCandidates.length > 0}
                    onCheckedChange={toggleSelectAll}
                  />
                  {selected.size > 0
                    ? `${selected.size} / ${filteredCandidates.length} selected`
                    : `${filteredCandidates.length} candidates — click a card for details`}
                </label>
                <Button size="sm" disabled={selected.size === 0} onClick={handleAddSelected} className="gap-1.5">
                  <Plus className="w-3.5 h-3.5" />
                  {selected.size > 0
                    ? ct.addSelectedCount.replace("{n}", String(selected.size))
                    : ct.addSelected}
                </Button>
              </div>

              {/* Candidate cards — click opens detail modal */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                {filteredCandidates.map((c) => {
                  const alreadyAdded = watchlistTickers.has(c.ticker);
                  const isSelected = selected.has(c.ticker);
                  const signal = c.signal ?? "NEUTRAL";
                  const changePos = (c.price_change_pct ?? 0) >= 0;

                  return (
                    <div
                      key={c.id}
                      className={`relative rounded-xl border p-3 transition-all cursor-pointer
                        ${isSelected
                          ? "border-blue-400 bg-blue-50 dark:border-blue-600 dark:bg-blue-950/30"
                          : "border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800/50 hover:border-blue-300 hover:shadow-sm dark:hover:border-blue-700"
                        }
                        ${alreadyAdded ? "opacity-50" : ""}`}
                      onClick={() => handleCardClick(c)}
                      title="Click to view detailed AI analysis"
                    >
                      {/* Dismiss button */}
                      <button
                        className="absolute top-2 right-2 text-slate-300 hover:text-slate-500 dark:text-slate-600 dark:hover:text-slate-400 z-10"
                        onClick={(e) => { e.stopPropagation(); handleDismiss(c.ticker); }}
                        title={ct.dismiss}
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>

                      {/* Header row */}
                      <div className="flex items-start gap-2 mb-2 pr-5">
                        <Checkbox
                          checked={isSelected}
                          onCheckedChange={() => toggleSelect(c.ticker)}
                          onClick={(e) => e.stopPropagation()}
                          className="mt-0.5 shrink-0"
                          disabled={alreadyAdded}
                        />
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            {c.rank && (
                              <span className="text-xs font-bold text-slate-400 dark:text-slate-500 w-4">#{c.rank}</span>
                            )}
                            <span className="font-mono font-bold text-blue-700 dark:text-blue-300 text-sm">{c.ticker}</span>
                            <span className="text-xs text-slate-400 uppercase">{c.market_type}</span>
                          </div>
                          {alreadyAdded && (
                            <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">✓ {ct.alreadyInWatchlist}</span>
                          )}
                        </div>
                      </div>

                      {/* Signal badge */}
                      <div className="mb-2">
                        <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full ${SIGNAL_STYLE[signal]}`}>
                          <SignalIcon signal={signal} />
                          {ct.signal[signal as keyof typeof ct.signal] ?? signal}
                        </span>
                      </div>

                      {/* Metrics */}
                      <div className="grid grid-cols-3 gap-1 text-xs mb-2">
                        {c.price_change_pct != null && (
                          <div className="text-center">
                            <div className="text-slate-400 dark:text-slate-500">{ct.priceChange}</div>
                            <div className={`font-mono font-semibold ${changePos ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400"}`}>
                              {changePos ? "+" : ""}{c.price_change_pct.toFixed(2)}%
                            </div>
                          </div>
                        )}
                        {c.volume_ratio != null && (
                          <div className="text-center">
                            <div className="text-slate-400 dark:text-slate-500">{ct.volRatio}</div>
                            <div className="font-mono font-semibold text-slate-700 dark:text-slate-200">×{c.volume_ratio.toFixed(1)}</div>
                          </div>
                        )}
                        {c.rsi != null && (
                          <div className="text-center">
                            <div className="text-slate-400 dark:text-slate-500">{ct.rsi}</div>
                            <div className={`font-mono font-semibold ${c.rsi < 30 ? "text-emerald-600 dark:text-emerald-400" : c.rsi > 70 ? "text-red-600 dark:text-red-400" : "text-slate-700 dark:text-slate-200"}`}>
                              {c.rsi.toFixed(0)}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Brief rationale */}
                      {c.rationale && (
                        <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed line-clamp-2">{c.rationale}</p>
                      )}

                      {/* "Click for details" hint */}
                      <div className="mt-2 text-[10px] text-slate-300 dark:text-slate-600 flex items-center gap-1">
                        <ExternalLink className="w-2.5 h-2.5" />
                        Click for AI analysis
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
