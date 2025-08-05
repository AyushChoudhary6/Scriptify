# Scriptify: YouTube to Text Converter

Convert any YouTube video to text using FastAPI, React, Docker, and Kubernetes.

## Features
- Download and transcribe YouTube videos to text
- Real transcription via AssemblyAI API
- Enhanced formatting via Gemini API
- Modern React frontend (Vite)
- FastAPI backend
- Containerized with Docker
- Orchestrated with Kubernetes (Deployments, Services, Ingress)
- Autoscaling with Horizontal Pod Autoscaler (HPA)
- Secrets management for API keys

## Architecture
- **Frontend:** React + Vite (Dockerized)
- **Backend:** FastAPI (Dockerized)
- **Kubernetes:** Deploys both services, manages scaling and routing
- **Ingress:** nginx controller for routing
- **HPA:** Scales backend pods based on CPU

## Quick Start Guide

### 1. Clone the Repo
```bash
git clone https://github.com/AyushChoudhary6/Scriptify.git
cd Scriptify
```

### 2. Build Docker Images
```bash
docker build -t scriptify-frontend:latest ./frontend
docker build -t scriptify-backend:latest ./backend
```

### 3. Push Images (if using Docker Hub)
```bash
docker tag scriptify-frontend:latest <your-dockerhub-username>/scriptify-frontend:latest
docker tag scriptify-backend:latest <your-dockerhub-username>/scriptify-backend:latest
docker push <your-dockerhub-username>/scriptify-frontend:latest
docker push <your-dockerhub-username>/scriptify-backend:latest
```

### 4. Set API Keys
Create Kubernetes secrets for AssemblyAI and Gemini API keys:
```bash
kubectl create secret generic backend-secrets \
  --from-literal=assemblyai-api-key=<YOUR_ASSEMBLYAI_API_KEY> \
  --from-literal=gemini-api-key=<YOUR_GEMINI_API_KEY>
```

### 5. Deploy to Kubernetes
```bash
kubectl apply -f k8s/
```

### 6. Install Metrics Server (for HPA)
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### 7. Access the App
- Use `kubectl port-forward` or your cloud provider's LoadBalancer IP to access the frontend.
- Example:
```bash
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80
```
- Visit [http://localhost:8080](http://localhost:8080)

## Notes
- Make sure Docker and Kubernetes are installed and running.
- API keys are required for transcription and enhancement features.
- HPA will autoscale backend pods based on CPU usage.

## Contact
Made by Ayush Choudhary. For questions, open an issue or connect on LinkedIn.
