# 🚀 Deployment Guide: Render (Backend) + Vercel (Frontend)

This guide walks you through deploying the **Enterprise AI Knowledge Assistant** to production with complete security and zero hardcoded secrets.

---

## 🔒 Step 0: Security & Secrets Audit
All secret keys and credentials have been removed from source files and template files.
- `.env` files are in `.gitignore` and will never be committed to Git.
- Real API keys and JWT secrets are injected **only** through Render & Vercel environment dashboards.

---

## 🖥️ Part 1: Deploy Backend to Render

### 1. Create a Web Service on Render
1. Push your project to a GitHub / GitLab repository.
2. Log in to [Render Dashboard](https://dashboard.render.com).
3. Click **New +** → **Web Service**.
4. Connect your GitHub repository.

### 2. Configure Service Settings
- **Name**: `enterprise-rag-backend` (or your choice)
- **Root Directory**: `backend`
- **Environment / Runtime**: `Python 3`
- **Build Command**: 
  ```bash
  pip install --upgrade pip && pip install -r requirements.txt
  ```
- **Start Command**: 
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```

### 3. Add Environment Variables on Render
Under **Environment Variables** in Render, add the following:

| Key | Value | Description |
|---|---|---|
| `PYTHON_VERSION` | `3.11.8` | Recommended Python runtime |
| `APP_NAME` | `Enterprise AI Knowledge Assistant` | Application display name |
| `APP_ENV` | `production` | Production environment flag |
| `DATABASE_URL` | `sqlite:///enterprise_rag.db` | Or your Render PostgreSQL URL |
| `SECRET_KEY` | *(Click 'Generate' or enter 32+ hex chars)* | App encryption secret |
| `JWT_SECRET` | *(Click 'Generate' or enter 32+ hex chars)* | JWT signing secret |
| `JWT_ALGORITHM` | `HS256` | Token algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token lifespan |
| `CORS_ORIGINS` | `https://your-app.vercel.app` | **Your Vercel URL (update after Part 2)** |
| `LLM_PROVIDER` | `openai` | OpenAI-compatible endpoint |
| `LLM_API_KEY` | `sk-or-v1-...` | Your actual OpenRouter API key |
| `LLM_API_BASE` | `https://openrouter.ai/api/v1` | OpenRouter endpoint |
| `LLM_MODEL` | `liquid/lfm-2.5-2.6b:free` | Selected model |
| `EMBEDDING_PROVIDER` | `mock` | Local embedding provider |
| `RERANK_PROVIDER` | `mock` | Local reranker |
| `STORAGE_PROVIDER` | `local` | Local file storage for uploads |
| `STORAGE_BUCKET` | `enterprise-rag-docs` | Storage bucket folder |
| `CHUNK_SIZE` | `800` | Chunk size |
| `CHUNK_OVERLAP` | `150` | Chunk overlap |
| `MAX_UPLOAD_SIZE_MB` | `10` | Max file upload limit |
| `ALLOWED_EXTENSIONS` | `pdf,docx,txt,md` | Allowed file formats |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | `60` | API rate limit |

4. Click **Deploy Web Service**.
5. Copy your Render Backend URL once deployed (e.g. `https://enterprise-rag-backend.onrender.com`).

---

## 🌐 Part 2: Deploy Frontend to Vercel

### 1. Import Project on Vercel
1. Log in to [Vercel Dashboard](https://vercel.com).
2. Click **Add New...** → **Project**.
3. Import your GitHub repository.

### 2. Configure Framework & Root Directory
- **Framework Preset**: `Next.js`
- **Root Directory**: Click **Edit** and choose `frontend`.

### 3. Add Environment Variable on Vercel
Under **Environment Variables**, add:

| Key | Value |
|---|---|
| `NEXT_PUBLIC_BACKEND_URL` | `https://enterprise-rag-backend.onrender.com` *(Your Render Backend URL from Part 1)* |

4. Click **Deploy**.

---

## 🔗 Part 3: Link Backend CORS to Frontend
Once Vercel finishes deploying, copy your production frontend URL (e.g., `https://enterprise-rag-frontend.vercel.app`):

1. Go back to your **Render Dashboard** → `enterprise-rag-backend` → **Environment**.
2. Update `CORS_ORIGINS`:
   ```env
   CORS_ORIGINS=https://enterprise-rag-frontend.vercel.app
   ```
3. Render will automatically re-deploy with CORS locked to your Vercel frontend.

---

## ✅ Part 4: Verification Checklist

1. Open your Vercel URL in browser (e.g. `https://enterprise-rag-frontend.vercel.app`).
2. Register a new account (`/register`).
3. Log in (`/login`) and check the Dashboard (`/dashboard`).
4. Upload a test policy or handbook PDF (`/documents`).
5. Open `/chat` and ask a question about your uploaded document.
6. Verify live streaming tokens and verifiable citation sources!
