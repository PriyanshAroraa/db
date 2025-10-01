# 🚀 Streamlit Cloud Deployment Guide

## 📋 Prerequisites

1. **GitHub Account**: Sign up at [github.com](https://github.com)
2. **Streamlit Cloud Account**: Sign up at [share.streamlit.io](https://share.streamlit.io)
3. **Git Repository**: Push your code to GitHub

## 🔧 Deployment Steps

### Step 1: Push to GitHub

```bash
# Add your GitHub remote (replace with your actual repo)
git remote add origin https://github.com/yourusername/bot-dashboard.git

# Push to GitHub
git push -u origin master
```

### Step 2: Deploy to Streamlit Cloud

1. **Go to**: [share.streamlit.io](https://share.streamlit.io)
2. **Sign in** with your GitHub account
3. **Click "New app"**
4. **Select your repository**: `yourusername/bot-dashboard`
5. **Choose branch**: `master`
6. **Main file path**: `static_dashboard.py`
7. **Click "Deploy!"**

### Step 3: Configure Secrets

In Streamlit Cloud, add your environment variables:

1. **Go to app settings**
2. **Click "Secrets"**
3. **Add your environment variables**:

```toml
[secrets]
DB_USER = "customer_services"
DB_PASS = "your_password"
DB_HOST = "mysql-analytics-warehouse.cqiyzuvvkkfc.us-east-1.rds.amazonaws.com"
DB_PORT = "3306"
DB_NAME = "analytics_db"
BOT_USER_IDS = "10111491,10211493,10411491,10711491,11011491"
```

## 🌐 Access Your Dashboard

Your dashboard will be available at:
- `https://your-app-name.streamlit.app`

## 🔄 Updating Your Dashboard

1. **Update data locally**: `python manual_report_updater.py`
2. **Commit changes**: `git add . && git commit -m "Update data"`
3. **Push to GitHub**: `git push`
4. **Streamlit auto-deploys** the changes

---

**This is the easiest way to deploy your Python Streamlit dashboard!**
