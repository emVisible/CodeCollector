/* live demo engine — a faithful mini port of the real formatter rules */

import { copyText, showToast } from "./copy";
import { tf, t } from "./i18n";
import {
  DEMO_FILES,
  GITIGNORE_PATTERNS,
  WHITELIST_EXTS,
  type DemoFile,
} from "../data/demoRepo";

interface Preset {
  filterOn: boolean;
  include: string | null;
}

const PRESETS: Record<string, Preset> = {
  default: { filterOn: true, include: null },
  all: { filterOn: false, include: null },
  src: { filterOn: true, include: "src/**" },
};

let currentPreset = "default";
const checked = new Set<string>();
let lastOutput = "";
let lastTokenCount = 0;

/* ── rule engine (mirrors collector.py) ─────────────────────── */

function globToRegex(pattern: string): RegExp {
  let re = "";
  for (let i = 0; i < pattern.length; i++) {
    const c = pattern[i];
    if (c === "*") {
      if (pattern[i + 1] === "*") {
        re += pattern[i + 2] === "/" ? "(?:.*/)?" : ".*";
        i += pattern[i + 2] === "/" ? 2 : 1;
      } else {
        re += "[^/]*";
      }
    } else if (c === "?") {
      re += "[^/]";
    } else {
      re += c.replace(/[.+^${}()|[\]\\]/g, "\\$&");
    }
  }
  return new RegExp(`^${re}$`);
}

function isGitignored(path: string): boolean {
  return GITIGNORE_PATTERNS.some((p) =>
    p.endsWith("/") ? path.startsWith(p) : path === p || path.endsWith("/" + p),
  );
}

function passesRules(file: DemoFile, preset: Preset): true | string {
  if (file.binary) return "binary";
  const ext = file.path.slice(file.path.lastIndexOf("."));
  const nameOk =
    file.path === ".env" ||
    WHITELIST_EXTS.some((e) => file.path.toLowerCase().endsWith(e));
  if (!nameOk && ext !== ".env") return "ext";
  if (preset.filterOn && isGitignored(file.path)) return "gitignored";
  if (preset.include && !globToRegex(preset.include).test(file.path)) {
    return "--include";
  }
  return true;
}

/* ── markdown generation (mirrors formatter.py) ─────────────── */

