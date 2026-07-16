/**
 * Watchlist page — manage tracked tickers, sync with Google Sheet,
 * and trigger AI analysis on demand or by schedule.
 */
"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { format } from "date-fns";
import { useLanguage } from "@/contexts/LanguageContext";
import { api } from "@/lib/api";
import type { WatchlistItem, WatchlistStatus } from "@/lib/types";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
import { Badge } from "@/components/ui/badge";
import {
  RefreshCw,
  Plus,
  Trash2,
  BarChart2,
  ExternalLink,
  CheckCircle2,
  XCircle,
  Clock,
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

export default function WatchlistPage() {
  const { t } = useLanguage();
  const router = useRouter();
  const wt = t.watchlist;

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

  const showToast = (msg: string, ok = true) => {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 3500);
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [itemsData, statusData] = await Promise.all([
        api.getWatchlist(),
        api.getWatchlistStatus().catch(() => null),
      ]);
      setItems(itemsData);
      setStatus(statusData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTicker.trim()) return;
    setAdding(true);
    try {
      const item = await api.addToWatchlist(newTicker.trim().toUpperCase(), newMarket, newNotes);
      setItems((prev) => [...prev, item]);
      setNewTicker("");
      setNewNotes("");
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
    } catch {
      showToast("Failed to remove", false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      const res = await api.syncWatchlistFromSheet();
      showToast(res.message || wt.syncDone);
      await load();
    } catch {
      showToast(wt.syncError, false);
    } finally {
      setSyncing(false);
    }
  };

  const handleAnalyzeAll = async () => {
    setAnalyzingAll(true);
    try {
      const res = await api.triggerWatchlistAnalysis();
      showToast(res.message || wt.analyzing);
    } catch {
      showToast("Failed to start analysis", false);
    } finally {
      setAnalyzingAll(false);
    }
  };

  const handleAnalyzeSingle = async (ticker: string) => {
    setAnalyzingTicker(ticker);
    try {
      const res = await api.triggerWatchlistAnalysis(ticker);
      showToast(res.message || wt.analyzing);
    } catch {
      showToast("Failed to start analysis", false);
    } finally {
      setAnalyzingTicker(null);
    }
  };

  const goToAnalysis = (ticker: string, market_type: string) => {
    router.push(`/analysis?ticker=${ticker}&market_type=${market_type}`);
  };

  const fmtDate = (iso?: string) => {
    if (!iso) return wt.never;
    try {
      return format(new Date(iso), "MM-dd HH:mm");
    } catch {
      return iso.slice(0, 16);
    }
  };

  const nextJob = status?.jobs?.find((j) => j.id === "daily_analysis");
  const syncJob = status?.jobs?.find((j) => j.id === "sheet_sync");

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Toast */}
      {toast && (
        <div
          className={`fixed top-20 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg text-sm font-medium transition-all
            ${toast.ok
              ? "bg-emerald-50 text-emerald-800 border border-emerald-200 dark:bg-emerald-900/40 dark:text-emerald-200 dark:border-emerald-700"
              : "bg-red-50 text-red-800 border border-red-200 dark:bg-red-900/40 dark:text-red-200 dark:border-red-700"
            }`}
        >
          {toast.ok ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
          {toast.msg}
        </div>
      )}

      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{wt.title}</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{wt.subtitle}</p>
      </div>

      {/* Status bar */}
      {status && (
        <div className="flex flex-wrap gap-3 mb-6 text-xs">
          <span className="flex items-center gap-1 text-slate-500 dark:text-slate-400">
            {status.sheets_configured
              ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              : <XCircle className="w-3.5 h-3.5 text-slate-400" />}
            {wt.statusSheets}{status.sheets_configured ? wt.connected : wt.notConfigured}
          </span>
          <span className="flex items-center gap-1 text-slate-500 dark:text-slate-400">
            {status.telegram_configured
              ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              : <XCircle className="w-3.5 h-3.5 text-slate-400" />}
            {wt.statusTelegram}{status.telegram_configured ? wt.connected : wt.notConfigured}
          </span>
          {nextJob?.next_run && (
            <span className="flex items-center gap-1 text-slate-500 dark:text-slate-400">
              <Clock className="w-3.5 h-3.5" />
              Next analysis: {fmtDate(nextJob.next_run)}
            </span>
          )}
          {syncJob?.next_run && (
            <span className="flex items-center gap-1 text-slate-500 dark:text-slate-400">
              <Clock className="w-3.5 h-3.5" />
              Next sync: {fmtDate(syncJob.next_run)}
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
              <Input
                placeholder={wt.tickerPlaceholder}
                value={newTicker}
                onChange={(e) => setNewTicker(e.target.value.toUpperCase())}
                className="font-mono"
              />
            </div>
            <Select value={newMarket} onValueChange={setNewMarket}>
              <SelectTrigger className="w-28">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {MARKET_OPTIONS.map((o) => (
                  <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <div className="flex-1 min-w-[160px]">
              <Input
                placeholder={wt.notesPlaceholder}
                value={newNotes}
                onChange={(e) => setNewNotes(e.target.value)}
              />
            </div>
            <Button type="submit" disabled={adding || !newTicker.trim()} className="gap-1.5">
              <Plus className="w-4 h-4" />
              {wt.addTicker}
            </Button>
          </form>

          <div className="flex gap-2 mt-4 flex-wrap">
            <Button
              variant="outline"
              size="sm"
              onClick={handleSync}
              disabled={syncing || !status?.sheets_configured}
              className="gap-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${syncing ? "animate-spin" : ""}`} />
              {syncing ? wt.syncing : wt.syncFromSheet}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleAnalyzeAll}
              disabled={analyzingAll || items.length === 0}
              className="gap-1.5"
            >
              <BarChart2 className="w-3.5 h-3.5" />
              {analyzingAll ? "Starting..." : wt.analyzeAll}
            </Button>
            <Button variant="ghost" size="sm" onClick={load} className="gap-1.5 ml-auto">
              <RefreshCw className="w-3.5 h-3.5" />
              {t.history?.refresh ?? "Refresh"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Watchlist table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="py-16 text-center text-slate-400 text-sm">{t.common.loading}</div>
          ) : items.length === 0 ? (
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
                  {items.map((item) => {
                    const rec = (item.last_recommendation ?? "").toUpperCase();
                    return (
                      <TableRow
                        key={item.id}
                        className="border-b border-slate-50 dark:border-slate-800/50 hover:bg-slate-50 dark:hover:bg-slate-800/30"
                      >
                        <TableCell className="font-mono font-semibold text-blue-700 dark:text-blue-300">
                          {item.ticker}
                        </TableCell>
                        <TableCell>
                          <span className="text-xs uppercase font-medium text-slate-500 dark:text-slate-400">
                            {item.market_type}
                          </span>
                        </TableCell>
                        <TableCell className="hidden md:table-cell text-slate-500 dark:text-slate-400 text-xs max-w-[160px] truncate">
                          {item.notes || "—"}
                        </TableCell>
                        <TableCell className="hidden lg:table-cell text-xs text-slate-400">
                          {fmtDate(item.added_at)}
                        </TableCell>
                        <TableCell className="text-xs text-slate-400">
                          {item.last_analyzed_at ? fmtDate(item.last_analyzed_at) : wt.never}
                        </TableCell>
                        <TableCell>
                          {rec ? (
                            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${REC_COLOR[rec] ?? "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300"}`}>
                              {rec}
                            </span>
                          ) : (
                            <span className="text-slate-300 dark:text-slate-600">—</span>
                          )}
                        </TableCell>
                        <TableCell className="hidden sm:table-cell text-xs font-mono text-slate-500 dark:text-slate-400">
                          {item.last_score != null ? `${item.last_score.toFixed(1)}` : "—"}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7 text-slate-400 hover:text-blue-600"
                              title={wt.goToAnalysis}
                              onClick={() => goToAnalysis(item.ticker, item.market_type)}
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7 text-slate-400 hover:text-emerald-600"
                              title={wt.analyze}
                              onClick={() => handleAnalyzeSingle(item.ticker)}
                              disabled={analyzingTicker === item.ticker}
                            >
                              <BarChart2 className={`w-3.5 h-3.5 ${analyzingTicker === item.ticker ? "animate-pulse" : ""}`} />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7 text-slate-400 hover:text-red-500"
                              title={wt.remove}
                              onClick={() => handleRemove(item.ticker)}
                            >
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
    </div>
  );
}
