"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Loader2, Circle } from "lucide-react";
import type { ProgressData } from "@/hooks/useAnalysis";

// Analyst form key → pipeline node name (only for the "analysts" phase)
const ANALYST_KEY_TO_NODE: Record<string, string> = {
  market:       "Market Analyst",
  social:       "Social Analyst",
  news:         "News Analyst",
  fundamentals: "Fundamentals Analyst",
  quant:        "Quant Analyst",
};

// Full ordered pipeline — analyst-phase entries are filtered by selected analysts at render time
const PIPELINE: { node: string; label_zh: string; label_en: string; phase: string }[] = [
  { node: "Market Analyst",       label_zh: "市場技術分析",       label_en: "Market Technical Analysis",    phase: "analysts" },
  { node: "Social Analyst",       label_zh: "社群媒體情緒分析",   label_en: "Social Media Sentiment",       phase: "analysts" },
  { node: "News Analyst",         label_zh: "新聞分析",           label_en: "News Analysis",                phase: "analysts" },
  { node: "Fundamentals Analyst", label_zh: "基本面分析",         label_en: "Fundamentals Analysis",        phase: "analysts" },
  { node: "Quant Analyst",        label_zh: "量化分析",           label_en: "Quantitative Analysis",        phase: "analysts" },
  { node: "Report Summarizer",    label_zh: "分析報告摘要",       label_en: "Report Summarization",         phase: "research" },
  { node: "Bull Researcher",      label_zh: "看漲研究員評估",     label_en: "Bull Researcher",              phase: "research" },
  { node: "Bear Researcher",      label_zh: "看跌研究員評估",     label_en: "Bear Researcher",              phase: "research" },
  { node: "Research Manager",     label_zh: "研究主管整合觀點",   label_en: "Research Manager Decision",    phase: "research" },
  { node: "Risky Analyst",        label_zh: "激進派風險辯論",     label_en: "Aggressive Risk Debate",       phase: "risk" },
  { node: "Neutral Analyst",      label_zh: "中立派風險辯論",     label_en: "Neutral Risk Debate",          phase: "risk" },
  { node: "Safe Analyst",         label_zh: "保守派風險辯論",     label_en: "Conservative Risk Debate",     phase: "risk" },
  { node: "Risk Judge",           label_zh: "風險主管最終決策",   label_en: "Risk Manager Decision",        phase: "risk" },
  { node: "Trader",               label_zh: "交易員制定建議",     label_en: "Trader Final Recommendation",  phase: "trader" },
];

const PHASE_LABELS: Record<string, { zh: string; en: string; color: string }> = {
  analysts: { zh: "分析師",  en: "Analysts",  color: "text-blue-600 dark:text-blue-400" },
  research: { zh: "研究員",  en: "Researchers", color: "text-purple-600 dark:text-purple-400" },
  risk:     { zh: "風險管理", en: "Risk Mgmt",  color: "text-orange-600 dark:text-orange-400" },
  trader:   { zh: "交易員",  en: "Trader",    color: "text-green-600 dark:text-green-400" },
};

function formatElapsed(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

interface Props {
  progressData: ProgressData | null;
  locale?: string;
  analysts?: string[];
}

export function AnalysisProgress({ progressData, locale = "zh-TW", analysts }: Props) {
  const isZh = locale === "zh-TW";

  // Live elapsed-time ticker (counts up every second from the server value)
  const [displayElapsed, setDisplayElapsed] = useState(progressData?.elapsed ?? 0);
  useEffect(() => {
    setDisplayElapsed(progressData?.elapsed ?? 0);
    const id = setInterval(() => setDisplayElapsed((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, [progressData?.elapsed]);

  const completedSet = new Set(progressData?.completed ?? []);
  const currentStep = progressData?.step ?? null;

  // Filter analyst-phase steps to only those the user selected.
  // Non-analyst phases (research, risk, trader) always appear.
  const selectedNodeSet = analysts
    ? new Set(analysts.map((k) => ANALYST_KEY_TO_NODE[k]).filter(Boolean))
    : null;

  const activePipeline = PIPELINE.filter(
    (s) => s.phase !== "analysts" || !selectedNodeSet || selectedNodeSet.has(s.node)
  );

  // Only show steps up to a few ahead of the current/last-completed position
  const activeIdx = activePipeline.findIndex((s) => s.node === currentStep);
  const lastCompletedIdx = activePipeline.reduce((acc, s, i) => completedSet.has(s.node) ? i : acc, -1);
  const showUpTo = Math.max(activeIdx, lastCompletedIdx) + 3;

  const visibleSteps = activePipeline.filter((_, i) => i <= showUpTo);

  return (
    <div className="w-full max-w-lg mx-auto py-8 px-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
          <span className="font-semibold text-base text-slate-700 dark:text-slate-200">
            {isZh ? "正在執行分析..." : "Running analysis..."}
          </span>
        </div>
        <span className="text-sm font-mono text-slate-500 dark:text-slate-400 tabular-nums">
          {formatElapsed(displayElapsed)}
        </span>
      </div>

      {/* Step list */}
      <div className="space-y-1">
        {visibleSteps.map((step, idx) => {
          const done = completedSet.has(step.node);
          const active = step.node === currentStep && !done;
          const pending = !done && !active;
          const label = isZh ? step.label_zh : step.label_en;
          const phaseInfo = PHASE_LABELS[step.phase];

          // Show phase header when phase changes
          const showPhaseHeader = idx === 0 || visibleSteps[idx - 1]?.phase !== step.phase;
          const isPhaseVisible = visibleSteps.some((s) => s.phase === step.phase);

          return (
            <div key={step.node}>
              {showPhaseHeader && isPhaseVisible && (
                <div className={`text-xs font-semibold uppercase tracking-wide mt-4 mb-1 ${phaseInfo.color}`}>
                  {isZh ? phaseInfo.zh : phaseInfo.en}
                </div>
              )}
              <div className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-300 ${
                active  ? "bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800" :
                done    ? "opacity-70" : "opacity-40"
              }`}>
                {done   && <CheckCircle2 className="h-4 w-4 text-green-500 flex-shrink-0" />}
                {active && <Loader2 className="h-4 w-4 text-blue-500 animate-spin flex-shrink-0" />}
                {pending && <Circle className="h-4 w-4 text-slate-300 dark:text-slate-600 flex-shrink-0" />}
                <span className={`text-sm ${
                  done   ? "text-slate-500 dark:text-slate-400 line-through" :
                  active ? "text-blue-700 dark:text-blue-300 font-medium" :
                           "text-slate-400 dark:text-slate-500"
                }`}>
                  {label}
                </span>
              </div>
            </div>
          );
        })}

        {/* "More steps ahead" hint when nothing is active yet */}
        {!currentStep && completedSet.size === 0 && (
          <div className="flex items-center gap-3 px-3 py-2 opacity-40">
            <Circle className="h-4 w-4 text-slate-300 dark:text-slate-600 flex-shrink-0" />
            <span className="text-sm text-slate-400 dark:text-slate-500">
              {isZh ? "準備中..." : "Initializing..."}
            </span>
          </div>
        )}
      </div>

      <p className="text-xs text-slate-400 dark:text-slate-500 mt-6 text-center">
        {isZh
          ? "分析通常需要 5–20 分鐘，請耐心等待"
          : "Analysis typically takes 5–20 minutes"}
      </p>
    </div>
  );
}
