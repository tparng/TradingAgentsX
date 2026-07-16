"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";

export type FontSize = "sm" | "md" | "lg" | "xl";

const SIZES: FontSize[] = ["sm", "md", "lg", "xl"];
const STORAGE_KEY = "tradingagentsx-font-size";
const DEFAULT: FontSize = "md";

interface FontSizeContextType {
  fontSize: FontSize;
  setFontSize: (size: FontSize) => void;
}

const FontSizeContext = createContext<FontSizeContextType | undefined>(undefined);

export function FontSizeProvider({ children }: { children: ReactNode }) {
  const [fontSize, setFontSizeState] = useState<FontSize>(DEFAULT);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as FontSize | null;
    const initial = stored && SIZES.includes(stored) ? stored : DEFAULT;
    setFontSizeState(initial);
    document.documentElement.setAttribute("data-font-size", initial);
  }, []);

  const setFontSize = useCallback((size: FontSize) => {
    setFontSizeState(size);
    localStorage.setItem(STORAGE_KEY, size);
    document.documentElement.setAttribute("data-font-size", size);
  }, []);

  return (
    <FontSizeContext.Provider value={{ fontSize, setFontSize }}>
      {children}
    </FontSizeContext.Provider>
  );
}

export function useFontSize(): FontSizeContextType {
  const ctx = useContext(FontSizeContext);
  if (!ctx) throw new Error("useFontSize must be used within FontSizeProvider");
  return ctx;
}
