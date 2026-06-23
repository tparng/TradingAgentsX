"use client";

import { useLayoutEffect, useRef } from "react";

/**
 * Pointer-reactive wrapper for the homepage content cards.
 *
 *   • Tracks the cursor as `--mx` / `--my` for a radial spotlight glow and applies
 *     a small 3D tilt — driven by CSS vars so React never re-renders on move.
 *   • Reveals on scroll: the card starts dropped + faded and pops up when it
 *     enters the viewport, staggered by its position in the grid so a row of
 *     cards cascades in instead of all appearing at once.
 *
 * The tilt lives on the outer element and the entrance on an inner wrapper, so
 * the two transforms never collide. No-ops under prefers-reduced-motion.
 */
export function InteractiveCard({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const innerRef = useRef<HTMLDivElement>(null);

  const onMove = (e: React.PointerEvent<HTMLDivElement>) => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    el.style.setProperty("--mx", `${(x * 100).toFixed(1)}%`);
    el.style.setProperty("--my", `${(y * 100).toFixed(1)}%`);
    const rx = (0.5 - y) * 7;
    const ry = (x - 0.5) * 7;
    el.style.setProperty("--rx", `${rx.toFixed(2)}deg`);
    el.style.setProperty("--ry", `${ry.toFixed(2)}deg`);
  };

  const onLeave = () => {
    const el = ref.current;
    if (!el) return;
    el.style.setProperty("--rx", "0deg");
    el.style.setProperty("--ry", "0deg");
  };

  useLayoutEffect(() => {
    const el = ref.current;
    const inner = innerRef.current;
    if (!el || !inner) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    // Stagger by position among grid siblings so a row cascades in.
    const siblings = el.parentElement ? Array.from(el.parentElement.children) : [];
    const idx = Math.max(0, siblings.indexOf(el));
    inner.style.transitionDelay = `${Math.min(idx, 9) * 75}ms`;

    inner.classList.add("reveal-init"); // hide before paint, no flash

    const io = new IntersectionObserver(
      (entries, obs) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            inner.classList.add("is-in");
            obs.unobserve(entry.target);
          }
        }
      },
      { threshold: 0.15, rootMargin: "0px 0px -8% 0px" },
    );
    io.observe(el);

    return () => io.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      onPointerMove={onMove}
      onPointerLeave={onLeave}
      className={`interactive-card ${className}`}
    >
      <div ref={innerRef} className="ic-reveal">
        {children}
      </div>
    </div>
  );
}
