import { en } from "../i18n/en";
import { zh } from "../i18n/zh";

export type Lang = "en" | "zh";

const STORAGE_KEY = "cc-lang";
const dicts: Record<Lang, Record<string, string>> = { en, zh };

let current: Lang = "en";
let changeListeners: Array<() => void> = [];

function detectInitial(): Lang {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "en" || stored === "zh") return stored;
  return navigator.language.toLowerCase().startsWith("zh") ? "zh" : "en";
}

export function getLang(): Lang {
  return current;
}

export function t(key: string): string {
  return dicts[current][key] ?? dicts.en[key] ?? key;
}

export function tf(key: string, vars: Record<string, string | number>): string {
  let out = t(key);
  for (const [k, v] of Object.entries(vars)) {
    out = out.replace(`{${k}}`, String(v));
  }
  return out;
}

export function applyI18n(): void {
  document.querySelectorAll<HTMLElement>("[data-i18n]").forEach((el) => {
    el.innerHTML = t(el.dataset.i18n!);
  });
  document.documentElement.lang = current;
  document.title = t("meta.title");

  const themeBtn = document.getElementById("themeToggle");
  if (themeBtn) themeBtn.setAttribute("aria-label", t("aria.theme"));

  const langBtn = document.getElementById("langToggle");
  if (langBtn) langBtn.textContent = current === "en" ? "中文" : "EN";
}

export function setLang(lang: Lang): void {
  current = lang;
  localStorage.setItem(STORAGE_KEY, lang);
  applyI18n();
  changeListeners.forEach((fn) => fn());
}

export function onLangChange(fn: () => void): void {
  changeListeners.push(fn);
}

export function initI18n(): void {
  current = detectInitial();

  // dev-time key parity check
  if (import.meta.env.DEV) {
    const enKeys = new Set(Object.keys(en));
    for (const key of Object.keys(zh)) {
      if (!enKeys.has(key)) console.warn(`[i18n] zh has unknown key: ${key}`);
    }
    for (const key of Object.keys(en)) {
      if (!(key in zh)) console.warn(`[i18n] zh missing key: ${key}`);
    }
  }

  applyI18n();

  document.getElementById("langToggle")?.addEventListener("click", () => {
    setLang(current === "en" ? "zh" : "en");
  });
}
