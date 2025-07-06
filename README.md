# Proyecto Mi Mapa App

Este repositorio contiene una aplicación web híbrida (desktop y móvil) que integra:

* **Backend**: API en Python con FastAPI que actúa de proxy para OSRM (ruteo) y Nominatim (geocoding).
* **Frontend**: SPA con Quasar (Vue 3 Options API) y Leaflet (@vue-leaflet/vue-leaflet) para mostrar mapas y rutas.

---

## 📁 Estructura del proyecto

```
mi-mapa-app/
├── backend/        # Código de la API FastAPI
│   ├── main.py     # Endpoints: /api/route, /api/geocode
│   ├── requirements.txt
│   └── venv/       # Entorno virtual (excluido con .gitignore)
├── frontend/       # App Quasar + Vue 3 + Leaflet
│   ├── src/
│   │   └── pages/
│   │       └── IndexPage.vue
│   ├── quasar.conf.js
│   └── package.json
└── .gitignore      # Ignora venv/, node_modules/, dist/, etc.
```

---

## 🔧 Prerrequisitos

* Git
* Node.js ≥ 16 y npm
* Python ≥ 3.9 (o 3.13) y pip
* OSRM corriendo en `http://localhost:5000`

---

## 🚀 Instalación y ejecución

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPO>
cd mi-mapa-app
```

### 2. Configurar el backend (FastAPI)

```bash
cd backend
python3 -m venv venv             # crea entorno virtual con Python 3.x
source venv/bin/activate         # Linux/macOS
# venv\Scripts\activate        # Windows

# Crear requirements.txt con:
# fastapi
# uvicorn[standard]
# httpx
pip install --upgrade pip
pip install -r requirements.txt

# Arrancar el servidor en modo desarrollo
tuvicorn main:app --reload --port 8000
```

El backend estará disponible en `http://localhost:8000` y la documentación automática en `http://localhost:8000/docs`.

### 3. Configurar el frontend (Quasar + Leaflet)

```bash
cd ../frontend
npm install                       # instala dependencias del proyecto
npm uninstall vue2-leaflet        # eliminar wrapper Vue2
npm install leaflet @vue-leaflet/vue-leaflet

# Levantar el servidor de desarrollo
quasar dev
```

El frontend se sirve en `http://localhost:8080`.

---

## ⚙️ Uso básico

1. Abrir `http://localhost:8000/docs` para probar manualmente los endpoints `/api/route` y `/api/geocode`.
2. Abrir `http://localhost:8080` y en la interfaz introduzca coordenadas de origen y destino (formato `lon,lat`), luego haga clic en **"Calcular ruta"**.
3. Verá el mapa centrado y la ruta dibujada.

