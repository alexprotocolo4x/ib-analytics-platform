# IB Analytics Platform

Plataforma de análisis de profundidad de IBs para TAG Markets.

## Stack

**Backend:**
- FastAPI (Python 3.9+)
- PostgreSQL / SQLite
- BeautifulSoup4 (HTML parsing)
- Pandas (data processing)

**Frontend:**
- React 18
- TypeScript
- Vite
- Recharts (visualización)
- Aurum theme (negro + oro)

## Estructura

```
ib-analytics-platform/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   ├── api/       # Endpoints
│   │   ├── models/    # Database models
│   │   ├── parsers/   # MT5 HTML parser
│   │   └── services/  # Business logic
│   ├── requirements.txt
│   └── README.md
├── frontend/          # React + TypeScript
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.tsx
│   ├── package.json
│   └── README.md
└── README.md
```

## Features

### Fase 1 (Actual):
- ✅ Upload HTML de MT5 Administrator
- ✅ Upload Excel con lista de cuentas
- ✅ Parser de HTML a datos estructurados
- ✅ Cálculo de métricas principales
- ✅ Dashboard con KPIs
- ✅ Tabla de cuentas con drill-down
- ✅ Export CSV/Excel

### Fase 2 (Futuro):
- Detección de fraude
- Análisis de riesgo
- Cohort analysis
- Histórico de datos

## Quick Start

### Backend:
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Datos

**Input:**
1. HTML export de MT5 Administrator (deals)
2. Excel con cuentas a analizar (columna: Login)

**Output:**
- Dashboard con métricas calculadas
- Tabla de cuentas con estadísticas
- Reportes exportables

---

**Desarrollado por:** Viernes  
**Cliente:** TAG Markets (Alex Lopez)  
**Fecha inicio:** 2026-05-19
