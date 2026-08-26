/* install section: method tabs + copy */

import { copyText, showToast } from "./copy";
import { t, tf } from "./i18n";

interface Method {
  cmd: string;
  capKey: string;
}

const METHODS: Record<string, Method> = {
  pipx: { cmd: "pipx install onepaste", capKey: "cap.pipx" },
  tokens: { cmd: 'pipx install "onepaste[tokens]"', capKey: "cap.tokens" },
  source: {
    cmd: "git clone https://github.com/emVisible/onepaste\ncd onepaste\npipx install -e .",
    capKey: "cap.source",
  },
};

let current = "pipx";

function apply(name: string): void {
  current = METHODS[name] ? name : "pipx";
  const method = METHODS[current];

  document.querySelectorAll<HTMLButtonElement>(".tab").forEach((b) => {
    const active = b.dataset.tab === current;
    b.classList.toggle("is-active", active);
    b.setAttribute("aria-selected", String(active));
  });

  const caption = document.getElementById("tabCaption");
  if (caption) caption.textContent = t(method.capKey);

  const cmdCode = document.querySelector("#installCmd code");
  if (cmdCode) cmdCode.textContent = method.cmd;
}

export function refreshInstallLabels(): void {
  apply(current);
}

export function initInstall(): void {
  apply("pipx");

  document.querySelectorAll<HTMLButtonElement>(".tab").forEach((btn) => {
    btn.addEventListener("click", () => apply(btn.dataset.tab ?? "pipx"));
  });

  document.getElementById("installCopy")?.addEventListener("click", async () => {
    const cmd = METHODS[current].cmd;
    const ok = await copyText(cmd);
    showToast(ok ? tf("toast.copied", { tokens: Math.ceil(cmd.length / 4) }) : "clipboard unavailable");
  });
}
