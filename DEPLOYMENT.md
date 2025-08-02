# Deployment Guide

This guide explains how to deploy the Georgia Power Bill Analyzer to various platforms for remote access.

## Quick GitHub Setup

### 1. Create GitHub Repository

1. Go to [GitHub.com](https://github.com) and create a new repository
2. Name it something like `georgia-power-analyzer` or `power-bill-analyzer`
3. Make it public (for free hosting) or private (if preferred)
4. Don't initialize with README (we already have one)

### 2. Push Code to GitHub

```bash
cd power-bill-analyzer
git init
git add .
git commit -m "Initial commit: Georgia Power Bill Analyzer web app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

## Deployment Options

### Option 1: Railway (Recommended - Free & Easy)

Railway offers free hosting that's perfect for this app:

1. **Sign up** at [railway.app](https://railway.app) using your GitHub account
2. **Connect Repository**: Click "New Project" → "Deploy from GitHub repo"
3. **Select your repository** from the list
4. **Configure**: Railway auto-detects Python apps, no configuration needed
5. **Deploy**: Click "Deploy" - your app will be live in ~2 minutes
6. **Access**: Railway provides a URL like `https://your-app-name.railway.app`

**Pros**: Free tier, automatic deployments, custom domains
**Cons**: May sleep after inactivity (wakes up quickly)

### Option 2: Render (Alternative Free Option)

1. **Sign up** at [render.com](https://render.com)
2. **New Web Service** → Connect GitHub repository
3. **Configure**:
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`
4. **Deploy**: Takes ~5 minutes to build and deploy

**Pros**: Always on, good free tier
**Cons**: Slower cold starts than Railway

### Option 3: Heroku (Paid but Reliable)

Heroku discontinued free tier but offers affordable hosting:

1. **Install Heroku CLI** and login
2. **Create Procfile** in your repository:
   ```
   web: python app.py
   ```
3. **Create runtime.txt** (optional, specifies Python version):
   ```
   python-3.11.0
   ```
4. **Deploy**:
   ```bash
   heroku create your-app-name
   git push heroku main
   heroku open
   ```

**Pros**: Most reliable, professional features
**Cons**: Costs $5-7/month for basic plan

### Option 4: GitHub Pages + Netlify (Static Only)

For a static version without file upload (demo mode only):

1. **Modify app** to work with static data
2. **Use GitHub Pages** for hosting
3. **Export results** as static HTML/JavaScript

**Pros**: Completely free, fast
**Cons**: No file upload, limited functionality

## Local Network Access

To access your app from other devices on your local network:

1. **Find your local IP address**:
   ```bash
   # On Mac/Linux:
   ifconfig | grep "inet "
   
   # On Windows:
   ipconfig
   ```

2. **Modify app.py** to accept external connections:
   ```python
   if __name__ == '__main__':
       app.run(debug=True, host='0.0.0.0', port=5000)
   ```

3. **Access from other devices**: `http://YOUR_LOCAL_IP:5000`

## Environment Variables

For production deployment, set these environment variables:

```bash
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
PORT=5000
```

Most platforms let you set these in their dashboard.

## Security Considerations

### For Public Deployment:
- Change the SECRET_KEY in `app.py`
- Consider adding file size limits
- Add rate limiting for uploads
- Consider user authentication
- Use HTTPS (most platforms provide this automatically)

### For Private Use:
- The current setup is fine for personal/friends use
- Consider password protection if needed

## Custom Domain

Most platforms allow custom domains:

1. **Buy a domain** (GoDaddy, Namecheap, etc.)
2. **Configure DNS** to point to your hosting platform
3. **Add domain** in your platform's dashboard
4. **Enable SSL** (usually automatic)

Example: `power-bill-analyzer.yourname.com`

## Monitoring and Maintenance

### Basic Monitoring:
- Check if app is responding: `curl https://your-app.railway.app/`
- Monitor error logs in platform dashboard
- Test periodically with sample data

### Updates:
- Push changes to GitHub
- Most platforms auto-deploy from main branch
- Test in a staging environment first for major changes

## Cost Estimates

| Platform | Free Tier | Paid Tier | Best For |
|----------|-----------|-----------|----------|
| Railway | 500 hours/month | $5+/month | Development/Personal |
| Render | 750 hours/month | $7+/month | Small apps |
| Heroku | None | $5-7/month | Professional use |
| Netlify | Unlimited static | $19+/month | Static sites |

## Troubleshooting

### Common Issues:

1. **Build Failures**: Check requirements.txt versions
2. **Port Issues**: Use environment PORT variable
3. **File Upload Issues**: Check platform file size limits
4. **Memory Issues**: Consider upgrading plan for large CSV files

### Debug Commands:
```bash
# Check if app starts locally
python app.py

# Test with sample data
python test_upload.py

# Check requirements
pip freeze > requirements.txt
```

## Sample GitHub Actions (Optional)

For automatic testing on every push:

Create `.github/workflows/test.yml`:
```yaml
name: Test App
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Start app and test
      run: |
        python app.py &
        sleep 5
        python test_upload.py
```

## Next Steps

1. **Choose a platform** (Railway recommended for beginners)
2. **Create GitHub repository** and push your code
3. **Deploy to chosen platform**
4. **Test with your data**
5. **Share the URL** with friends/family
6. **Monitor usage** and update as needed

## Support

If you need help with deployment:
1. Check platform documentation
2. Most platforms have excellent support chat
3. GitHub issues for code problems
4. Stack Overflow for technical questions

---

**Ready to deploy?** Start with Railway - it's the easiest option and will have your app running in under 5 minutes!