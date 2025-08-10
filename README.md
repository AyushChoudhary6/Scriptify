# Scriptify: AI-Powered YouTube Video Summarizer

🎥 **Transform YouTube videos into intelligent, comprehensive summaries using advanced AI models.**

Scriptify is a modern web application that generates detailed, structured summaries from YouTube videos using cutting-edge AI technology. Built with a robust DevOps pipeline featuring Docker containerization and Kubernetes orchestration.

## ✨ Features
- 🤖 **AI-Powered Summarization**: Advanced natural language processing for intelligent video summaries
- 📊 **Multiple Summary Types**: Comprehensive, Brief, Bullet Points, and Academic formats
- ⏱️ **Automatic Timestamps**: Generated timestamps for key moments in videos
- 🎯 **Key Highlights**: AI-extracted important points and insights
- 📱 **Modern React Frontend**: Built with Vite for fast, responsive user experience
- 🚀 **FastAPI Backend**: High-performance Python backend with async support
- 🐳 **Docker Containerization**: Consistent deployment across environments
- ⚙️ **Kubernetes Orchestration**: Production-ready container management
- 📈 **Auto-scaling**: Horizontal Pod Autoscaler (HPA) for traffic management
- 🔐 **Secure Secrets Management**: Kubernetes secrets for API key protection
- 🔄 **GitLab CI/CD Pipeline**: Automated build, test, and deployment

## 🏗️ Architecture

### **Hybrid Docker + Kubernetes Approach**
- **🔧 Docker**: Container image building and development
- **☸️ Kubernetes**: Production deployment and orchestration
- **🌐 Frontend**: React + Vite + Nginx (containerized)
- **⚡ Backend**: FastAPI + Python (containerized)
- **🔀 Ingress**: Traffic routing and load balancing
- **📊 HPA**: Automatic scaling based on resource usage
- **🔐 Secrets**: Secure API key management

### **CI/CD Pipeline Flow**
```
Git Push → GitLab CI → Docker Build → Kubernetes Deploy → Live App
    ↓           ↓           ↓             ↓            ↓
  Code      Sequential    Images      K8s Manifests   Auto Port
 Changes    Build Jobs    Created      Applied       Forwarding
```

## 🚀 Quick Start Guide

### **Option 1: Automatic Deployment (Recommended)**
Use the GitLab CI/CD pipeline for automatic deployment:

1. **Clone the Repository**
```bash
git clone https://github.com/AyushChoudhary6/Scriptify.git
cd Scriptify
```

2. **Setup GitLab Runner**
```bash
# Start GitLab runner with Docker
docker compose -f gitlab-runner-docker-compose.yml up -d

# Register runner with your GitLab project
docker exec -it gitlab-runner gitlab-runner register \
  --url https://gitlab.com \
  --registration-token YOUR_TOKEN_HERE \
  --executor docker \
  --docker-image alpine:latest \
  --description "Local Docker Runner" \
  --tag-list "local" \
  --docker-privileged=true \
  --docker-volumes /var/run/docker.sock:/var/run/docker.sock
```

3. **Configure API Keys**
Update your Kubernetes secrets file with your API keys:
```bash
# Edit k8s/secrets.yml with your actual API keys
kubectl apply -f k8s/secrets.yml
```

4. **Deploy via Pipeline**
```bash
git add .
git commit -m "Deploy Scriptify"
git push origin main
```

The pipeline will automatically:
- 🔧 Build backend Docker image
- 🎨 Build frontend Docker image  
- 🧪 Run tests
- 🚀 Deploy to Kubernetes
- 🌐 Set up port forwarding
- ✅ Make app accessible at localhost:3000

### **Option 2: Manual Deployment**

#### **Local Development with Docker**
```bash
# Build images
docker build -t scriptify-backend:latest ./backend
docker build -t scriptify-frontend:latest ./frontend

# Run with Docker Compose
docker compose up -d

# Access at:
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

#### **Kubernetes Deployment**
```bash
# Build Docker images
docker build -t scriptify-backend:latest ./backend
docker build -t scriptify-frontend:latest ./frontend

