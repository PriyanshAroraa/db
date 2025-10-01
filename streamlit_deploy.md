# 🚀 Deploy to Streamlit Cloud

## Quick Deploy to Streamlit Cloud

### Step 1: Push to GitHub
```bash
# Create GitHub repository
# Push your code
git remote add origin https://github.com/yourusername/bot-dashboard.git
git push -u origin master
```

### Step 2: Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Main file path: `static_dashboard.py`
6. Deploy!

### Step 3: Environment Variables
In Streamlit Cloud dashboard, add:
- `DB_USER`
- `DB_PASS` 
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `BOT_USER_IDS`

## Advantages:
- ✅ Free hosting
- ✅ Built for Streamlit
- ✅ Easy environment variables
- ✅ Automatic deployments
