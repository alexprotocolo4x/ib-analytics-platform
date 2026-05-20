# IB Analytics Production System

Sistema de producción para procesar y analizar millones de deals de MT5 Administrator.

## 🎯 Características

- ✅ **Procesa archivos de cualquier tamaño** (hasta 50GB+)
- ✅ **Importación streaming** (línea por línea, sin cargar en RAM)
- ✅ **PostgreSQL + TimescaleDB** (optimizado para series temporales)
- ✅ **Vistas materializadas** con auto-refresh
- ✅ **Consultas instantáneas** sobre millones de deals
- ✅ **Export a Excel** con análisis completos
- ✅ **Dashboard web** (próximamente)

## 📦 Stack Tecnológico

- **PostgreSQL 14+** con extensión TimescaleDB
- **Python 3.9+** con psycopg2, pandas
- **DigitalOcean Droplet** 8GB RAM ($24/mes) o similar

---

## 🚀 Setup - DigitalOcean Droplet

### 1. Crear Droplet

1. Ve a https://cloud.digitalocean.com
2. **Create → Droplets**
3. Configuración:
   - **Image**: Ubuntu 22.04 LTS
   - **Size**: Basic → **$24/month (8GB RAM, 160GB SSD)**
   - **Region**: Frankfurt (más cerca de Dubai)
   - **Authentication**: SSH Key o Password
   - **Hostname**: `ib-analytics-prod`
4. **Create Droplet**
5. **Copia la IP del droplet**

### 2. Conectar al Servidor

```bash
ssh root@YOUR_DROPLET_IP
```

### 3. Instalar PostgreSQL + TimescaleDB

```bash
# Actualizar sistema
apt update && apt upgrade -y

# Instalar PostgreSQL 14
sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
apt update
apt install -y postgresql-14 postgresql-contrib-14

# Instalar TimescaleDB
sh -c "echo 'deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main' > /etc/apt/sources.list.d/timescaledb.list"
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | apt-key add -
apt update
apt install -y timescaledb-2-postgresql-14

# Configurar TimescaleDB
timescaledb-tune --quiet --yes

# Reiniciar PostgreSQL
systemctl restart postgresql
```

### 4. Crear Base de Datos

```bash
# Cambiar a usuario postgres
su - postgres

# Crear base de datos y usuario
psql << EOF
CREATE DATABASE ib_analytics;
CREATE USER ib_admin WITH ENCRYPTED PASSWORD 'CAMBIA_ESTA_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE ib_analytics TO ib_admin;
\c ib_analytics
CREATE EXTENSION IF NOT EXISTS timescaledb;
\q
EOF

exit
```

### 5. Instalar Python y Dependencias

```bash
apt install -y python3-pip python3-venv

# Crear entorno virtual
mkdir -p /opt/ib-analytics
cd /opt/ib-analytics
python3 -m venv venv
source venv/bin/activate

# Instalar librerías
pip install psycopg2-binary pandas openpyxl
```

### 6. Clonar Repositorio

```bash
cd /opt/ib-analytics
git clone https://github.com/alexprotocolo4x/ib-analytics-platform.git production
cd production
```

O si no tienes Git aún:

```bash
cd /opt/ib-analytics
curl -L https://github.com/alexprotocolo4x/ib-analytics-platform/archive/main.zip -o repo.zip
apt install -y unzip
unzip repo.zip
mv ib-analytics-platform-main production
cd production
```

### 7. Crear Schema de Base de Datos

```bash
# Configurar variable de entorno
export DATABASE_URL='postgresql://ib_admin:TU_PASSWORD@localhost:5432/ib_analytics'

# Crear schema
psql $DATABASE_URL < database/schema.sql
```

---

## 📥 Importar Datos

### Opción A - Subir archivo al servidor

```bash
# Desde tu Mac
scp "Deals test1.htm.zip" root@YOUR_DROPLET_IP:/opt/ib-analytics/data/

# En el servidor
cd /opt/ib-analytics/data
unzip "Deals test1.htm.zip"
```

### Opción B - Descargar desde Google Drive

```bash
# En el servidor
cd /opt/ib-analytics/data
curl -L "https://drive.usercontent.google.com/download?id=FILE_ID&export=download&confirm=t" -o deals.zip
unzip deals.zip
```

### Ejecutar Importación

```bash
cd /opt/ib-analytics/production

# Activar entorno virtual
source ../venv/bin/activate

# Configurar DATABASE_URL
export DATABASE_URL='postgresql://ib_admin:TU_PASSWORD@localhost:5432/ib_analytics'

# Importar archivo (puede tomar 20-40 minutos para 2GB)
python3 scripts/import_deals.py /opt/ib-analytics/data/deals.htm
```

**Output esperado:**
```
🚀 IB Analytics - Importación a PostgreSQL
============================================================
📁 Archivo: deals.htm
💾 Tamaño: 1957.7 MB
📦 Batch size: 10,000 filas
============================================================

🔌 Conectando a PostgreSQL...
✅ Conexión establecida
  ✅ Encoding: utf-8

📖 Leyendo archivo...
  📋 Headers: 25 columnas detectadas
  1,000,000 líneas | 45,230 deals | 5.2% completado
  2,000,000 líneas | 92,150 deals | 10.8% completado
  ...
  
✅ IMPORTACIÓN COMPLETADA
============================================================
Líneas leídas:        75,257,242
Deals importados:     1,234,567
Tiempo total:         1823.4s (30.4 min)
Velocidad:            677 deals/segundo

📊 RESUMEN EN BASE DE DATOS:
Total deals:          1,234,567
Cuentas únicas:       45,678
Símbolos únicos:      89
Volumen total:        12,345.67 lotes
Revenue bruto:        $308,641.75
P&L total:            $456,789.12

🎉 Listo para consultas!
```

