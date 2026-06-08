"use client";

import { useEffect, useState } from "react";

const STORAGE_KEY = "gold-dashboard-visual-mode";
type VisualMode = "on" | "off";

function readVisualMode(): VisualMode {
  if (typeof document === "undefined") {
    return "off";
  }
  return document.documentElement.dataset.visualMode === "on" ? "on" : "off";
}

export default function VisualModeToggle() {
  const [visualMode, setVisualMode] = useState<VisualMode>("off");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setVisualMode(readVisualMode());
    setMounted(true);
  }, []);

  function toggleVisualMode() {
    const nextMode: VisualMode = visualMode === "on" ? "off" : "on";
    document.documentElement.dataset.visualMode = nextMode;
    localStorage.setItem(STORAGE_KEY, nextMode);
    setVisualMode(nextMode);
  }

  const isOn = visualMode === "on";
  const buttonText = mounted && isOn ? "BASE MODE" : "VISUAL MODE";
  const ariaLabel = mounted && isOn ? "Return to base dashboard mode" : "Activate visual command mode";

  return (
    <button
      type="button"
      className="visualModeToggle"
      aria-label={ariaLabel}
      aria-pressed={mounted ? isOn : false}
      suppressHydrationWarning
      onClick={toggleVisualMode}
    >
      <span className="visualModeDot" aria-hidden="true" />
      <span>{buttonText}</span>
    </button>
  );
}
