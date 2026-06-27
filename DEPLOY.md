# Deploying CV Analyzer (free tier)

Two pieces: **backend → Render**, **frontend → Vercel**. ~10 minutes. The app works
even without an OpenAI key (deterministic/mock mode), so the public demo is functional
and exposes no secrets.

> Repo layout note: the app lives in the `CV/` subfolder — `CV/backend` (FastAPI) and
> `CV/frontend` (Next.js). The settings below point each platform at the right subfolder.

---

## 1. Backend → Render

1. Go to <https://dashboard.render.com> → sign in with GitHub.
2. **New + → Blueprint** → pick the `cv-analyzer` repo. Render auto-detects [`render.yaml`](./render.yaml).
3. It will create a web service `cv-analyzer-api` with root dir `CV/backend`. Click **Apply**.
4. When prompted for env vars:
   - `ALLOWED_ORIGINS` → leave blank for now (you'll set it in step 3 once you have the Vercel URL).
   - `OPENAI_API_KEY` → **optional**. Leave blank to run in mock mode, or paste a key for real GPT analysis.
5. Wait for the first deploy (~3–5 min). Note the URL, e.g. `https://cv-analyzer-api.onrender.com`.
6. Test it: open `https://<your-api>.onrender.com/health` → should return `{"status":"ok"}`.

> Free tier sleeps after ~15 min idle; the first request then takes ~50s to wake. Fine for a demo.

## 2. Frontend → Vercel

1. Go to <https://vercel.com/new> → sign in with GitHub → import the `cv-analyzer` repo.
2. **Root Directory** → set to `CV/frontend` (click *Edit* next to root directory).
3. Framework preset: **Next.js** (auto-detected). Build/Output: defaults are fine.
4. **Environment Variables** → add:
   - `NEXT_PUBLIC_API_BASE_URL` = your Render URL from step 1 (e.g. `https://cv-analyzer-api.onrender.com`)
5. Click **Deploy**. Note the URL, e.g. `https://cv-analyzer.vercel.app`.

## 3. Connect them (CORS)

1. Back in Render → `cv-analyzer-api` → **Environment** → set:
   - `ALLOWED_ORIGINS` = your Vercel URL (e.g. `https://cv-analyzer.vercel.app`)
2. Save → Render redeploys automatically. Done.

## 4. Put the live URL in the README

Replace the `Live demo` line at the top of [`README.md`](./README.md) with your Vercel URL.

---

### Checklist
- [ ] Render backend deployed, `/health` returns ok
- [ ] Vercel frontend deployed with `NEXT_PUBLIC_API_BASE_URL` set
- [ ] `ALLOWED_ORIGINS` on Render set to the Vercel URL
- [ ] README live-demo link updated
