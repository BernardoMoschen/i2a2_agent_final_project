# Streamlit Cloud Deployment Guide

## 📦 Deploy Configuration

**Main Application File**: `src/ui/app.py`

## 🚀 Steps to Deploy on Streamlit Cloud

### 1. Push to GitHub
Ensure your code is pushed to GitHub:
```bash
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

### 2. Streamlit Cloud Setup

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Configure:
   - **Repository**: `BernardoMoschen/i2a2_agent_final_project`
   - **Branch**: `main`
   - **Main file path**: `src/ui/app.py` ⬅️ **IMPORTANT**
   - **App URL**: Choose a custom URL (e.g., `fiscal-agent`)

### 3. Environment Variables (Secrets)

Click on "Advanced settings" → "Secrets" and add:

```toml
# .streamlit/secrets.toml (example - DO NOT commit real keys!)

# Optional: Pre-configure Gemini API key
# Users can still input their own key at runtime
GEMINI_API_KEY = "your-api-key-here"

# Database path (will be created in cloud)
DATABASE_PATH = "./fiscal_documents.db"

# Archive directory
ARCHIVE_DIR = "./archives"
```

### 4. Python Version

- **Recommended**: Python 3.11 or 3.12
- The cloud will use your `requirements.txt` automatically

## 📋 Pre-Deployment Checklist

- [x] Main file exists: `src/ui/app.py`
- [x] `requirements.txt` in repository root
- [x] No hardcoded secrets in code
- [x] `.gitignore` excludes sensitive files
- [x] Dependencies are pinned (avoid `latest`)
- [ ] Test locally: `streamlit run src/ui/app.py`

## 🔐 Security Notes

### What to Configure in Streamlit Secrets:

```toml
# Optional: Default Gemini API key (for demos)
GEMINI_API_KEY = "AIza..."

# Database configuration
DATABASE_URL = "sqlite:///fiscal_documents.db"
```

### What Users Configure at Runtime:

- Gemini API Key (via sidebar input)
- Archive Directory
- Database Path

## 🌐 Public URL

After deployment, your app will be available at:
```
https://[your-app-name].streamlit.app
```

Example: `https://fiscal-agent.streamlit.app`

## 🐛 Troubleshooting

### Error: "No module named 'src'"

**Solution**: Ensure you specify the full path `src/ui/app.py`

### Error: "Failed to install requirements"

**Solution**: Check `requirements.txt` for incompatible versions:
```bash
# Test locally first
pip install -r requirements.txt
```

### Database Persistence

**Note**: Streamlit Cloud uses ephemeral storage. Databases are reset on app restart.

**Solutions**:
- Use PostgreSQL (Supabase, ElephantSQL)
- Use SQLite with periodic backups to cloud storage
- Document that it's a demo/POC environment

## 📊 Resource Limits (Free Tier)

- **RAM**: 1 GB
- **CPU**: Shared
- **Storage**: Ephemeral (resets on sleep/restart)
- **Sleep**: After 7 days of inactivity

**Recommendation**: For production, upgrade to Streamlit Cloud Teams or deploy to your own infrastructure.

## 🔄 Continuous Deployment

Every push to `main` branch automatically redeploys the app.

To disable: Settings → Advanced → Uncheck "Auto-rerun on source file changes"

## 📚 Additional Resources

- [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-community-cloud)
- [Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [App Settings](https://docs.streamlit.io/streamlit-community-cloud/manage-your-app)

---

## 🎯 Quick Deploy Command

For local testing before cloud deployment:

```bash
# Run locally
streamlit run src/ui/app.py

# Check it works on http://localhost:8501
```

Then deploy to cloud following steps above.
