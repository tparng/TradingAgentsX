import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-[1.25rem] text-sm font-bold transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus-visible:ring-ring/50 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive cursor-pointer",
  {
    variants: {
      variant: {
        default:
          // Light: ocean blue → cyan → teal | Dark: sky → teal vivid
          "bg-gradient-to-br from-blue-500 via-cyan-500 to-teal-400 dark:from-sky-400 dark:via-cyan-400 dark:to-teal-300 text-white " +
          "border border-cyan-700/30 dark:border-teal-600/40 " +
          "shadow-[0_2px_0_theme(colors.cyan.700),0_4px_12px_rgba(6,182,212,0.3),inset_0_1px_0_rgba(255,255,255,0.3)] " +
          "dark:shadow-[0_2px_0_theme(colors.teal.700),0_4px_12px_rgba(45,212,191,0.25),inset_0_1px_0_rgba(255,255,255,0.2)] " +
          "hover:-translate-y-0.5 " +
          "hover:shadow-[0_4px_0_theme(colors.cyan.700),0_8px_24px_rgba(6,182,212,0.4),inset_0_1px_0_rgba(255,255,255,0.35)] " +
          "dark:hover:shadow-[0_4px_0_theme(colors.teal.700),0_8px_24px_rgba(45,212,191,0.35),inset_0_1px_0_rgba(255,255,255,0.25)] " +
          "active:translate-y-0.5 active:scale-[0.97] " +
          "active:shadow-[0_1px_0_theme(colors.cyan.800),inset_0_2px_4px_rgba(6,182,212,0.3)] " +
          "dark:active:shadow-[0_1px_0_theme(colors.teal.800),inset_0_2px_4px_rgba(45,212,191,0.25)]",
        destructive:
          "bg-gradient-to-br from-red-400 to-red-600 text-white border border-red-700/40 " +
          "shadow-[0_2px_0_theme(colors.red.800),0_4px_12px_rgba(220,38,38,0.3)] " +
          "hover:-translate-y-0.5 hover:shadow-[0_4px_0_theme(colors.red.800),0_8px_24px_rgba(220,38,38,0.4)] " +
          "active:translate-y-0.5 active:scale-[0.97]",
        outline:
          "bg-white/95 dark:bg-[#111827]/95 border border-slate-200 dark:border-slate-700/60 text-slate-700 dark:text-slate-200 " +
          "shadow-[0_1px_3px_rgba(15,23,42,0.08)] dark:shadow-[0_1px_3px_rgba(0,0,0,0.3)] " +
          "hover:-translate-y-0.5 hover:border-cyan-400 dark:hover:border-teal-500/60 " +
          "hover:shadow-[0_4px_12px_rgba(6,182,212,0.15)] dark:hover:shadow-[0_4px_12px_rgba(45,212,191,0.2)]",
        secondary:
          "bg-gradient-to-br from-sky-50 to-cyan-50 dark:from-[#0C1929] dark:to-[#0A1F2A] " +
          "text-cyan-700 dark:text-cyan-300 border border-cyan-100 dark:border-cyan-900/40 " +
          "shadow-[0_1px_3px_rgba(15,23,42,0.06)] dark:shadow-[0_1px_3px_rgba(0,0,0,0.2)] " +
          "hover:-translate-y-0.5 hover:shadow-[0_4px_12px_rgba(6,182,212,0.12)] dark:hover:shadow-[0_4px_12px_rgba(45,212,191,0.15)]",
        ghost:
          "hover:bg-cyan-50 dark:hover:bg-cyan-900/20 text-slate-600 dark:text-slate-300 hover:text-cyan-700 dark:hover:text-cyan-300 rounded-[0.875rem]",
        link: "text-cyan-600 dark:text-cyan-400 underline-offset-4 hover:underline rounded-none",
      },
      size: {
        default: "h-10 px-5 py-2 has-[>svg]:px-4",
        sm: "h-8 rounded-[1rem] gap-1.5 px-3 has-[>svg]:px-2.5 text-xs",
        lg: "h-12 rounded-[1.25rem] px-8 has-[>svg]:px-6 text-base",
        icon: "size-10",
        "icon-sm": "size-8",
        "icon-lg": "size-12",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot : "button"

  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
