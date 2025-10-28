# Railway Deployment Setup

## Prerequisites
1. Railway account (https://railway.app)
2. GitHub repository connected to Railway
3. OpenAI API key

## Step 1: Create Railway Project

```bash
# Install Railway CLI (optional)
npm install -g @railway/cli

# Login
railway login
```

## Step 2: Create Services

### Backend Service
1. Create new project in Railway dashboard
2. Add service → "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect Dockerfile

### PostgreSQL Database
1. In same project, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway will provision and provide `DATABASE_URL`

## Step 3: Configure Environment Variables

In Railway backend service settings, add:

```
APP_ENV=production
TZ=America/New_York
OPENAI_API_KEY=<your-openai-key>
OPENAI_MODEL=gpt-4-turbo-preview
API_V1_PREFIX=/api/v1
```

**Note:** `DATABASE_URL` is automatically provided by Railway when you link the PostgreSQL service.

## Step 4: Link Database to Backend

1. In backend service settings
2. Go to "Variables" tab
3. Click "Add Reference" → Select PostgreSQL service
4. This automatically adds `DATABASE_URL`

## Step 5: Deploy

### Automatic Deployment
- Push to `main` branch triggers automatic deployment
- Railway runs migrations via `alembic upgrade head` in start command
- Health check at `/health` endpoint

### Manual Deployment
```bash
railway up
```

## Step 6: Verify Deployment

1. Check Railway logs for successful startup
2. Visit the provided Railway URL + `/health`
3. Should return: `{"status": "healthy", ...}`
4. Visit `/docs` for API documentation

## Environment URLs

- **Production API**: `https://<your-service>.railway.app`
- **Health Check**: `https://<your-service>.railway.app/health`
- **API Docs**: `https://<your-service>.railway.app/docs`

## Monitoring

Railway provides:
- Real-time logs
- Metrics (CPU, memory, network)
- Deployment history
- Automatic SSL certificates

## Troubleshooting

### Database Connection Issues
- Verify `DATABASE_URL` is set correctly
- Check PostgreSQL service is running
- Ensure services are in same project

### Migration Failures
- Check Alembic migrations in logs
- Manually run: `railway run alembic upgrade head`
- Verify database schema

### Port Binding
- Railway automatically sets `$PORT` variable
- Ensure app binds to `0.0.0.0:$PORT`
- Default is 8000 if not set

## Scaling (Future)

Railway supports:
- Horizontal scaling (multiple instances)
- Vertical scaling (more CPU/RAM)
- Custom domains
- Private networking

## Cost Estimation

**Free Tier:**
- $5 credit/month
- Suitable for development/testing

**Pro Plan:**
- $20/month base
- Pay for usage
- Suitable for production MVP

## Backup Strategy

1. Railway provides automatic PostgreSQL backups
2. Export data via pg_dump for additional safety:
```bash
railway run pg_dump $DATABASE_URL > backup.sql
```
