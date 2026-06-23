"use client";

import { useEffect } from "react";

/**
 * Custom pointer: a crisp dot that tracks the cursor exactly, plus a larger
 * ring that eases in behind it. Over interactive elements (links, buttons,
 * inputs, cards) the ring grows and tints brand cyan; on press it dips for
 * tactile feedback.
 *
 * Activates only on devices with a fine, hovering pointer and when motion is
 * allowed — otherwise the native cursor is left untouched (touch screens,
 * prefers-reduced-motion). Driven by rAF + direct style writes, so it never
 * triggers a React re-render.
 */

const INTERACTIVE = "a, button, [role='button'], input, textarea, select, label, summary, .interactive-card, .cursor-pointer";

export function CustomCursor() {
  useEffect(() => {
    const fine = window.matchMedia("(pointer: fine)").matches;
    const canHover = window.matchMedia("(hover: hover)").matches;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!fine || !canHover || reduced) return;

    const dot = document.createElement("div");
    dot.className = "cursor-dot";
    const ring = document.createElement("div");
    ring.className = "cursor-ring";
    document.body.append(dot, ring);
    document.documentElement.classList.add("has-custom-cursor");

    // Target = real pointer position; ring eases toward it each frame.
    let tx = window.innerWidth / 2;
    let ty = window.innerHeight / 2;
    let rx = tx;
    let ry = ty;
    let raf = 0;
    let visible = false;

    const render = () => {
      rx += (tx - rx) * 0.18;
      ry += (ty - ry) * 0.18;
      dot.style.transform = `translate3d(${tx}px, ${ty}px, 0) translate(-50%, -50%)`;
      ring.style.transform = `translate3d(${rx}px, ${ry}px, 0) translate(-50%, -50%)`;
      raf = requestAnimationFrame(render);
    };

    const onMove = (e: PointerEvent) => {
      tx = e.clientX;
      ty = e.clientY;
      if (!visible) {
        visible = true;
        document.documentElement.classList.add("cursor-active");
      }
    };

    const onOver = (e: PointerEvent) => {
      const target = e.target as Element | null;
      const hot = !!target?.closest?.(INTERACTIVE);
      ring.classList.toggle("is-hover", hot);
      dot.classList.toggle("is-hover", hot);
    };

    const onDown = () => ring.classList.add("is-down");
    const onUp = () => ring.classList.remove("is-down");
    const onLeave = () => document.documentElement.classList.remove("cursor-active");
    const onEnter = () => document.documentElement.classList.add("cursor-active");

    raf = requestAnimationFrame(render);
    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("pointerover", onOver, { passive: true });
    window.addEventListener("pointerdown", onDown, { passive: true });
    window.addEventListener("pointerup", onUp, { passive: true });
    document.addEventListener("pointerleave", onLeave);
    document.addEventListener("pointerenter", onEnter);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerover", onOver);
      window.removeEventListener("pointerdown", onDown);
      window.removeEventListener("pointerup", onUp);
      document.removeEventListener("pointerleave", onLeave);
      document.removeEventListener("pointerenter", onEnter);
      dot.remove();
      ring.remove();
      document.documentElement.classList.remove("has-custom-cursor", "cursor-active");
    };
  }, []);

  return null;
}
