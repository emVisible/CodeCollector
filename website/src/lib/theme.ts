const STORAGE_KEY = "cc-theme";

type Theme = "light" | "dark";

function apply(theme: Theme): void {
  document.documentElement.dataset.theme = theme;
  const btn = document.getElementById("themeToggle");
  // aria-label is managed by i18n.applyI18n()
  if (btn) {
    btn.textContent = theme === "light" ? "[\u263E]" : "[\u263C]";
  }
}

export function getTheme(): Theme {
  return (document.documentElement.dataset.theme as Theme) || "light";
}

export function initTheme(): void {
  const stored = localStorage.getItem(STORAGE_KEY);
  apply(stored === "dark" ? "dark" : "light");

  document.getElementById("themeToggle")?.addEventListener("click", () => {
    const next: Theme = getTheme() === "light" ? "dark" : "light";
    localStorage.setItem(STORAGE_KEY, next);
    apply(next);
  });
}
