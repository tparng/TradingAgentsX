/**
 * Error Alert Component
 * Displays user-friendly error messages with special handling for rate limits
 */
"use client";

import { useState } from "react";
import { AlertCircle, Clock, TrendingUp, Copy, Check, ChevronDown, ChevronUp } from "lucide-react";
import { Card } from "@/components/ui/card";

interface ErrorAlertProps {
  error: string | {
    error: string;
    error_type?: string;
    retry_after?: number;
    quota_limit?: number;
  };
}

export function ErrorAlert({ error }: ErrorAlertProps) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const isRateLimit = typeof error === "object" && error.error_type === "rate_limit";
  const errorMessage = typeof error === "string" ? error : error.error;
  const errorType = typeof error === "object" ? error.error_type : undefined;
  const retryAfter = typeof error === "object" ? error.retry_after : null;
  const quotaLimit = typeof error === "object" ? error.quota_limit : null;

  const TRUNCATE_LIMIT = 300;
  const isLong = errorMessage.length > TRUNCATE_LIMIT;
  const displayMessage = isLong && !expanded
    ? errorMessage.slice(0, TRUNCATE_LIMIT) + "…"
    : errorMessage;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(errorMessage);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getRetryTimeDisplay = (seconds: number | null) => {
    if (!seconds) return null;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    if (minutes > 0) return `${minutes} 分 ${remainingSeconds} 秒`;
    return `${remainingSeconds} 秒`;
  };

  return (
    <Card className={`p-6 border-2 ${
      isRateLimit
        ? "bg-orange-50 dark:bg-orange-900/20 border-orange-300 dark:border-orange-700"
        : "bg-red-50 dark:bg-red-900/20 border-red-300 dark:border-red-700"
    }`}>
      <div className="flex items-start gap-4">
        <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
          isRateLimit
            ? "bg-orange-100 dark:bg-orange-800"
            : "bg-red-100 dark:bg-red-800"
        }`}>
          {isRateLimit
            ? <Clock className="w-5 h-5 text-orange-600 dark:text-orange-400" />
            : <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
          }
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2 mb-2">
            <h3 className={`font-semibold text-lg ${
              isRateLimit
                ? "text-orange-900 dark:text-orange-200"
                : "text-red-900 dark:text-red-200"
            }`}>
              {isRateLimit ? "API 請求額度已達上限" : "分析失敗"}
            </h3>

            {/* Error type badge */}
            {errorType && errorType !== "rate_limit" && (
              <span className="shrink-0 text-xs font-mono px-2 py-0.5 rounded bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800">
                {errorType}
              </span>
            )}
          </div>

          {/* Error message */}
          <div className={`mb-3 text-sm font-mono whitespace-pre-wrap break-words rounded-md p-3 ${
            isRateLimit
              ? "bg-orange-100/50 dark:bg-orange-900/30 text-orange-900 dark:text-orange-200"
              : "bg-red-100/50 dark:bg-red-900/30 text-red-900 dark:text-red-200"
          }`}>
            {displayMessage}
          </div>

          {/* Expand / Copy row */}
          <div className="flex items-center gap-2 mb-3">
            {isLong && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
              >
                {expanded
                  ? <><ChevronUp className="w-3 h-3" />收起</>
                  : <><ChevronDown className="w-3 h-3" />顯示完整訊息</>
                }
              </button>
            )}
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors ml-auto"
            >
              {copied
                ? <><Check className="w-3 h-3 text-green-500" />已複製</>
                : <><Copy className="w-3 h-3" />複製錯誤訊息</>
              }
            </button>
          </div>

          {/* Rate-limit specific extras */}
          {isRateLimit && (
            <div className="space-y-3 mt-4">
              {retryAfter && (
                <div className="flex items-start gap-2 bg-white/50 dark:bg-gray-900/50 p-3 rounded-lg">
                  <Clock className="w-4 h-4 text-orange-600 dark:text-orange-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">建議等待時間</p>
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      請在 <span className="font-bold text-orange-600 dark:text-orange-400">
                        {getRetryTimeDisplay(retryAfter)}
                      </span> 後重試
                    </p>
                  </div>
                </div>
              )}
              {quotaLimit && (
                <div className="flex items-start gap-2 bg-white/50 dark:bg-gray-900/50 p-3 rounded-lg">
                  <TrendingUp className="w-4 h-4 text-orange-600 dark:text-orange-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">每日額度限制</p>
                    <p className="text-sm text-gray-700 dark:text-gray-300">當前計劃：每日 {quotaLimit} 次請求</p>
                  </div>
                </div>
              )}
              <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 p-4 rounded-lg mt-4">
                <p className="text-sm font-semibold text-blue-900 dark:text-blue-200 mb-2">💡 解決方案：</p>
                <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-1.5 list-disc list-inside">
                  <li>等待額度重置（通常為每日重置）</li>
                  <li>升級至付費方案以獲得更高額度</li>
                  <li>減少分析師數量或研究深度以降低 API 呼叫次數</li>
                  <li>使用不同的 API 金鑰（如果有多個帳戶）</li>
                </ul>
              </div>
            </div>
          )}

          {/* General error hints */}
          {!isRateLimit && (
            <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 p-3 rounded-lg text-xs text-blue-800 dark:text-blue-300">
              <p className="font-semibold mb-1">💡 常見原因：</p>
              <ul className="space-y-0.5 list-disc list-inside">
                <li>Ollama 未啟動或模型未下載（Connection refused）</li>
                <li>API 金鑰無效或未填寫</li>
                <li>網路連線問題或 API 服務暫時不可用</li>
              </ul>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
