# IB Analytics Production - Quick Start

## ✅ Sistema Completo Creado

**Capacidad:** Procesar archivos de **cualquier tamaño** (2GB, 50GB, lo que sea)

**Stack:**
- PostgreSQL + TimescaleDB (series temporales)
- Python batch importer (streaming línea por línea)
- Consultas SQL instantáneas sobre millones de deals
- Export a Excel automático

**Código:** https://github.com/alexprotocolo4x/ib-analytics-platform

---

## 🚀 Setup (20 minutos)

### Paso 1 - Crear Droplet en DigitalOcean

1. Ve a https://cloud.digitalocean.com
2. **Create → Droplets**
3. Configuración:
   - Ubuntu 22.04 LTS
   - **Basic $24/month** (8GB RAM, 160GB SSD)
   - Region: Frankfurt
   - Authentication: Password
   - Hostname: `ib-analytics`
4. **Create Droplet**
5. **Anota la IP**

### Paso 2 - Setup Automático (1 Comando)

**Conecta al servidor:**
```bash
ssh root@YOUR_DROPLET_IP
```

**Ejecuta el instalador automático:**
```bash
curl -fsSL https://raw.githubusercontent.com/alexprotocolo4x/ib-analytics-platform/main/scripts-production/setup_server.sh | bash
```

Este script instala TODO automáticamente:
- PostgreSQL 14 + TimescaleDB
- Python + dependencias
- Crea base de datos
- Descarga código
- Configura entorno

**Tiempo:** 5-10 minutos

---

## 📥 Importar Datos

### Subir archivo al servidor

**Desde tu Mac:**
```bash
# Si tienes el ZIP
scp "Deals test1.htm.zip" root@YOUR_IP:/opt/ib-analytics/data/

# Si ya está extraído
scp "Deals test1.htm" root@YOUR_IP:/opt/ib-analytics/data/
```

### Importar a base de datos

**En el servidor:**
```bash
# Activar entorno
source /opt/ib-analytics/activate.sh

# Si es ZIP, extraer primero
cd /opt/ib-analytics/data
unzip "Deals test1.htm.zip"

# Importar (20-40 min para archivo de 2GB)
python3 scripts/import_deals.py /opt/ib-analytics/data/Deals\ test1.htm
```

**Output esperado:**
```
🚀 IB Analytics - Importación a PostgreSQL
============================================================
📁 Archivo: Deals test1.htm
💾 Tamaño: 1957.7 MB
📦 Batch size: 10,000 filas
============================================================

🔌 Conectando a PostgreSQL...
✅ Conexión establecida

📖 Leyendo archivo...
  📋 Headers: 25 columnas detectadas
  1,000,000 líneas | 45,230 deals | 5.2% completado
  2,000,000 líneas | 92,150 deals | 10.8% completado
  ...
  
✅ IMPORTACIÓN COMPLETADA
Deals importados:     1,234,567
Tiempo total:         1823.4s (30.4 min)
Velocidad:            677 deals/segundo
```

---

## 📊 Consultas

### Resumen General
```bash
python3 scripts/query_analytics.py summary
```

Output:
```
📊 RESUMEN GENERAL
============================================================
Total Deals:          1,234,567
Cuentas Únicas:       45,678
Volumen Total:        12,345.67 lotes
Revenue Bruto:        $308,641.75
P&L Total:            $456,789.12
Profit Factor:        2.34
Margen Neto (70%):    $216,049.23

🎯 TOP 10 SÍMBOLOS
============================================================
 1. JP225        -   5,432.10 lotes - Revenue: $135,803
 2. XAUUSDc      -   3,210.50 lotes - Revenue: $80,263
 ...
```

### Exportar a Excel
```bash
python3 scripts/query_analytics.py export /tmp/mayo_2026.xlsx
```

### Descargar a tu Mac
```bash
# Desde tu Mac
scp root@YOUR_IP:/tmp/mayo_2026.xlsx ~/Desktop/
```

---

## 🔄 Procesar Múltiples Archivos (Mes Completo)

```bash
# En el servidor
source /opt/ib-analytics/activate.sh
cd /opt/ib-analytics/data

# Importar todos los archivos
for file in *.htm; do
    echo "Procesando: $file"
    python3 /opt/ib-analytics/production/scripts/import_deals.py "$file"
done
```

**Todos los datos se acumulan en la misma base de datos.**

Luego exportas:
```bash
python3 scripts/query_analytics.py export /tmp/mayo_completo.xlsx
```

---

## 💡 Consultas SQL Personalizadas

```bash
# Conectar a PostgreSQL
psql postgresql://ib_admin:PASSWORD@localhost:5432/ib_analytics
```

**Ejemplos:**

**Revenue por día:**
```sql
SELECT 
    DATE(time) as date,
    COUNT(*) as deals,
    SUM(volume) as volume,
    SUM(volume) * 25.0 as revenue
FROM deals
GROUP BY DATE(time)
ORDER BY date DESC;
```

**Top cuentas por semana:**
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

## 💰 Costos

**DigitalOcean Droplet 8GB:**
- $24/mes (o $0.036/hora)
- Incluye 1TB transfer
- Puedes destruir cuando no lo uses (facturas por hora)

**Alternativas:**
- **4GB RAM** ($12/mes) - Para archivos <1GB
- **16GB RAM** ($48/mes) - Para archivos >5GB

---

## 🎯 Ventajas vs Scripts Locales

| Aspecto | Script Local | Sistema Producción |
|---------|--------------|-------------------|
| **Tamaño max** | ~500MB | Ilimitado |
| **Velocidad** | 10-30 min | 20-40 min (pero sin crashes) |
| **Consultas** | Re-procesar cada vez | Instantáneas |
| **Histórico** | Archivos separados | Base de datos unificada |
| **Multi-mes** | Manual, tedioso | Automático |
| **Dashboard** | No | Sí (próximamente) |
| **API** | No | Sí (próximamente) |

---

## 📞 Próximos Pasos (Opcionales)

### 1. Dashboard Web
FastAPI + Next.js para visualización en tiempo real:
- Gráficas interactivas
- Filtros dinámicos
- Export automático

**Tiempo:** 1-2 días de desarrollo

### 2. API REST
Endpoints para integraciones externas:
```
GET /api/summary
GET /api/symbols?limit=50
GET /api/accounts/{login}/stats
GET /api/deals?start_date=2026-05-01&end_date=2026-05-31
```

### 3. Alertas Automáticas
Notificaciones cuando:
- Account con balance negativo
- Volumen diario por debajo de threshold
- Nuevos símbolos detectados

---

## 🆘 Soporte

**Documentación completa:** `/opt/ib-analytics/production/README-PRODUCTION.md`

**Logs de importación:**
```sql
SELECT * FROM import_logs ORDER BY started_at DESC;
```

**GitHub:** https://github.com/alexprotocolo4x/ib-analytics-platform

---

## ✅ Resumen

**Lo que tienes ahora:**
1. ✅ Sistema que procesa archivos de **cualquier tamaño**
2. ✅ Base de datos PostgreSQL optimizada
3. ✅ Consultas instantáneas sobre millones de deals
4. ✅ Export automático a Excel
5. ✅ Código en GitHub (listo para colaboración)

**Costo:** $24/mes

**Siguiente paso:** Crear el droplet y ejecutar el script de setup (20 minutos)

**¿Listo para deployar?**
