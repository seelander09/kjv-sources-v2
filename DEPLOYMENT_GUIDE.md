# KJV Sources AI Chat - Internet Deployment Guide
================================================

## 🚀 Quick Start (Local Testing)

### 1. Test the New AI Chat Interface
```powershell
# Start the server
.\start_server.ps1

# Open the new AI chat interface
Start-Process "http://127.0.0.1:8000/frontend/ai_chat.html"
```

## 🌐 Internet Deployment Options

### Option 1: Docker Deployment (Recommended)

#### Prerequisites
- Docker and Docker Compose installed
- Domain name (optional but recommended)
- SSL certificate (for HTTPS)

#### Step 1: Build and Deploy
```bash
# Build the Docker image
docker-compose build

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

#### Step 2: Configure Domain (Optional)
1. Update `nginx.conf` with your domain name
2. Place SSL certificates in `./ssl/` directory
3. Restart nginx: `docker-compose restart nginx`

#### Step 3: Access Your Application
- **AI Chat Interface**: `https://yourdomain.com/frontend/ai_chat.html`
- **API Documentation**: `https://yourdomain.com/docs`
- **Health Check**: `https://yourdomain.com/health`

### Option 2: Cloud Platform Deployment

#### Heroku Deployment
```bash
# Create Heroku app
heroku create your-kjv-ai-chat

# Set environment variables
heroku config:set ENVIRONMENT=production
heroku config:set QDRANT_HOST=your-qdrant-host
heroku config:set QDRANT_API_KEY=your-qdrant-api-key

# Deploy
git push heroku main
```

#### Railway Deployment
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

#### DigitalOcean App Platform
1. Connect your GitHub repository
2. Configure build settings:
   - Build Command: `pip install -r requirements.txt && pip install -r api_requirements.txt`
   - Run Command: `uvicorn rag_api_server:app --host 0.0.0.0 --port $PORT`
3. Set environment variables
4. Deploy

### Option 3: VPS Deployment

#### Ubuntu/Debian Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone your repository
git clone https://github.com/yourusername/kjv-sources.git
cd kjv-sources

# Deploy
docker-compose up -d
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file:
```env
# Server Configuration
ENVIRONMENT=production
PORT=8000
WORKERS=4

# Database
QDRANT_HOST=your-qdrant-host
QDRANT_PORT=6333
QDRANT_API_KEY=your-qdrant-api-key

# API Keys (for enhanced AI)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Security
SECRET_KEY=your-secret-key
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Monitoring
LOG_LEVEL=INFO
ENABLE_METRICS=true
```

### SSL Certificate Setup
```bash
# Using Let's Encrypt
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Monitoring and Maintenance

### Health Checks
```bash
# Check application health
curl https://yourdomain.com/health

# Check Docker services
docker-compose ps

# View logs
docker-compose logs -f kjv-ai-chat
```

### Backup Strategy
```bash
# Backup Qdrant data
docker run --rm -v qdrant_data:/data -v $(pwd):/backup alpine tar czf /backup/qdrant_backup.tar.gz -C /data .

# Backup application data
tar czf app_backup.tar.gz logs/ uploads/ cache/
```

### Scaling
```bash
# Scale the application
docker-compose up -d --scale kjv-ai-chat=3

# Add load balancer
docker-compose up -d nginx
```

## 🔒 Security Considerations

### Production Security Checklist
- [ ] SSL/TLS certificates installed
- [ ] Environment variables secured
- [ ] Rate limiting configured
- [ ] CORS origins restricted
- [ ] Security headers enabled
- [ ] Non-root user in Docker
- [ ] Regular security updates
- [ ] Backup strategy implemented

### Firewall Configuration
```bash
# UFW firewall setup
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

## 📈 Performance Optimization

### Caching Strategy
- Redis for session storage
- CDN for static assets
- Browser caching headers
- API response caching

### Database Optimization
- Qdrant indexing optimization
- Connection pooling
- Query optimization

## 🐛 Troubleshooting

### Common Issues

#### 1. CORS Errors
```javascript
// Update frontend/ai_chat.html
const API_BASE = 'https://yourdomain.com';  // Change from localhost
```

#### 2. Database Connection Issues
```bash
# Check Qdrant status
docker-compose logs qdrant

# Restart services
docker-compose restart
```

#### 3. Memory Issues
```bash
# Monitor resource usage
docker stats

# Increase memory limits in docker-compose.yml
```

### Log Analysis
```bash
# View application logs
docker-compose logs kjv-ai-chat

# View nginx logs
docker-compose logs nginx

# Real-time monitoring
docker-compose logs -f
```

## 🎯 Next Steps

### 1. Enhanced AI Integration
- Integrate with OpenAI GPT-4
- Add Anthropic Claude support
- Implement local LLM options

### 2. Advanced Features
- User authentication
- Conversation history
- Export functionality
- Advanced analytics

### 3. Monitoring
- Set up Prometheus/Grafana
- Implement alerting
- Performance monitoring

## 📞 Support

For deployment issues:
1. Check the logs: `docker-compose logs`
2. Verify configuration: `python deployment_config.py`
3. Test locally first: `.\start_server.ps1`

Your KJV Sources AI Chat is now ready for internet deployment! 🎉
