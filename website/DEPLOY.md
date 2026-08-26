# OnePaste Website

The marketing site — itself styled as a `onepaste` output. Static, zero runtime
dependencies, bilingual (EN/中文), dual theme (paper/dark).

## Develop

```bash
cd website
npm install
npm run dev        # http://localhost:5173
```

## Build & preview

```bash
npm run build      # type-checks, outputs dist/
npm run preview
```

## Deploy to Vercel

1. Import the `emVisible/onepaste` repo into Vercel.
2. Set **Root Directory** to `website` (Framework preset auto-detects Vite).
3. Deploy — output is `dist/`, no other configuration needed.

Everything runs client-side; no env vars are required.
