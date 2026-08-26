/* hero terminal typewriter with click/key skip support */

const SPINNER_FRAMES = ["\u280B", "\u2819", "\u2839", "\u2838", "\u283C", "\u2834", "\u2826", "\u2827", "\u2807", "\u280F"];
const CMD = "onepaste .";

export function initTypewriter(pageTokens: () => number): void {
  const hero = document.getElementById("hero");
  const cmdEl = document.getElementById("typedCmd");
  const out = document.getElementById("termOut");
  if (!hero || !cmdEl || !out) return;

  const heroEl: HTMLElement = hero;
  const cmdSpan: HTMLElement = cmdEl;
  const lines = Array.from(out.querySelectorAll("p"));
  const statTokens = document.getElementById("statTokens");
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const timers: number[] = [];
  let spinnerTimer: number | undefined;
  let spinnerEl: HTMLSpanElement | undefined;
  let finished = false;

  function clearTimers(): void {
    timers.forEach(clearTimeout);
    if (spinnerTimer !== undefined) clearInterval(spinnerTimer);
    if (spinnerEl) {
      spinnerEl.remove();
      spinnerEl = undefined;
    }
  }

  function finish(): void {
    if (finished) return;
    finished = true;
    clearTimers();
    cmdSpan.textContent = CMD;
    lines.forEach((p) => p.classList.add("is-shown"));
    if (statTokens) statTokens.textContent = pageTokens().toLocaleString("en-US");
    heroEl.classList.remove("anim");
    heroEl.classList.add("is-done");
    document.removeEventListener("click", skip);
    document.removeEventListener("keydown", skip);
  }

  function skip(): void {
    if (!finished) finish();
  }

  // final state without JS motion
  if (reduced) {
    finish();
    return;
  }

  heroEl.classList.add("anim");

  const wait = (ms: number, fn: () => void): void => {
    timers.push(window.setTimeout(fn, ms));
  };

  // reveal output lines progressively while "scanning"
  wait(300, () => lines[0]?.classList.add("is-shown"));
  wait(750, () => lines[1]?.classList.add("is-shown"));
  wait(1500, () => {
    spinnerEl = document.createElement("span");
    spinnerEl.className = "spinner";
    spinnerEl.setAttribute("aria-hidden", "true");
    cmdSpan.parentElement?.appendChild(spinnerEl);
    let f = 0;
    spinnerTimer = window.setInterval(() => {
      if (spinnerEl) {
        spinnerEl.textContent = SPINNER_FRAMES[f++ % SPINNER_FRAMES.length];
      }
    }, 80);
  });
  wait(2600, finish);

  // type command characters on their own timeline
  let i = 0;
  (function type(): void {
    if (finished) return;
    if (i < CMD.length) {
      cmdSpan.textContent += CMD[i++];
      timers.push(window.setTimeout(type, 55 + Math.random() * 65));
    }
  })();

  document.addEventListener("click", skip);
  document.addEventListener("keydown", skip);
}