# Apply Kubernetes manifests
kubectl apply -f k8s/

# Port forward to access locally
kubectl port-forward service/frontend-service 3000:80
kubectl port-forward service/backend-service 8000:8000
```

## 🔧 DevOps Pipeline Details

### **GitLab CI/CD Stages**
1. **🔧 Build Backend**: Docker image creation for FastAPI backend
2. **🎨 Build Frontend**: Docker image creation for React frontend  
3. **🧪 Test**: Validation of built images and application health
4. **🚀 Deploy**: Kubernetes deployment with automatic port forwarding

### **Pipeline Features**
- ✅ **Sequential Builds**: Backend → Frontend → Test → Deploy
- ✅ **Local GitLab Runner**: Custom runner with "local" tag
- ✅ **Kubernetes Integration**: Complete k8s manifest application
- ✅ **Auto Port Forwarding**: Immediate localhost access after deployment
- ✅ **Health Checks**: Deployment readiness validation
- ✅ **Resource Management**: HPA, Secrets, Ingress configuration

### **Kubernetes Components Applied**
- 📦 **Deployments**: backend-deployment.yml, frontend-deployment.yml
- 🌐 **Services**: backend-service.yml, frontend-service.yml  
- 🔐 **Secrets**: secrets.yml (API keys management)
- 🔀 **Ingress**: ingress.yml (traffic routing)
- 📈 **HPA**: hpa.yml (horizontal pod autoscaling)

## 🛠️ Technology Stack

### **Frontend**
- ⚛️ **React 18**: Modern component-based UI
- ⚡ **Vite**: Fast build tool and dev server
- 🎨 **CSS3**: Custom styling with gradients and animations
- 🐳 **Nginx**: Production web server in container

### **Backend**  
- 🐍 **FastAPI**: High-performance async Python framework
- 🤖 **AI Integration**: AssemblyAI + Gemini APIs
- 📦 **Uvicorn**: ASGI server for production
- 🐳 **Docker**: Containerized deployment

### **DevOps & Infrastructure**
- 🐳 **Docker**: Container runtime and image building
- ☸️ **Kubernetes**: Container orchestration platform
- 🔄 **GitLab CI/CD**: Automated pipeline with local runner
- 📊 **HPA**: Kubernetes Horizontal Pod Autoscaler
- 🔐 **Secrets Management**: Kubernetes native secret storage

### **Monitoring & Scaling**
- 📈 **Resource Monitoring**: CPU/Memory usage tracking
- 🔄 **Auto-scaling**: Dynamic pod scaling based on load
- 🔍 **Health Checks**: Liveness and readiness probes
- 📊 **Deployment Status**: Real-time pod and service monitoring

## 📋 Prerequisites

- 🐳 **Docker & Docker Compose**: Container runtime
- ☸️ **Kubernetes Cluster**: Local (kind, minikube) or cloud cluster  
- 🔄 **GitLab Runner**: For CI/CD pipeline execution
- 🔑 **API Keys**: AssemblyAI and Gemini API access

## 🎯 Usage

1. **Access the Application**: http://localhost:3000
2. **Paste YouTube URL**: Any valid YouTube video link
3. **Select Summary Type**: Choose from 4 AI summary formats
4. **Get AI Summary**: Receive intelligent video summary with timestamps

## 📊 Application URLs

After successful deployment:
- 🌐 **Frontend**: http://localhost:3000
- 🔧 **Backend API**: http://localhost:8000  
- 📖 **API Documentation**: http://localhost:8000/docs
- 🎥 **YouTube Summarizer**: Ready to use!

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Contact

**Ayush Choudhary**
- 🔗 **LinkedIn**: [Connect with me](https://linkedin.com/in/ayushchoudhary6)
- 📧 **Email**: ayushrjchoudhary2005@gmail.com
- 🐙 **GitHub**: [@AyushChoudhary6](https://github.com/AyushChoudhary6)

## ⭐ Show Your Support

Give a ⭐ if this project helped you learn about modern DevOps practices with Docker and Kubernetes!

---

**Built with ❤️ by Ayush Choudhary | Showcasing DevOps Excellence with Docker + Kubernetes**
