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
          // Light: blue → pink gradient | Dark: blue → violet gradient
          "bg-gradient-to-br from-blue-400 to-pink-500 dark:from-blue-400 dark:to-violet-500 text-white " +
          "border border-pink-600/30 dark:border-violet-700/40 " +
          "shadow-[0_2px_0_theme(colors.pink.700),0_4px_12px_rgba(219,39,119,0.3),inset_0_1px_0_rgba(255,255,255,0.3)] " +
          "dark:shadow-[0_2px_0_theme(colors.violet.800),0_4px_12px_rgba(139,92,246,0.3),inset_0_1px_0_rgba(255,255,255,0.2)] " +
          "hover:-translate-y-0.5 " +
          "hover:shadow-[0_4px_0_theme(colors.pink.700),0_8px_24px_rgba(219,39,119,0.4),inset_0_1px_0_rgba(255,255,255,0.35)] " +
          "dark:hover:shadow-[0_4px_0_theme(colors.violet.800),0_8px_24px_rgba(139,92,246,0.4),inset_0_1px_0_rgba(255,255,255,0.25)] " +
          "active:translate-y-0.5 active:scale-[0.97] " +
          "active:shadow-[0_1px_0_theme(colors.pink.800),inset_0_2px_4px_rgba(219,39,119,0.3)] " +
          "dark:active:shadow-[0_1px_0_theme(colors.violet.900),inset_0_2px_4px_rgba(139,92,246,0.3)]",
        destructive:
          "bg-gradient-to-br from-red-400 to-red-600 text-white border border-red-700/40 " +
          "shadow-[0_2px_0_theme(colors.red.800),0_4px_12px_rgba(220,38,38,0.3)] " +
          "hover:-translate-y-0.5 hover:shadow-[0_4px_0_theme(colors.red.800),0_8px_24px_rgba(220,38,38,0.4)] " +
          "active:translate-y-0.5 active:scale-[0.97]",
        outline:
          "bg-white/95 dark:bg-[#111827]/95 border border-slate-200 dark:border-slate-700/60 text-slate-700 dark:text-slate-200 " +
          "shadow-[0_1px_3px_rgba(15,23,42,0.08)] dark:shadow-[0_1px_3px_rgba(0,0,0,0.3)] " +
          "hover:-translate-y-0.5 hover:border-pink-300 dark:hover:border-violet-500/60 " +
          "hover:shadow-[0_4px_12px_rgba(219,39,119,0.12)] dark:hover:shadow-[0_4px_12px_rgba(139,92,246,0.2)]",
        secondary:
          "bg-gradient-to-br from-blue-50 to-pink-50 dark:from-[#1E293B] dark:to-[#1E1A3A] " +
          "text-blue-700 dark:text-violet-300 border border-pink-100 dark:border-violet-900/40 " +
          "shadow-[0_1px_3px_rgba(15,23,42,0.06)] dark:shadow-[0_1px_3px_rgba(0,0,0,0.2)] " +
          "hover:-translate-y-0.5 hover:shadow-[0_4px_12px_rgba(219,39,119,0.10)] dark:hover:shadow-[0_4px_12px_rgba(139,92,246,0.15)]",
        ghost:
          "hover:bg-pink-50 dark:hover:bg-violet-900/20 text-slate-600 dark:text-slate-300 hover:text-pink-700 dark:hover:text-violet-300 rounded-[0.875rem]",
        link: "text-pink-600 dark:text-violet-400 underline-offset-4 hover:underline rounded-none",
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
