# Railway Deployment Guide - Trading Dashboard MVP

**Status:** Ready to deploy from GitHub  
**Prerequisites:** GitHub repo pushed, Railway account created, OpenAI API key available

---

## Step 1: Connect GitHub to Railway

1. **Log into Railway** at https://railway.app
2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Authorize Railway to access your GitHub account if needed
   - Select your repository: `windsurf-project` (or your repo name)

3. **Railway Auto-Detection**
   - Railway will detect the `railway.toml` and `Dockerfile` automatically
   - It will use the configuration from `railway.toml` for build settings

---

## Step 2: Add PostgreSQL Database

1. **In the same Railway project**, click "+ New"
2. Select "Database" → "PostgreSQL"
3. Railway provisions the database and generates `DATABASE_URL` automatically
4. **No manual configuration needed** - Railway handles the connection string

---

## Step 3: Link Database to Backend Service

1. Go to your **backend service** settings
2. Click the "Variables" tab
3. Click "Add Reference" or "Link Database"
4. Select the PostgreSQL service you just created
5. Railway automatically injects `DATABASE_URL` into your backend environment

---

## Step 4: Configure Environment Variables

In your **backend service** → Variables tab, add these:

```
APP_ENV=production
TZ=America/New_York
OPENAI_API_KEY=<your-openai-key-here>
OPENAI_MODEL=gpt-4-turbo-preview
API_V1_PREFIX=/api/v1
```

**Note:** `DATABASE_URL` is already set from Step 3 (linked reference).

---

## Step 5: Verify Build Configuration

Railway will use these files automatically:

- **`railway.toml`** - Defines build and deploy commands
- **`apps/backend/Dockerfile`** - Container build instructions
- **`apps/backend/alembic/`** - Database migrations (run automatically on startup)

The start command in `railway.toml` runs:
```bash
cd apps/backend && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

This ensures migrations run before the API starts.

---

## Step 6: Deploy

### Option A: Manual Deploy (First Time)
1. In Railway dashboard, click "Deploy" on your backend service
2. Watch the build logs in real-time
3. Wait for "Deployment successful" message

### Option B: Automatic Deploy (After GitHub Actions Setup)
- Push to `main` branch triggers automatic deployment via GitHub Actions
- See Step 8 for GitHub Actions configuration

---

## Step 7: Verify Deployment

1. **Get your Railway URL**
   - In the backend service, go to "Settings" → "Domains"
   - Railway provides a URL like: `https://your-service.up.railway.app`

2. **Test Health Endpoint**
   ```bash
   curl https://your-service.up.railway.app/health
   ```
   Expected response:
   ```json
   {
     "status": "healthy",
     "service": "trading-dashboard-api",
     "version": "0.1.0"
   }
   ```

3. **Check API Documentation**
   - Visit: `https://your-service.up.railway.app/docs`
   - FastAPI auto-generated docs should load

4. **Review Logs**
   - In Railway dashboard, click "Logs" to see:
     - Alembic migration output
     - Uvicorn startup messages
     - Any errors or warnings

---

## Step 8: Setup GitHub Actions Auto-Deploy

1. **Generate Railway Token**
   - In Railway dashboard, go to Account Settings → Tokens
   - Click "Create Token"
   - Copy the token (you'll only see it once)

2. **Add Token to GitHub Secrets**
   - Go to your GitHub repo → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `RAILWAY_TOKEN`
   - Value: paste the token from step 1
   - Click "Add secret"

3. **Update GitHub Actions Workflow**
   - Edit `.github/workflows/deploy.yml`
   - Replace the health check URL placeholder with your actual Railway URL:
   ```yaml
   - name: Health Check
     run: |
       echo "Waiting for deployment to be ready..."
       sleep 30
       curl -f https://your-service.up.railway.app/health || exit 1
   ```

4. **Test Auto-Deploy**
   - Make a small commit and push to `main`
   - Go to GitHub → Actions tab
   - Watch the "Deploy to Railway" workflow run
   - Verify it completes successfully

---

## Step 9: Monitor & Troubleshoot

### Common Issues

**Issue: Database connection failed**
- Verify PostgreSQL service is running in Railway
- Check `DATABASE_URL` is linked correctly in Variables tab
- Review logs for connection errors

**Issue: Migration errors**
- Check Alembic migration files are committed to Git
- Manually run migrations: `railway run alembic upgrade head`
- Verify database schema matches migration expectations

**Issue: Port binding errors**
- Railway sets `$PORT` automatically (usually 8000)
- Ensure Uvicorn binds to `0.0.0.0:$PORT`
- Check `railway.toml` start command is correct

**Issue: OpenAI API errors**
- Verify `OPENAI_API_KEY` is set correctly
- Check API key has sufficient credits/quota
- Review logs for specific OpenAI error messages

### Viewing Logs
```bash
# Install Railway CLI (optional)
npm install -g @railway/cli

# Login
railway login

# View logs
railway logs
```

---

## Step 10: Next Steps (Per PRD)

Once deployed and verified:

✅ **Epic A Complete** - Foundations deployed to Railway  
⬜ **Epic B** - Implement CSV ingest & validation  
⬜ **Epic C** - Build FIFO engine & metrics  
⬜ **Epic D** - Create dashboard UI with animations  
⬜ **Epic E** - Add AI coach integration  
⬜ **Epic F** - Creator demo & documentation  

---

## Quick Reference

| Resource | URL/Command |
|----------|-------------|
| Railway Dashboard | https://railway.app/dashboard |
| Health Check | `https://your-service.up.railway.app/health` |
| API Docs | `https://your-service.up.railway.app/docs` |
| View Logs | Railway dashboard → Service → Logs |
| Manual Deploy | `railway up` (via CLI) |
| Run Migrations | `railway run alembic upgrade head` |

---

## Cost Estimate

**Railway Pricing:**
- **Hobby Plan:** $5/month (500 hours execution time)
- **Pro Plan:** $20/month + usage-based pricing
- **Database:** ~$5-10/month for PostgreSQL

**Estimated MVP Cost:** $10-15/month (Hobby tier sufficient for development)

---

## Support & Documentation

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- PRD Reference: `LLM_PLAN/Product_Requirement_Document.md`
- Setup Details: `infra/railway-setup.md`
