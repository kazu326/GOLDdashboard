"use client";

import { useEffect, useState } from "react";

const STORAGE_KEY = "gold-dashboard-theme";
type Theme = "dark" | "light";

function readTheme(): Theme {
  if (typeof document === "undefined") {
    return "dark";
  }
  return document.documentElement.dataset.theme === "light" ? "light" : "dark";
}

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("dark");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setTheme(readTheme());
    setMounted(true);
  }, []);

  function toggleTheme() {
    const nextTheme: Theme = theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = nextTheme;
    localStorage.setItem(STORAGE_KEY, nextTheme);
    setTheme(nextTheme);
  }

  const isLight = theme === "light";
  const buttonText = mounted ? (isLight ? "Light" : "Dark") : "Theme";
  const ariaLabel = mounted ? `Switch to ${isLight ? "dark" : "light"} theme` : "Switch dashboard theme";

  return (
    <button
      type="button"
      className="themeToggle"
      aria-label={ariaLabel}
      aria-pressed={mounted ? isLight : false}
      suppressHydrationWarning
      onClick={toggleTheme}
    >
      <span className="themeToggleTrack" aria-hidden="true">
        <span className="themeToggleThumb" />
      </span>
      <span className="themeToggleText">{buttonText}</span>
    </button>
  );
}
