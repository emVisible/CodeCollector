/* easter egg: type "collect" anywhere */

const TARGET = "collect";

export function initEasterEgg(): void {
  let buffer = "";
  let playing = false;

  const overlay = document.getElementById("eggOverlay");
  if (!overlay) return;

  document.addEventListener("keydown", (e: KeyboardEvent) => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.key.length !== 1) return;

    buffer = (buffer + e.key.toLowerCase()).slice(-TARGET.length);
    if (buffer !== TARGET || playing) return;

    buffer = "";
    playing = true;

    // staggered fly-in for every section
    const pieces = document.querySelectorAll<HTMLElement>(
      ".hero, .file-section, .manifest",
    );
    pieces.forEach((el, i) => {
      el.style.animationDelay = `${i * 60}ms`;
    });
    document.body.classList.add("egg-fly");
    overlay.hidden = false;
    requestAnimationFrame(() => overlay.classList.add("is-on"));

    window.setTimeout(() => {
      overlay.classList.remove("is-on");
      document.body.classList.remove("egg-fly");
      pieces.forEach((el) => (el.style.animationDelay = ""));
      window.setTimeout(() => {
        overlay.hidden = true;
        playing = false;
      }, 350);
    }, 1500);
  });
}
