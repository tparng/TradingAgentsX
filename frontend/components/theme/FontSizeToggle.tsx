"use client";

import { ALargeSmall } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useFontSize, FontSize } from "@/contexts/FontSizeContext";
import { useLanguage } from "@/contexts/LanguageContext";

const OPTIONS: { value: FontSize; label: string; labelZh: string; preview: string }[] = [
  { value: "sm", label: "Small",  labelZh: "小",  preview: "A" },
  { value: "md", label: "Medium", labelZh: "中",  preview: "A" },
  { value: "lg", label: "Large",  labelZh: "大",  preview: "A" },
  { value: "xl", label: "X-Large",labelZh: "超大", preview: "A" },
];

const PREVIEW_SIZE: Record<FontSize, string> = {
  sm: "text-xs",
  md: "text-sm",
  lg: "text-base",
  xl: "text-lg",
};

export function FontSizeToggle() {
  const { fontSize, setFontSize } = useFontSize();
  const { locale } = useLanguage();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="w-9 h-9 text-slate-600 dark:text-slate-300 hover:text-blue-700 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/20"
          title={locale === "zh-TW" ? "字體大小" : "Font size"}
        >
          <ALargeSmall className="h-4 w-4" />
          <span className="sr-only">{locale === "zh-TW" ? "字體大小" : "Font size"}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {OPTIONS.map((opt) => (
          <DropdownMenuItem
            key={opt.value}
            onClick={() => setFontSize(opt.value)}
            className={fontSize === opt.value ? "bg-accent" : ""}
          >
            <span className={`mr-2 font-bold ${PREVIEW_SIZE[opt.value]}`}>{opt.preview}</span>
            <span>{locale === "zh-TW" ? opt.labelZh : opt.label}</span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
