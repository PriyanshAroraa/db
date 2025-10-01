# 🚀 Vercel Deployment Guide

## 📋 Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI**: Install with `npm i -g vercel`
3. **Git Repository**: Push your code to GitHub

## 🔧 Deployment Steps

### Step 1: Prepare Your Environment Variables

You need to set up your database credentials as Vercel environment variables:

```bash
# Using Vercel CLI
vercel env add DB_USER
vercel env add DB_PASS
vercel env add DB_HOST
vercel env add DB_PORT
vercel env add DB_NAME
```

**Or via Vercel Dashboard:**
1. Go to your project settings
2. Navigate to "Environment Variables"
3. Add each variable with your actual values

### Step 2: Deploy to Vercel

```bash
# Login to Vercel
vercel login

# Deploy from your project directory
vercel

# For production deployment
vercel --prod
```

### Step 3: Configure Database Access

⚠️ **IMPORTANT**: Your database needs to allow connections from Vercel's IP ranges. You may need to:

1. **Whitelist Vercel IPs** in your database security settings
2. **Use a connection pooler** like PlanetScale or Supabase for better reliability
3. **Consider using environment-specific credentials**

## 🌐 Access Your Dashboard

Once deployed, your dashboard will be available at:
- **Your Vercel URL**: `https://your-project.vercel.app`
- **API Endpoint**: `https://your-project.vercel.app/api/bot-data`

## 🔒 Security Considerations

### Database Security
- ✅ Use environment variables for credentials
- ✅ Restrict database access to Vercel IPs only
- ✅ Consider using read-only database user
- ✅ Enable SSL/TLS connections

### Dashboard Security
- ✅ Add authentication if needed
- ✅ Implement rate limiting
- ✅ Use HTTPS only
- ✅ Consider IP whitelisting for internal use

## 📊 Features Included

Your Vercel-hosted dashboard includes:

- ✅ **Real-time Metrics**: Total P&L, races, balances
- ✅ **Interactive Charts**: Performance comparison, trends
- ✅ **Auto-refresh**: Updates every 5 minutes
- ✅ **Responsive Design**: Works on all devices
- ✅ **Export Functionality**: Download data as needed
- ✅ **Error Handling**: Graceful failure management

## 🔄 Updating the Dashboard

To update your dashboard:

```bash
# Make changes to your code
git add .
git commit -m "Update dashboard"
git push

# Redeploy
vercel --prod
```

## 🆘 Troubleshooting

### Common Issues:

1. **Database Connection Failed**
   - Check environment variables
   - Verify IP whitelisting
   - Test database connectivity

2. **API Timeout**
   - Vercel has 10-second timeout for hobby plans
   - Consider optimizing queries
   - Use connection pooling

3. **CORS Errors**
   - Check API endpoint configuration
   - Verify headers in `api/bot-data.py`

## 💡 Alternative Hosting Options

If Vercel doesn't work for your setup:

1. **Railway**: Better for database connections
2. **Render**: Good for full-stack apps
3. **DigitalOcean App Platform**: More control
4. **AWS Amplify**: Enterprise-grade hosting

## 📞 Support

If you encounter issues:
1. Check Vercel deployment logs
2. Test API endpoint directly
3. Verify database connectivity
4. Check environment variables

---

**Your dashboard is now ready for production deployment!** 🎉
