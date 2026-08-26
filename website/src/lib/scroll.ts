/* scroll systems: progress bar, line ruler, token counter */

let sectionTokens: HTMLElement[] = [];
let perSection: Map<HTMLElement, number> = new Map();
let revealed = 0;
let totalTokens = 0;
let displayed = 0;
let animating = false;

export function estimateTokens(text: string): number {
  return Math.max(1, Math.ceil(text.length / 4));
}

function countFiles(): number {
  return document.querySelectorAll(".file-section").length + 1; // + manifest
}

function animateCounter(target: number): void {
  if (animating) return;
  animating = true;
  const el = document.getElementById("counterValue");
  if (!el) return;

  const from = displayed;
  const start = performance.now();
  const dur = Math.min(900, 220 + target * 0.4);

  (function tick(now: number): void {
    const p = Math.min(1, (now - start) / dur);
    const eased = 1 - Math.pow(1 - p, 3);
    displayed = Math.round(from + (target - from) * eased);
    el.textContent = displayed.toLocaleString("en-US");
    if (p < 1 && displayed !== target) {
      requestAnimationFrame(tick);
    } else {
      displayed = target;
      el.textContent = target.toLocaleString("en-US");
      animating = false;
    }
  })(start);
}

function onScroll(): void {
  const doc = document.documentElement;
  const max = doc.scrollHeight - innerHeight;
  const p = max > 0 ? Math.min(1, scrollY / max) : 0;

  const bar = document.getElementById("progressBar");
  if (bar) bar.style.width = `${(p * 100).toFixed(2)}%`;

  const ruler = document.getElementById("rulerText");
  if (ruler && totalTokens > 0) {
    const cur = Math.round(p * totalTokens);
    ruler.textContent = `L ${String(cur).padStart(4, "0")} / ${String(totalTokens).padStart(4, "0")}`;
  }
}

/** Recompute page stats (call on load and after language switch). */
export function recomputeStats(): void {
  sectionTokens = Array.from(
    document.querySelectorAll<HTMLElement>(".file-section, .manifest"),
  );
  totalTokens = estimateTokens(document.body.innerText || " ");
  revealed = 0;

  perSection = new Map();
  for (const sec of sectionTokens) {
    const n = estimateTokens(sec.innerText || " ");
    perSection.set(sec, n);
    if (sec.dataset.revealed === "1") revealed += n;
  }

  const filesEl = document.getElementById("pageFiles");
  if (filesEl) filesEl.textContent = String(countFiles());
  const pageTok = document.getElementById("pageTokens");
  if (pageTok) pageTok.textContent = totalTokens.toLocaleString("en-US");

  if (!animating) animateCounter(revealed);

  // hero done-line mirrors the real number
  const statTokens = document.getElementById("statTokens");
  if (statTokens && document.getElementById("hero")?.classList.contains("is-done")) {
    statTokens.textContent = totalTokens.toLocaleString("en-US");
  }

  onScroll();
}

export function initScrollSystems(): void {
  recomputeStats();

  let ticking = false;
  addEventListener(
    "scroll",
    () => {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(() => {
          onScroll();
          ticking = false;
        });
      }
    },
    { passive: true },
  );

  const io = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        const sec = entry.target as HTMLElement;
        if (sec.dataset.revealed === "1") continue;
        sec.dataset.revealed = "1";
        revealed += perSection.get(sec) ?? 0;
        animateCounter(revealed);
      }
    },
    { rootMargin: "0px 0px -8% 0px" },
  );
  sectionTokens.forEach((s) => io.observe(s));
}
