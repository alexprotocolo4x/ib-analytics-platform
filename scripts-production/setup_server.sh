#!/bin/bash
# IB Analytics Production - Automated Server Setup
# Run on fresh Ubuntu 22.04 server

set -e

echo "🚀 IB Analytics Production - Server Setup"
echo "=========================================="

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Pedir password de base de datos
echo -e "${YELLOW}Ingresa password para usuario de base de datos ib_admin:${NC}"
read -s DB_PASSWORD
echo ""

if [ -z "$DB_PASSWORD" ]; then
    echo -e "${RED}❌ Password no puede estar vacío${NC}"
    exit 1
fi

echo -e "${GREEN}📦 Actualizando sistema...${NC}"
apt update && apt upgrade -y

echo -e "${GREEN}🐘 Instalando PostgreSQL 14...${NC}"
sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
apt update
apt install -y postgresql-14 postgresql-contrib-14

echo -e "${GREEN}⏰ Instalando TimescaleDB...${NC}"
sh -c "echo 'deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main' > /etc/apt/sources.list.d/timescaledb.list"
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | apt-key add -
apt update
apt install -y timescaledb-2-postgresql-14

echo -e "${GREEN}⚙️  Configurando TimescaleDB...${NC}"
timescaledb-tune --quiet --yes

echo -e "${GREEN}🔄 Reiniciando PostgreSQL...${NC}"
systemctl restart postgresql
sleep 2

echo -e "${GREEN}🗄️  Creando base de datos y usuario...${NC}"
su - postgres << EOF
psql << PSQL
CREATE DATABASE ib_analytics;
CREATE USER ib_admin WITH ENCRYPTED PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE ib_analytics TO ib_admin;
\c ib_analytics
CREATE EXTENSION IF NOT EXISTS timescaledb;
\q
PSQL
EOF

echo -e "${GREEN}🐍 Instalando Python y dependencias...${NC}"
apt install -y python3-pip python3-venv git unzip curl

echo -e "${GREEN}📁 Creando directorios...${NC}"
mkdir -p /opt/ib-analytics/{data,reports}
cd /opt/ib-analytics

echo -e "${GREEN}🔗 Clonando repositorio...${NC}"
if [ -d "production" ]; then
    rm -rf production
fi
git clone https://github.com/alexprotocolo4x/ib-analytics-platform.git production 2>/dev/null || {
    echo "Git clone failed, downloading zip..."
    curl -L https://github.com/alexprotocolo4x/ib-analytics-platform/archive/main.zip -o repo.zip
    unzip -q repo.zip
    mv ib-analytics-platform-main production
    rm repo.zip
}

echo -e "${GREEN}🐍 Creando entorno virtual...${NC}"
python3 -m venv venv
source venv/bin/activate

echo -e "${GREEN}📦 Instalando librerías Python...${NC}"
pip install --quiet psycopg2-binary pandas openpyxl

echo -e "${GREEN}🗄️  Creando schema de base de datos...${NC}"
export DATABASE_URL="postgresql://ib_admin:$DB_PASSWORD@localhost:5432/ib_analytics"

if [ -f production/database/schema.sql ]; then
    psql $DATABASE_URL < production/database/schema.sql
else
    echo -e "${YELLOW}⚠️  Schema file not found, skipping...${NC}"
fi

echo -e "${GREEN}📝 Creando archivo de configuración...${NC}"
cat > /opt/ib-analytics/.env << ENVFILE
DATABASE_URL=postgresql://ib_admin:$DB_PASSWORD@localhost:5432/ib_analytics
ENVFILE

chmod 600 /opt/ib-analytics/.env

echo -e "${GREEN}📝 Creando script de activación...${NC}"
cat > /opt/ib-analytics/activate.sh << 'ACTIVATESCRIPT'
#!/bin/bash
cd /opt/ib-analytics/production
source ../venv/bin/activate
export $(cat ../.env | xargs)
echo "✅ Entorno activado"
echo "DATABASE_URL configured"
echo ""
echo "Comandos disponibles:"
echo "  python3 scripts/import_deals.py <archivo.htm>"
echo "  python3 scripts/query_analytics.py summary"
echo "  python3 scripts/query_analytics.py export"
ACTIVATESCRIPT

chmod +x /opt/ib-analytics/activate.sh

# Get server IP
SERVER_IP=$(curl -s ifconfig.me)

echo ""
echo -e "${GREEN}✅ ¡INSTALACIÓN COMPLETADA!${NC}"
echo "=========================================="
echo ""
echo -e "${YELLOW}📋 INFORMACIÓN DEL SERVIDOR${NC}"
echo "IP:          $SERVER_IP"
echo "Database:    ib_analytics"
echo "User:        ib_admin"
echo "Password:    [guardado en /opt/ib-analytics/.env]"
echo ""
echo -e "${YELLOW}🚀 PRÓXIMOS PASOS${NC}"
echo ""
echo "1. Subir tus archivos HTML al servidor:"
echo "   ${GREEN}scp 'archivo.htm' root@$SERVER_IP:/opt/ib-analytics/data/${NC}"
echo ""
echo "2. Activar entorno:"
echo "   ${GREEN}source /opt/ib-analytics/activate.sh${NC}"
echo ""
echo "3. Importar datos:"
echo "   ${GREEN}python3 scripts/import_deals.py /opt/ib-analytics/data/archivo.htm${NC}"
echo ""
echo "4. Consultar análisis:"
echo "   ${GREEN}python3 scripts/query_analytics.py summary${NC}"
echo ""
echo "5. Exportar a Excel:"
echo "   ${GREEN}python3 scripts/query_analytics.py export${NC}"
echo ""
echo "6. Descargar Excel a tu Mac:"
echo "   ${GREEN}scp root@$SERVER_IP:/tmp/ib_analytics_export.xlsx ~/Desktop/${NC}"
echo ""
echo -e "${GREEN}📖 Documentación completa: /opt/ib-analytics/production/README.md${NC}"
echo ""
