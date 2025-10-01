# 🚂 Railway Deployment Guide

## 📋 Prerequisites

1. **GitHub Account**: [github.com](https://github.com)
2. **Railway Account**: [railway.app](https://railway.app)

## 🔧 Deployment Steps

### Step 1: Push to GitHub

```bash
# Add your GitHub remote
git remote add origin https://github.com/yourusername/bot-dashboard.git
git push -u origin master
```

### Step 2: Deploy to Railway

1. **Go to**: [railway.app](https://railway.app)
2. **Sign in** with GitHub
3. **Click "New Project"**
4. **Select "Deploy from GitHub repo"**
5. **Choose your repository**
6. **Railway auto-detects Python and deploys**

### Step 3: Configure Environment Variables

In Railway dashboard:
1. **Go to your project**
2. **Click "Variables" tab**
3. **Add your environment variables**:

```
DB_USER=customer_services
DB_PASS=your_password
DB_HOST=mysql-analytics-warehouse.cqiyzuvvkkfc.us-east-1.rds.amazonaws.com
DB_PORT=3306
DB_NAME=analytics_db
BOT_USER_IDS=10111491,10211493,10411491,10711491,11011491
```

## 🌐 Access Your Dashboard

Railway provides a URL like:
- `https://your-app-name.up.railway.app`

---

**Railway is excellent for Python apps with databases!**