---

## 📊 Consultas y Análisis

### Resumen General

```bash
python3 scripts/query_analytics.py summary
```

### Top Símbolos

```bash
# Top 10
python3 scripts/query_analytics.py symbols

# Top 50
python3 scripts/query_analytics.py symbols 50
```

### Top Cuentas

```bash
python3 scripts/query_analytics.py accounts 20
```

### Análisis por Fecha

```bash
python3 scripts/query_analytics.py date 2026-05-01 2026-05-31
```

### Exportar a Excel

```bash
# Excel en /tmp
python3 scripts/query_analytics.py export

# Excel personalizado
python3 scripts/query_analytics.py export /opt/ib-analytics/reports/mayo_2026.xlsx
```

### Descargar Excel a tu Mac

```bash
scp root@YOUR_DROPLET_IP:/tmp/ib_analytics_export.xlsx ~/Desktop/
```

---

## 🗄️ Consultas SQL Directas

```bash
# Conectar a PostgreSQL
psql $DATABASE_URL

# Ejemplos de consultas
```

**Deals por día:**
```sql
SELECT 
    DATE(time) as date,
    COUNT(*) as deals,
    SUM(volume) as volume,
    SUM(profit) as profit
FROM deals
GROUP BY DATE(time)
ORDER BY date DESC;
```

**Revenue por símbolo y mes:**
```sql
SELECT 
    symbol,
    DATE_TRUNC('month', time) as month,
    COUNT(*) as deals,
    SUM(volume) * 25.0 as revenue
FROM deals
GROUP BY symbol, month
ORDER BY month DESC, revenue DESC;
```

**Cuentas top por semana:**
```sql
SELECT 
    login,
    DATE_TRUNC('week', time) as week,
    SUM(volume) as volume,
    SUM(profit) as profit
FROM deals
GROUP BY login, week
ORDER BY week DESC, volume DESC
LIMIT 20;
```

---

## 🔄 Importar Múltiples Archivos

Para procesar un mes completo (múltiples días):

```bash
cd /opt/ib-analytics/production
source ../venv/bin/activate
export DATABASE_URL='postgresql://ib_admin:PASSWORD@localhost:5432/ib_analytics'

# Importar todos los archivos en un directorio
for file in /opt/ib-analytics/data/*.htm; do
    echo "Procesando: $file"
    python3 scripts/import_deals.py "$file"
done
```

---

## ⚡ Performance

**Hardware recomendado:**

| Tamaño Archivo | RAM Necesaria | Tiempo Estimado |
|----------------|---------------|-----------------|
| 100 MB         | 2 GB          | 2-3 min         |
| 500 MB         | 4 GB          | 8-10 min        |
| 2 GB           | 8 GB          | 30-40 min       |
| 10 GB          | 16 GB         | 2-3 horas       |

**Optimizaciones:**
- BATCH_SIZE = 10,000 (ajustar según RAM disponible)
- TimescaleDB compression (después de importación)
- Índices automáticos en columnas clave

---

## 🌐 Dashboard Web (Próximo)

FastAPI + Next.js dashboard para:
- Visualización en tiempo real
- Filtros dinámicos (fecha, cuenta, símbolo)
- Gráficas interactivas
- Export automático de reportes

---

## 📝 Logs de Importación

Ver historial de importaciones:

```sql
SELECT 
    filename,
    deals_imported,
    duration_seconds,
    started_at,
    status
FROM import_logs
ORDER BY started_at DESC;
```

---

## 🔒 Seguridad

```bash
# Cambiar password de PostgreSQL
psql -U postgres
ALTER USER ib_admin WITH PASSWORD 'NUEVA_PASSWORD_SEGURA';

# Configurar firewall (solo permitir SSH)
ufw allow OpenSSH
ufw enable

# Si necesitas acceso remoto a PostgreSQL:
ufw allow 5432/tcp
# Editar /etc/postgresql/14/main/postgresql.conf
# listen_addresses = '*'
# Editar /etc/postgresql/14/main/pg_hba.conf
# host all all 0.0.0.0/0 md5
systemctl restart postgresql
```

---

## 💰 Costos

**DigitalOcean Droplet 8GB:**
- $24/mes (facturación por hora: $0.036/hora)
- Incluye 1TB transfer mensual
- Snapshots adicionales: $0.05/GB/mes

**Total estimado:** $24-30/mes

---

## 🆘 Troubleshooting

**Error: "could not connect to server"**
```bash
systemctl status postgresql
systemctl restart postgresql
```

**Error: "out of memory"**
- Reduce BATCH_SIZE en import_deals.py
- Upgrade a droplet con más RAM

**Importación muy lenta**
- Verificar uso de CPU: `htop`
- Verificar I/O de disco: `iotop`
- Considerar SSD más rápido

---

## 📞 Soporte

- GitHub: https://github.com/alexprotocolo4x/ib-analytics-platform
- Docs TimescaleDB: https://docs.timescale.com
- PostgreSQL: https://www.postgresql.org/docs/
