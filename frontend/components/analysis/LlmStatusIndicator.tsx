"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

type Status = "checking" | "online" | "offline";

interface Props {
  baseUrl: string;
}

const POLL_INTERVAL_MS = 30_000;

export function LlmStatusIndicator({ baseUrl }: Props) {
  const [status, setStatus] = useState<Status>("checking");
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const urlRef = useRef(baseUrl);

  const check = async (url: string) => {
    setStatus("checking");
    try {
      const res = await api.checkLlmStatus(url);
      setStatus(res.status === "online" ? "online" : "offline");
    } catch {
      setStatus("offline");
    }
  };

  useEffect(() => {
    urlRef.current = baseUrl;

    // Debounce URL changes by 600 ms so rapid typing doesn't flood the backend
    const debounce = setTimeout(() => {
      check(baseUrl);

      if (timerRef.current) clearInterval(timerRef.current);
      timerRef.current = setInterval(() => check(urlRef.current), POLL_INTERVAL_MS);
    }, 600);

    return () => {
      clearTimeout(debounce);
    };
  }, [baseUrl]);

  // Cleanup interval on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const dotClass =
    status === "online"
      ? "bg-green-500"
      : status === "offline"
      ? "bg-red-500"
      : "bg-slate-400 animate-pulse";

  const label =
    status === "online" ? "Online" : status === "offline" ? "Offline" : "Checking...";

  const textClass =
    status === "online"
      ? "text-green-600 dark:text-green-400"
      : status === "offline"
      ? "text-red-600 dark:text-red-400"
      : "text-slate-400";

  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`inline-block h-2 w-2 rounded-full flex-shrink-0 ${dotClass}`} />
      <span className={`text-xs font-medium ${textClass}`}>{label}</span>
    </span>
  );
}
