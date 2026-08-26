/* directory-tree nav highlighting */

const SECTION_IDS = ["summary", "how", "demo", "changelog", "install"];

export function initNav(): void {
  const links = new Map<string, HTMLAnchorElement>();
  document.querySelectorAll<HTMLAnchorElement>("#treeNav a").forEach((a) => {
    const id = a.getAttribute("href")?.slice(1);
    if (id) links.set(id, a);
  });

  function setActive(id: string | null): void {
    links.forEach((a, key) => a.classList.toggle("is-active", key === id));
  }

  const io = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          setActive((entry.target as HTMLElement).id);
        }
      }
    },
    { rootMargin: "-30% 0px -60% 0px" },
  );

  SECTION_IDS.forEach((id) => {
    const el = document.getElementById(id);
    if (el) io.observe(el);
  });
}
