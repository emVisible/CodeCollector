export const en = {
  "meta.title": "OnePaste — Your codebase. One paste.",

  "hero.hint": "\u25BC you are reading the output",

  "sum.headline": "Your whole codebase.<br />One&nbsp;paste.",
  "sum.sub":
    "OnePaste packs any directory into a single Markdown file your LLM can actually read. No account. No upload. It never leaves your machine.",
  "sum.telemetry": "none. it can't phone home.",

  "how.c1": "# 1. point it at a folder",
  "how.c2": "# 2. press Enter \u2014 files are weighed in tokens,",
  "how.c3": "#    gitignored junk stays out, big outputs split",
  "how.c4": "# 3. paste one file into any LLM",

  "demo.liveTag": "live \u2014 runs in your browser",
  "demo.blurb":
    "A miniature repo, the real formatting rules. Toggle files, watch tokens move, copy the result.",
  "demo.envWarn": ".env looks sensitive \u2014 usually kept out",
  "demo.tokUnit": "tok",
  "demo.copy": "Copy output",
  "demo.filterOn": "\u00B7 .gitignore on",
  "demo.filterOff": "\u00B7 .gitignore off",
  "demo.filesLines": "{files} files \u00B7 {lines} lines",
  "toast.copied": "Copied \u00B7 {tokens} tokens",

  "diff.l1": ".gitignore filtering defaults ON inside git repos",
  "diff.l2": "--stdout pipes straight into other tools",
  "diff.l3": "exact token counting (tiktoken) with estimate fallback",
  "diff.l4": "--include / --exclude-pattern glob filters",
  "diff.l5": "code fences auto-lengthen around nested backticks",
  "diff.l6": "now on PyPI \u2014 pipx install onepaste",

  "common.copy": "Copy",

  "cap.pipx": "Recommended \u2014 isolated CLI install",
  "cap.tokens": "Adds exact token counting via tiktoken",
  "cap.source": "Development checkout",

  "install.note": "Local-only by design: nothing is uploaded, ever.",

  "footer.colophon":
    "This website is itself a onepaste output \u2014 hand-built, static, zero runtime libraries.",

  "egg.msg": "collected.",

  "aria.theme": "Toggle dark mode",
} as const;

export type Dict = Record<keyof typeof en | string, string>;