function fenceMarker(content: string): string {
  const runs = content.match(/`{3,}/g);
  const longest = runs ? Math.max(...runs.map((r) => r.length)) : 0;
  return "`".repeat(Math.max(3, longest + 1));
}

function estimateTokens(text: string): number {
  return Math.max(1, Math.ceil(text.length / 4));
}

function buildTree(paths: string[]): string[] {
  interface TreeNode {
    [name: string]: TreeNode | null;
  }
  const root: TreeNode = {};
  for (const p of paths) {
    let node = root;
    const parts = p.split("/");
    parts.forEach((part, idx) => {
      if (idx === parts.length - 1) node[part] ??= null;
      else node[part] ??= {};
      node = node[part] as TreeNode;
    });
  }
  const lines: string[] = [];
  function walk(node: TreeNode, prefix: string): void {
    const items = Object.entries(node).sort(([a, av], [b, bv]) => {
      const aDir = av !== null;
      const bDir = bv !== null;
      if (aDir !== bDir) return aDir ? -1 : 1;
      return a.localeCompare(b);
    });
    items.forEach(([name, child], i) => {
      const last = i === items.length - 1;
      lines.push(`${prefix}${last ? "\u2514\u2500\u2500 " : "\u251C\u2500\u2500 "}${name}`);
      if (child) walk(child, prefix + (last ? "    " : "\u2502   "));
    });
  }
  walk(root, "");
  return lines.length ? lines : ["(empty)"];
}

function generateMarkdown(selected: DemoFile[], filterOn: boolean): { text: string; tokens: number } {
  const now = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  const stamp = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;

  const out: string[] = [];
  out.push("# OnePaste - Collection Summary", "");
  out.push(`**Generated:** ${stamp}  `);
  out.push("**Root:** `~/mini-repo`  ");
  out.push("**Mode:** Recursive  ");
  if (filterOn) out.push("**Filter:** `.gitignore` enabled  ");

  let totalLines = 0;
  let totalTokens = 0;

  for (const f of selected) {
    const lines = f.content.split("\n").length - (f.content.endsWith("\n") ? 1 : 0) + (f.content ? 0 : 0);
    totalLines += Math.max(1, lines);
    totalTokens += estimateTokens(f.content);
  }

  out.push("");
  out.push(`**Files collected:** ${selected.length}  `);
  out.push(`**Total lines:** ${totalLines.toLocaleString("en-US")}  `);
  out.push(`**Total size:** ${(selected.reduce((n, f) => n + f.content.length, 0) / 1024).toFixed(1)} KB  `);
  out.push(`**Total tokens:** ${totalTokens.toLocaleString("en-US")} *(estimate)*  `);

  out.push("", "## Directory Tree", "", "```", ...buildTree(selected.map((f) => f.path)), "```");

  for (const f of selected) {
    const lang = f.lang || "text";
    const lineCount = Math.max(1, f.content.split("\n").length - (f.content.endsWith("\n") ? 1 : 0));
    const fence = fenceMarker(f.content);
    out.push(
      "",
      `### \`${f.path}\``,
      "",
      `**Lines:** ${lineCount} | **Size:** ${f.content.length.toLocaleString("en-US")} bytes | **Tokens:** ${estimateTokens(f.content).toLocaleString("en-US")}`,
      "",
      `${fence}${lang}`,
      f.content.trimEnd(),
      `${fence}`,
    );
  }

  return { text: out.join("\n") + "\n", tokens: totalTokens };
}

/* ── rendering ──────────────────────────────────────────────── */

function reasonLabel(reason: string): string {
  switch (reason) {
    case "binary":
      return "binary";
    case "gitignored":
      return "gitignored";
    case "--include":
      return "--include";
    default:
      return "";
  }
}

function renderTree(preset: Preset): void {
  const ul = document.getElementById("fileTree");
  if (!ul) return;
  ul.innerHTML = "";

  for (const file of DEMO_FILES) {
    const verdict = passesRules(file, preset);
    const li = document.createElement("li");
    const includable = verdict === true;

    const label = document.createElement("label");
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = checked.has(file.path);
    cb.disabled = !includable;
    cb.addEventListener("change", () => {
      if (cb.checked) checked.add(file.path);
      else checked.delete(file.path);
      render();
    });

    const pathSpan = document.createElement("span");
    pathSpan.className = "fpath";
    pathSpan.textContent = file.path;

    label.append(cb, pathSpan);

    if (!includable) {
      li.classList.add("is-excluded");
      const reason = document.createElement("span");
      reason.className = "reason";
      reason.textContent = reasonLabel(verdict);
      label.appendChild(reason);
    }

    li.appendChild(label);
    ul.appendChild(li);
  }
}

function popNumber(el: HTMLElement | null): void {
  if (!el) return;
  el.style.transform = "scale(1.18)";
  window.setTimeout(() => {
    el.style.transition = "transform .25s ease";
    el.style.transform = "scale(1)";
    window.setTimeout(() => (el.style.transition = ""), 260);
  }, 30);
}

function render(): void {
  const preset = PRESETS[currentPreset];
  renderTree(preset);

  const selected = DEMO_FILES.filter(
    (f) => checked.has(f.path) && passesRules(f, preset) === true,
  );

  const { text, tokens } = generateMarkdown(selected, preset.filterOn);
  lastOutput = text;
  lastTokenCount = tokens;

  const previewCode = document.querySelector("#demoPreview code");
  if (previewCode) previewCode.textContent = text;

  const tokEl = document.getElementById("demoTokens");
  if (tokEl) {
    tokEl.textContent = tokens.toLocaleString("en-US");
    popNumber(tokEl);
  }

  const totalLines = selected.reduce((n, f) => {
    const l = f.content.split("\n").length - (f.content.endsWith("\n") ? 1 : 0);
    return n + Math.max(1, l);
  }, 0);
  const filesEl = document.getElementById("demoFiles");
  if (filesEl) filesEl.textContent = tf("demo.filesLines", { files: selected.length, lines: totalLines });

  const stateEl = document.getElementById("filterState");
  if (stateEl) {
    stateEl.textContent = preset.include
      ? `\u00B7 --include "${preset.include}"`
      : preset.filterOn
        ? t("demo.filterOn")
        : t("demo.filterOff");
  }

  const warn = document.getElementById("envWarn");
  if (warn) {
    warn.hidden = !selected.some((f) => f.sensitive);
  }
}

export function initDemo(): void {
  applyPreset("default");

  document.querySelectorAll<HTMLButtonElement>(".preset").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".preset").forEach((b) => b.classList.remove("is-active"));
      btn.classList.add("is-active");
      applyPreset(btn.dataset.preset ?? "default");
    });
  });

  document.getElementById("demoCopy")?.addEventListener("click", async () => {
    const ok = await copyText(lastOutput);
    showToast(ok ? tf("toast.copied", { tokens: lastTokenCount }) : "clipboard unavailable");
  });

  // re-render dynamic labels when language changes
  const observer = new MutationObserver(() => render());
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
}

function applyPreset(name: string): void {
  currentPreset = PRESETS[name] ? name : "default";
  const preset = PRESETS[currentPreset];
  checked.clear();
  for (const f of DEMO_FILES) {
    if (passesRules(f, preset) === true) checked.add(f.path);
  }
  render();
}
