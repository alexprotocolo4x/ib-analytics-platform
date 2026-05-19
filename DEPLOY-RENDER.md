# Deploy IB Analytics en Render.com

## Paso 1: Sube a GitHub

```bash
# Crear repo en GitHub (https://github.com/new)
# Nombre: ib-analytics-platform
# Público

# Luego conecta el repo:
cd ~/.openclaw/workspace/ib-analytics-platform
git remote add origin https://github.com/TU-USUARIO/ib-analytics-platform.git
git push -u origin main
```

## Paso 2: Deploy en Render

1. Ve a https://render.com y haz login con GitHub
2. Click "New +" → "Web Service"
3. Conecta tu repositorio `ib-analytics-platform`
4. Configuración:
   - **Name**: ib-analytics-platform
   - **Region**: Frankfurt (más cercano a Dubai)
   - **Branch**: main
   - **Root Directory**: (dejar vacío)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `cd backend && python main.py`
   - **Instance Type**: Free

5. Click "Create Web Service"

## Paso 3: Espera 2-3 minutos

Render te dará una URL tipo: `https://ib-analytics-platform.onrender.com`

## Listo!

La URL será estable, sin límites de upload, y no se cae.
