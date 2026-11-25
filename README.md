# IB Analytics

Plataforma que procesa los reportes de operaciones de un broker y mide la profundidad y el rendimiento de cada red de introducing brokers: niveles, clientes, volumen y actividad.

## Marca blanca

Puede implementarse para cualquier broker que exporte sus reportes de operaciones.

Para implementarlo con su marca, escríbanos a contact@alfaxisgroup.com.

## Funciones

- Carga de reportes en HTML y Excel.
- Reconstrucción de la red de cada IB y sus niveles.
- Métricas de volumen, clientes activos y actividad por red.
- Panel con gráficos.

## Stack

| Capa | Tecnología |
| --- | --- |
| API | FastAPI (Python) |
| Procesamiento | Pandas y BeautifulSoup |
| Base de datos | PostgreSQL o SQLite |
| Panel | React, TypeScript, Vite y Recharts |

## Desarrollo local

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Las cadenas de conexión y credenciales se configuran por variables de entorno.

---

Desarrollado por **Alfaxis** · [alfaxisgroup.com](https://alfaxisgroup.com) · contact@alfaxisgroup.com

© 2026 Alfaxis. Todos los derechos reservados. Software propietario: su uso, copia o distribución requiere autorización escrita de Alfaxis.
