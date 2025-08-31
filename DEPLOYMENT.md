# 🚀 URDB Tariff Viewer - Deployment Guide

This guide will help you deploy your Streamlit URDB Tariff Viewer application to make it accessible on the internet.

## 📋 Prerequisites

- GitHub account (for Streamlit Cloud deployment)
- Basic familiarity with command line/terminal
- Your app code ready for deployment

## 🎯 Deployment Options

### Option 1: Streamlit Cloud (Recommended - Easiest) ⭐

**Pros:** Free, easiest setup, optimized for Streamlit apps
**Cons:** Limited customization, may have usage limits

#### Steps:

1. **Create a GitHub Repository**
   ```bash
   # Initialize git if not already done
   git init
   git add .
   git commit -m "Initial commit - URDB Tariff Viewer"

   # Create repository on GitHub and push
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git push -u origin main
   ```

2. **Deploy to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub account
   - Select your repository
   - Set main file path to `app.py`
   - Click "Deploy"

3. **Your app will be live at:** `https://YOUR_REPO_NAME-YOUR_USERNAME.streamlit.app`

### Option 2: Heroku (Good Alternative)

**Pros:** Free tier, more customization options
**Cons:** May require more configuration

#### Steps:

1. **Install Heroku CLI**
   ```bash
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Create Heroku App**
   ```bash
   heroku login
   heroku create your-app-name
   ```

3. **Create Procfile**
   ```bash
   echo "web: streamlit run app.py --server.port $PORT --server.headless true" > Procfile
   ```

4. **Deploy**
   ```bash
   git add Procfile
   git commit -m "Add Procfile for Heroku"
   git push heroku main
   ```

5. **Your app will be live at:** `https://your-app-name.herokuapp.com`

### Option 3: AWS/Google Cloud/Azure (Production Ready)

**Pros:** Scalable, professional, full control
**Cons:** Paid, more complex setup

Choose based on your cloud preference:

#### AWS (EC2 + Docker)
1. Create EC2 instance
2. Install Docker
3. Create Dockerfile
4. Deploy container

#### Google Cloud Run
1. Create Dockerfile
2. Use Cloud Build
3. Deploy to Cloud Run

## 🔧 Configuration Files Created

Your app is now ready with these deployment files:

- `requirements.txt` - Python dependencies
- `packages.txt` - System dependencies
- `.streamlit/config.toml` - Streamlit configuration
- `Procfile` - Heroku process definition (create if using Heroku)

## 🧪 Testing Your Deployment

After deployment:

1. **Test all features:**
   - Tariff selection
   - Heatmap visualization
   - Cost calculator
   - Dark/light mode toggle
   - Responsive design

2. **Test different devices:**
   - Desktop browsers
   - Mobile devices
   - Different screen sizes

3. **Performance check:**
   - Load times
   - Data processing speed
   - Memory usage

## 🔒 Security Considerations

- Your app is publicly accessible
- Consider implementing authentication if needed
- Be aware of usage limits on free tiers
- Monitor for any security vulnerabilities in dependencies

## 🚨 Troubleshooting

### Common Issues:

1. **"No JSON files found" error:**
   - Ensure `tariffs/` directory is included in deployment
   - Check file paths in your code

2. **Import errors:**
   - Verify all dependencies are in `requirements.txt`
   - Check Python version compatibility

3. **Memory/timeout issues:**
   - Large datasets may cause timeouts
   - Consider optimizing data loading

4. **File upload limits:**
   - Streamlit Cloud has file size limits
   - Consider using cloud storage for large files

## 📈 Scaling and Optimization

For production use:

1. **Optimize data loading:**
   - Cache frequently used data
   - Use efficient data structures

2. **Monitor performance:**
   - Use Streamlit's built-in analytics
   - Monitor server resources

3. **Backup strategy:**
   - Regular data backups
   - Version control for code changes

## 🎨 Customization

After deployment, you can customize:

- App title and favicon
- Color scheme
- Add authentication
- Custom domain setup
- Advanced analytics

## 📞 Support

- Streamlit Cloud: [docs.streamlit.io](https://docs.streamlit.io)
- Heroku: [devcenter.heroku.com](https://devcenter.heroku.com)
- General help: Check deployment platform documentation

---

**Happy deploying! 🎉**

Your URDB Tariff Viewer will soon be accessible to anyone with an internet connection.
