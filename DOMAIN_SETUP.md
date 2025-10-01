# 🌐 Custom Domain Setup for bot-analytics.vercel.app

## 📋 To Set Up Custom Domain

### **Option 1: Via Vercel CLI (Recommended)**
```bash
# Add the custom domain
vercel domains add bot-analytics.vercel.app

# Or set it directly in the project
vercel domains add bot-analytics.vercel.app --project db
```

### **Option 2: Via Vercel Dashboard**
1. Go to: https://vercel.com/dashboard
2. Select your project: `db`
3. Go to **Settings** → **Domains**
4. Add domain: `bot-analytics.vercel.app`
5. Click **Add**

### **Option 3: Via Project Settings**
1. Go to your project settings
2. Navigate to **Domains** section
3. Add `bot-analytics.vercel.app`
4. Save changes

---

## 🚀 **After Domain Setup**

The dashboard will be available at:
**https://bot-analytics.vercel.app**

---

## 📝 **Note**
- Vercel automatically provides SSL certificates
- The domain will work immediately after adding
- No DNS configuration needed for .vercel.app subdomains
