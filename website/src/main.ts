import "./styles/tokens.css";
import "./styles/base.css";
import "./styles/components.css";
import "./styles/sections.css";

import { initI18n, onLangChange } from "./lib/i18n";
import { initTheme } from "./lib/theme";
import { initTypewriter } from "./lib/typewriter";
import { initScrollSystems, recomputeStats } from "./lib/scroll";
import { initNav } from "./lib/nav";
import { initEasterEgg } from "./lib/easteregg";
import { initDemo } from "./lib/demo";
import { initInstall, refreshInstallLabels } from "./lib/install";

function pageTokenTarget(): number {
  const el = document.getElementById("pageTokens");
  return el ? Number(el.textContent.replace(/,/g, "")) || 0 : 0;
}

function fillGeneratedStamp(): void {
  const el = document.getElementById("metaGenerated");
  if (!el) return;
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  el.textContent = `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}

initTheme();
initI18n();
fillGeneratedStamp();

// typewriter needs the final token number; compute stats first
initScrollSystems();
initTypewriter(pageTokenTarget);

initNav();
initDemo();
initInstall();
initEasterEgg();

// diff lines sweep themselves once when the section scrolls into view
(function initDiffSweep(): void {
  const block = document.getElementById("changelog");
  if (!block) return;
  const rows = block.querySelectorAll(".add");
  const io = new IntersectionObserver(
    (entries) => {
      if (entries.some((e) => e.isIntersecting)) {
        rows.forEach((row, i) => {
          window.setTimeout(() => row.classList.add("is-swept"), i * 130);
        });
        io.disconnect();
      }
    },
    { threshold: 0.35 },
  );
  io.observe(block);
})();

// language switch changes every string → re-weigh the page
onLangChange(() => {
  recomputeStats();
  refreshInstallLabels();
});
