"use client";

import dynamic from "next/dynamic";

const SoftAurora = dynamic(() => import("@/components/SoftAurora"), {
  ssr: false,
});

export function SoftAuroraBackground() {
  return (
    <div className="fixed inset-0 -z-10 pointer-events-none">
      <SoftAurora
        speed={0.6}
        scale={1.5}
        brightness={1}
        color1="#06B6D4"
        color2="#3B82F6"
        noiseFrequency={2.5}
        noiseAmplitude={1}
        bandHeight={0.5}
        bandSpread={1}
        octaveDecay={0.1}
        layerOffset={0}
        colorSpeed={1}
        enableMouseInteraction
        mouseInfluence={0.25}
      />
    </div>
  );
}
