#!/bin/bash

# Post-deployment script to expose the service and provide access URL
echo "🚀 =============================================="
echo "🌐 POST-DEPLOYMENT SERVICE EXPOSURE"
echo "=============================================="

# Kill any existing port-forward processes
pkill -f "kubectl port-forward" || true
sleep 2

# Get cluster type and provide appropriate access method
if command -v minikube &> /dev/null && minikube status &> /dev/null; then
    echo "📡 Detected Minikube cluster"
    MINIKUBE_IP=$(minikube ip)
    NODEPORT=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.spec.ports[0].nodePort}')
    echo "🔗 Site URL: http://$MINIKUBE_IP:$NODEPORT"
    echo "🔗 API Test: http://$MINIKUBE_IP:$NODEPORT/test/"
    
elif docker ps | grep -q "kindest/node"; then
    echo "📡 Detected Kind cluster"
    echo "🔧 Setting up port forwarding..."
    
    # Start port forwarding in background
    kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 8080:80 --address=0.0.0.0 > /dev/null 2>&1 &
    PORT_FORWARD_PID=$!
    
    # Wait for port forwarding to be ready
    sleep 5
    
    # Test connectivity
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 | grep -q "200"; then
        echo "✅ Port forwarding successful!"
        echo "🔗 Site URL: http://localhost:8080"
        echo "🔗 API Test: http://localhost:8080/test/"
        echo "🔗 Health Check: http://localhost:8080/echo/"
        
        # Test endpoints
        echo ""
        echo "🧪 Testing endpoints..."
        FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080)
        BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/test/)
        
        echo "   Frontend Status: $FRONTEND_STATUS"
        echo "   Backend API Status: $BACKEND_STATUS"
        
        if [ "$FRONTEND_STATUS" = "200" ] && [ "$BACKEND_STATUS" = "200" ]; then
            echo "✅ All services are running correctly!"
        else
            echo "⚠️  Some services may have issues"
        fi
        
    else
        echo "❌ Port forwarding failed"
        kill $PORT_FORWARD_PID 2>/dev/null || true
    fi
    
else
    echo "📡 Detected cloud/external cluster"
    EXTERNAL_IP=$(kubectl get ingress scriptify-ingress -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [ -z "$EXTERNAL_IP" ]; then
        EXTERNAL_IP=$(kubectl get ingress scriptify-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    fi
    
    if [ -n "$EXTERNAL_IP" ]; then
        echo "🔗 Site URL: http://$EXTERNAL_IP"
        echo "🔗 API Test: http://$EXTERNAL_IP/test/"
    else
        echo "⚠️  External IP not yet assigned. Please wait a few minutes."
        echo "🔍 Check ingress status: kubectl get ingress"
    fi
fi

echo "=============================================="
echo "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "=============================================="
