"use client";

import { useLayoutEffect, useRef } from "react";

/**
 * Scroll-linked depth motion. Instead of a one-shot fade, every wrapped section
 * is continuously driven by its position in the viewport: it rushes in from the
 * distance (scaled down + faded) and settles to 1:1 as it reaches a comfortable
 * reading position. This keeps the hero's "pushed toward you" dive going all the
 * way down the page so the whole experience feels unified.
 *
 * All registered elements share one scroll listener + rAF for performance.
 * Respects prefers-reduced-motion.
 */

const items = new Set<HTMLElement>();
let rafId = 0;
let bound = false;

const clamp = (v: number, a: number, b: number) => Math.min(Math.max(v, a), b);
const easeOut = (x: number) => 1 - Math.pow(1 - x, 3);

function apply(el: HTMLElement) {
  const r = el.getBoundingClientRect();
  const vh = window.innerHeight || 1;
  // Progress 0→1 as the element's top edge rises from ~94% to ~52% of the viewport.
  const p = clamp((vh * 0.94 - r.top) / (vh * (0.94 - 0.52)), 0, 1);
  const e = easeOut(p);
  // Stronger depth: rushes in smaller, lifts further, and turns in from the side.
  const scale = 0.8 + e * 0.2;
  const ty = (1 - e) * 80;
  // Alternating horizontal drift + a slight Y-axis rotation so adjacent sections
  // swing in from opposite sides like pages turning toward you.
  const dir = el.dataset.from === "left" ? -1 : el.dataset.from === "right" ? 1 : 0;
  const tx = dir * (1 - e) * 110;
  const ry = dir * (1 - e) * 9;
  const blur = ((1 - e) * 6).toFixed(2);
  el.style.transform = `perspective(1200px) translate3d(${tx.toFixed(1)}px, ${ty.toFixed(1)}px, 0) rotateY(${ry.toFixed(2)}deg) scale(${scale.toFixed(4)})`;
  el.style.opacity = (0.05 + e * 0.95).toFixed(4);
  el.style.filter = p < 0.999 ? `blur(${blur}px)` : "none";
}

function tick() {
  rafId = 0;
  items.forEach(apply);
}

function onScroll() {
  if (!rafId) rafId = requestAnimationFrame(tick);
}

export function ScrollReveal({
  children,
  className = "",
  from = "center",
}: {
  children: React.ReactNode;
  className?: string;
  /** Direction the section drifts in from as it's pushed toward the viewer. */
  from?: "left" | "right" | "center";
}) {
  const ref = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    items.add(el);
    apply(el); // set initial state before paint to avoid a flash
    if (!bound) {
      window.addEventListener("scroll", onScroll, { passive: true });
      window.addEventListener("resize", onScroll);
      bound = true;
    }

    return () => {
      items.delete(el);
      if (items.size === 0 && bound) {
        window.removeEventListener("scroll", onScroll);
        window.removeEventListener("resize", onScroll);
        if (rafId) cancelAnimationFrame(rafId);
        rafId = 0;
        bound = false;
      }
    };
  }, []);

  return (
    <div ref={ref} data-from={from} className={`scroll-reveal ${className}`}>
      {children}
    </div>
  );
}
