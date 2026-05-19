# IB Analytics Platform - Quick Start

## 🚀 Arrancar el Proyecto

### 1. Backend (Terminal 1)

```bash
cd ~/.openclaw/workspace/ib-analytics-platform/backend

# Instalar dependencias (solo primera vez)
pip3 install -r requirements.txt

# Arrancar servidor
python3 -m uvicorn app.main:app --reload --port 8000
```

Backend corriendo en: **http://localhost:8000**

### 2. Frontend (Terminal 2)

```bash
cd ~/.openclaw/workspace/ib-analytics-platform/frontend

# Instalar dependencias (solo primera vez)
npm install

# Arrancar dev server
npm run dev
```

Frontend corriendo en: **http://localhost:5173**

---

## 📋 Uso

1. **Abrir** http://localhost:5173 en tu navegador

2. **Subir archivo HTML** de MT5 Administrator:
   - Exportado desde MT5 Administrator
   - Formato: HTML
   - Contiene: Deals del período

3. **Subir archivo Excel** con cuentas:
   - Formato: .xlsx o .xls
   - Debe tener columna llamada **"Login"**
   - Ejemplo:
     ```
     Login
     50533467
     50733133
     50582926
     ...
     ```

4. **Ver resultados:**
   - KPIs calculados automáticamente
   - Tabla con métricas por cuenta
   - Listo para análisis

---

## 🧪 Test Rápido

Puedes probar el backend directamente:

```bash
cd backend
python3 test_backend.py
```

Esto procesará el HTML de ejemplo y mostrará las métricas calculadas.

---

## 📡 API Endpoints

- `POST /api/upload/mt5-html` - Subir HTML de MT5
- `POST /api/upload/accounts-excel` - Subir Excel de cuentas
- `GET /api/upload/status` - Ver estado de uploads
- `GET /api/analytics/kpis` - Obtener KPIs calculados
- `GET /api/analytics/accounts` - Métricas por cuenta
- `GET /api/analytics/symbols` - Métricas por símbolo
- `GET /api/analytics/deals` - Lista de deals (paginado)
- `DELETE /api/upload/clear` - Limpiar datos

Documentación interactiva: **http://localhost:8000/docs**

---

## 🎨 Tema Visual

- **Colores:** Negro profundo + Oro (Aurum theme)
- **Tipografía:** 
  - Headers: Cormorant Garamond
  - Body: Inter
  - Números: JetBrains Mono

---

## ⚙️ Configuración

### Variables de Entorno

**Backend:** No requiere configuración adicional (usa in-memory storage)

**Frontend:** `.env.development`
```
VITE_API_URL=http://localhost:8000
```

---

## 📊 Métricas Calculadas

- **Lotes Totales** - Volumen total de trades cerrados
- **Revenue Bruto** - $25 × lotes (configurable)
- **Pago al IB** - $17 × lotes (configurable)
- **Margen Neto** - Revenue - Pago IB
- **P&L Clientes** - Suma de profits/losses
- **Profit Factor** - Gross Profit / |Gross Loss|
- **Win Rate** - % de trades ganadores
- **Cuentas Activas** - Cuentas con al menos 1 trade

---

## 🐛 Troubleshooting

### Backend no arranca

```bash
# Verificar Python
python3 --version  # Debe ser 3.9+

# Reinstalar dependencias
pip3 install -r requirements.txt --force-reinstall
```

### Frontend no arranca

```bash
# Limpiar y reinstalar
rm -rf node_modules package-lock.json
npm install
```

### CORS Error

Si ves errores de CORS, verifica que el backend esté corriendo en puerto 8000.

---

**Desarrollado por:** Viernes  
**Cliente:** TAG Markets (Alex Lopez)  
**Fecha:** 2026-05-19
