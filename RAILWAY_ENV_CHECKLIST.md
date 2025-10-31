# Railway Environment Variables Checklist

Use this checklist when setting up your Railway backend service.

---

## Required Environment Variables

### ✅ Automatically Provided by Railway

- **`DATABASE_URL`**  
  - **Source:** Linked PostgreSQL service  
  - **Action:** Link the PostgreSQL database to your backend service in Railway dashboard  
  - **Format:** `postgresql://user:password@host:port/database`  
  - **Verification:** Check Variables tab shows `DATABASE_URL` with a reference icon

- **`PORT`**  
  - **Source:** Railway platform (automatically set)  
  - **Action:** None required  
  - **Default:** Usually 8000  
  - **Note:** The `railway.toml` startCommand uses `$PORT` correctly

---

## ✅ Must Set Manually in Railway

Add these in: **Backend Service → Settings → Variables**

### 1. `APP_ENV`
- **Value:** `production`
- **Purpose:** Tells the app it's running in production mode
- **Required:** Yes

### 2. `TZ`
- **Value:** `America/New_York`
- **Purpose:** Sets timezone for EST calculations (per PRD requirement)
- **Required:** Yes

### 3. `OPENAI_API_KEY`
- **Value:** `sk-...` (your OpenAI API key)
- **Purpose:** AI Coach feature (Epic E)
- **Required:** Yes (you mentioned this is already available)
- **Security:** Never commit this to Git

### 4. `OPENAI_MODEL`
- **Value:** `gpt-4-turbo-preview`
- **Purpose:** Specifies which OpenAI model to use
- **Required:** No (defaults to this value in code)
- **Note:** Can override if you want to use a different model

### 5. `API_V1_PREFIX`
- **Value:** `/api/v1`
- **Purpose:** API route prefix
- **Required:** No (defaults to this value in code)
- **Note:** Only set if you want a different prefix

---

## Verification Steps

After setting all variables:

1. **Check Variables Tab**
   ```
   ✓ DATABASE_URL (reference from PostgreSQL)
   ✓ APP_ENV = production
   ✓ TZ = America/New_York
   ✓ OPENAI_API_KEY = sk-... (hidden)
   ✓ OPENAI_MODEL = gpt-4-turbo-preview (optional)
   ✓ API_V1_PREFIX = /api/v1 (optional)
   ```

2. **Deploy and Check Logs**
   - Look for successful database connection
   - Verify Alembic migrations run without errors
   - Confirm Uvicorn starts on correct port

3. **Test Health Endpoint**
   ```bash
   curl https://your-service.up.railway.app/health
   ```
   Should return:
   ```json
   {
     "status": "healthy",
     "service": "trading-dashboard-api",
     "version": "0.1.0"
   }
   ```

---

## GitHub Secrets (Separate from Railway)

For GitHub Actions auto-deploy, add to: **GitHub Repo → Settings → Secrets and variables → Actions**

### `RAILWAY_TOKEN`
- **Value:** Token generated from Railway dashboard (Account Settings → Tokens)
- **Purpose:** Allows GitHub Actions to deploy to Railway
- **Required:** Yes (for auto-deploy on push to main)
- **Note:** This is NOT set in Railway - it's set in GitHub

---

## Environment Variable Reference

| Variable | Required | Set Where | Default | Notes |
|----------|----------|-----------|---------|-------|
| `DATABASE_URL` | Yes | Railway (auto) | - | Linked from PostgreSQL service |
| `PORT` | Yes | Railway (auto) | 8000 | Set by Railway platform |
| `APP_ENV` | Yes | Railway (manual) | - | Must be `production` |
| `TZ` | Yes | Railway (manual) | - | Must be `America/New_York` |
| `OPENAI_API_KEY` | Yes | Railway (manual) | - | Your OpenAI API key |
| `OPENAI_MODEL` | No | Railway (manual) | `gpt-4-turbo-preview` | Optional override |
| `API_V1_PREFIX` | No | Railway (manual) | `/api/v1` | Optional override |
| `RAILWAY_TOKEN` | Yes | GitHub Secrets | - | For CI/CD only |

---

## Quick Copy-Paste (for Railway Variables)

```
APP_ENV=production
TZ=America/New_York
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo-preview
API_V1_PREFIX=/api/v1
```

**Remember:** Replace `sk-your-key-here` with your actual OpenAI API key.

---

## Troubleshooting

**Issue:** `DATABASE_URL` not found
- **Fix:** Ensure PostgreSQL service is created and linked to backend service

**Issue:** Timezone errors or incorrect date calculations
- **Fix:** Verify `TZ=America/New_York` is set exactly as shown

**Issue:** OpenAI API errors
- **Fix:** Check `OPENAI_API_KEY` is valid and has credits
- **Fix:** Verify no extra spaces or quotes around the key value

**Issue:** Port binding errors
- **Fix:** Ensure `railway.toml` uses `$PORT` (not hardcoded 8000)
- **Fix:** Verify Dockerfile doesn't override the startCommand

---

## Next Steps After Setting Variables

1. ✅ All variables set in Railway
2. ✅ PostgreSQL linked to backend
3. ✅ `RAILWAY_TOKEN` added to GitHub Secrets
4. 🚀 Deploy via Railway dashboard or push to `main`
5. ✅ Verify health endpoint responds
6. ✅ Check logs for successful startup
7. 📝 Update `.github/workflows/deploy.yml` with your Railway URL

---

## Security Best Practices

- ✅ Never commit `.env` files to Git
- ✅ Use Railway's variable management (encrypted at rest)
- ✅ Rotate `OPENAI_API_KEY` periodically
- ✅ Use Railway's built-in secrets for sensitive values
- ✅ Keep `RAILWAY_TOKEN` secure in GitHub Secrets only
- ✅ Review Railway access logs regularly
