/* the miniature repo used by the live demo */

export interface DemoFile {
  path: string;
  lang: string;
  content: string;
  binary?: boolean;
  sensitive?: boolean;
}

export const GITIGNORE_PATTERNS = [".env", "assets/"];
export const WHITELIST_EXTS = [".ts", ".md"];

export const DEMO_FILES: DemoFile[] = [
  {
    path: "README.md",
    lang: "md",
    content: "# mini-repo\n\nA tiny sample project used by this demo.\n",
  },
  {
    path: "src/main.ts",
    lang: "ts",
    content: 'import { greet } from "./utils";\n\nconsole.log(greet("world"));\n',
  },
  {
    path: "src/utils.ts",
    lang: "ts",
    content:
      'export function greet(name: string): string {\n  return `hello, ${name}!`;\n}\n',
  },
  {
    path: "tests/main.test.ts",
    lang: "ts",
    content:
      'import { greet } from "../src/utils";\n\nit("greets", () => {\n  expect(greet("x")).toBe("hello, x!");\n});\n',
  },
  {
    path: "docs/notes.md",
    lang: "md",
    content: "# Notes\n\n```\na fenced block inside a file\n```\n",
  },
  {
    path: ".env",
    lang: "text",
    content: "SECRET_KEY=do-not-ship-me\n",
    sensitive: true,
  },
  {
    path: "assets/logo.bin",
    lang: "",
    content: "\u0000\u0001\u0002PNG-fake-bytes",
    binary: true,
  },
];
