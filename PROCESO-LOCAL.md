# Procesamiento Local - IB Analytics

## Para archivos HTML grandes (>500 MB)

### Paso 1: Verificar dependencias instaladas

```bash
cd ~/.openclaw/workspace/ib-analytics-platform
pip3 install -r requirements.txt
```

### Paso 2: Procesar el archivo HTML

**Sintaxis básica:**
```bash
python3 process_local.py <ruta_archivo_html>
```

**Con filtro de duración (excluye scalping < 3 minutos):**
```bash
python3 process_local.py <ruta_archivo_html> 3
```

### Ejemplos

```bash
# Procesar archivo sin filtros
python3 process_local.py ~/Desktop/deals_mayo.html

# Procesar con filtro de 3 minutos
python3 process_local.py ~/Desktop/deals_mayo.html 3

# Procesar archivo de 2GB
python3 process_local.py ~/Downloads/mt5_deals_full.html
```

### Resultado

El script generará:
1. **Resumen en consola** con todas las métricas
2. **Archivo Excel** con 4 hojas:
   - Resumen General
   - Por Símbolo (top 20)
   - Por Cuenta (top 50)
   - Deals Filtrados (si se aplicó filtro)

**Nombre del archivo:** `<nombre_original>_analytics.xlsx`

### Ventajas

✅ Sin límites de tamaño (procesa archivos de GB)  
✅ Procesamiento local (máxima velocidad)  
✅ No requiere internet  
✅ No depende de servicios externos  
✅ Resultados en 5-10 minutos para 2GB

### Tiempo estimado

- 100 MB → ~1 minuto
- 500 MB → ~3 minutos
- 1 GB → ~5 minutos
- 2 GB → ~10 minutos

### Troubleshooting

**Error: "No module named 'app'"**
```bash
# Ejecuta desde el directorio correcto
cd ~/.openclaw/workspace/ib-analytics-platform
```

**Error: "ModuleNotFoundError: No module named 'pandas'"**
```bash
pip3 install -r requirements.txt
```

**Memoria insuficiente**
Si tu máquina tiene < 8 GB RAM y el archivo es muy grande:
```bash
# Dividir el archivo HTML en partes más pequeñas
# O procesar en una máquina con más RAM
```
