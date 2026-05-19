#!/bin/bash
# IB Analytics - VPS Deployment Script
# Run on fresh Ubuntu 22.04 server

set -e

echo "🚀 IB Analytics Platform - VPS Setup"
echo "======================================"

# Update system
echo "📦 Updating system..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
echo "🐳 Installing Docker..."
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose
echo "🔧 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repository
echo "📥 Cloning repository..."
cd /opt
sudo git clone https://github.com/alexprotocolo4x/ib-analytics-platform.git
cd ib-analytics-platform

# Build Docker image
echo "🏗️  Building Docker image..."
sudo docker build -t ib-analytics .

# Run container
echo "🚀 Starting container..."
sudo docker run -d \
  --name ib-analytics \
  --restart always \
  -p 80:8100 \
  ib-analytics

# Install nginx (optional, for custom domain)
echo "🌐 Installing Nginx..."
sudo apt-get install -y nginx

# Basic nginx config
sudo tee /etc/nginx/sites-available/ib-analytics > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    
    client_max_body_size 3G;
    
    location / {
        proxy_pass http://localhost:8100;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 600s;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/ib-analytics /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Get server IP
IP=$(curl -s ifconfig.me)

echo ""
echo "✅ ¡Deployment completado!"
echo "======================================"
echo "🌐 URL: http://$IP"
echo "🐳 Container: ib-analytics"
echo "📊 Status: docker ps"
echo "📋 Logs: docker logs ib-analytics"
echo ""
echo "Para actualizar:"
echo "  cd /opt/ib-analytics-platform"
echo "  sudo git pull"
echo "  sudo docker build -t ib-analytics ."
echo "  sudo docker stop ib-analytics && sudo docker rm ib-analytics"
echo "  sudo docker run -d --name ib-analytics --restart always -p 8100:8100 ib-analytics"
echo ""
