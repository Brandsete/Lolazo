# RiftTracker ⚡

Plataforma integral de estadísticas, analítica y seguimiento de partidas para **League of Legends** construida con arquitectura moderna y asíncrona: **FastAPI** en el backend y **React + Vite** en el frontend.

Diseñada con un estricto enfoque en **seguridad, robustez y resiliencia**, integrando caché en memoria con expiración configurable (TTL), tratamiento centralizado y diferenciado de errores de Riot Games, límites de concurrencia y consultas (rate limiting), reintentos con respaldo exponencial y protección contra fuga de credenciales.

---

## 📋 Tabla de Contenidos
- [Requisitos](#-requisitos)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Instalación y Configuración](#-instalación-y-configuración)
- [Configuración de Variables de Entorno (.env)](#-configuración-de-variables-de-entorno-env)
- [Obtención y Renovación de la Clave de Riot Games](#-obtención-y-renovación-de-la-clave-de-riot-games)
- [Comandos de Ejecución en Windows](#-comandos-de-ejecución-en-windows)
- [Comandos de Pruebas y Calidad](#-comandos-de-pruebas-y-calidad)
- [Endpoints Disponibles en la API](#-endpoints-disponibles-en-la-api)
- [Ejemplos de Uso](#-ejemplos-de-uso)
- [Errores Frecuentes y Soluciones](#-errores-frecuentes-y-soluciones)
- [Limitaciones Conocidas](#-limitaciones-conocidas)
- [Instrucciones para Despliegue en Producción](#-instrucciones-para-despliegue-en-producción)

---

## 💻 Requisitos

### Entorno de Desarrollo
- **Sistema Operativo**: Windows 10/11, Linux o macOS (Probado y optimizado en Windows).
- **Python**: Versión 3.11 o superior (verificado con Python 3.12).
- **Node.js**: Versión 18.x o superior con **npm** (v9 o superior).
- **Git**: Para control de versiones.

---

## 📁 Estructura del Proyecto

```text
rifttracker/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── health.py        # GET /api/health
│   │   │       │   ├── matches.py       # GET /api/matches/{match_id}
│   │   │       │   ├── players.py       # GET /api/players/... (perfil, stats, campeones, roles, partidas)
│   │   │       │   ├── regions.py       # GET /api/regions y /api/regions/{id}
│   │   │       │   └── riot.py          # GET /api/riot/status
│   │   │       └── router.py            # Enrutador consolidado API v1
│   │   ├── core/
│   │   │   ├── cache.py                 # Caché en memoria con TTL configurable y límites de tamaño
│   │   │   ├── config.py                # Configuración tipada con Pydantic Settings
│   │   │   ├── exceptions.py            # Jerarquía de excepciones y manejadores seguros
│   │   │   ├── logging_config.py        # Filtro de seguridad que censura credenciales en logs
│   │   │   ├── rate_limiter.py          # Limitador de peticiones por IP (Sliding Window)
│   │   │   └── validation.py            # Validación estricta de Riot ID, regiones, colas y partidas
│   │   ├── schemas/                     # Modelos de datos y respuestas JSON Pydantic
│   │   ├── services/                    # Capa de servicios e integración externa
│   │   │   ├── ddragon_service.py       # CDN oficial de Data Dragon (iconos de campeones y perfiles)
│   │   │   ├── match_service.py         # Match-V5, parseo de rendimiento y caché de partidas
│   │   │   ├── player_service.py        # Account-V1, Summoner-V4 y League-V4
│   │   │   ├── region_service.py        # Mapeo oficial de Plataforma a Clúster regional
│   │   │   ├── riot_client.py           # Cliente HTTP asíncrono con timeouts, reintentos y semáforo
│   │   │   └── stats_service.py         # Fórmulas analíticas (KDA, CS/min, oro, objetivos)
│   │   └── main.py                      # Instancia FastAPI, CORS restrictivo y cabeceras de seguridad
│   ├── tests/                           # Suite de pruebas unitarias y de integración con Pytest
│   ├── pyproject.toml                   # Configuración de herramientas (Pytest, Ruff)
│   └── requirements.txt                 # Dependencias Python
├── frontend/
│   ├── src/
│   │   ├── components/                  # Componentes modulares React (Tarjetas, Historial, Métricas)
│   │   ├── services/
│   │   │   ├── api.js                   # Cliente HTTP centralizado del frontend
│   │   │   └── mockData.js              # Datos simulados de demostración cuando no hay clave activa
│   │   ├── App.jsx                      # Orquestador principal de estado y vistas
│   │   ├── index.css                    # Estilos CSS, diseño responsive y modo oscuro
│   │   └── main.jsx                     # Punto de montaje React
│   ├── package.json                     # Dependencias de frontend
│   └── vite.config.js                   # Proxy de desarrollo `/api` -> `http://127.0.0.1:8000`
├── .env.example                         # Plantilla documentada de variables de entorno
├── package.json                         # Scripts para automatización monorepo
└── README.md                            # Documentación integral
```

---

## ⚙️ Configuración de Variables de Entorno (.env)

Copia el archivo `.env.example` para crear tu `.env` local en la raíz del proyecto o dentro de `backend/`:

```powershell
cp .env.example .env
```

### Variables disponibles

| Variable | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `RIOT_API_KEY` | String | `RGAPI-00000000...` | Clave oficial de Riot Games Developer Portal. |
| `BACKEND_HOST` | String | `127.0.0.1` | Dirección IP de escucha del servidor Uvicorn. |
| `BACKEND_PORT` | Entero | `8000` | Puerto TCP del backend. |
| `FRONTEND_ORIGIN` | String | `http://localhost:5173` | Origen frontend autorizado para CORS. |
| `ALLOWED_ORIGINS` | String | `http://localhost:5173,http://127.0.0.1:5173` | Lista de orígenes CORS permitidos (separados por coma). |
| `CACHE_TTL_SECONDS` | Entero | `300` | TTL por defecto de caché en memoria (segundos). |
| `CACHE_TTL_PROFILE_SECONDS` | Entero | `300` | TTL para perfiles de invocador y cuentas (5 minutos). |
| `CACHE_TTL_LEAGUE_SECONDS` | Entero | `120` | TTL para clasificaciones competitivas (2 minutos). |
| `CACHE_TTL_MATCH_SECONDS` | Entero | `3600` | TTL para partidas concluidas (inmutables, 1 hora). |
| `CACHE_TTL_STATS_SECONDS` | Entero | `300` | TTL para estadísticas agregadas (5 minutos). |
| `CACHE_MAX_ENTRIES` | Entero | `2000` | Cantidad máxima de elementos en caché antes de desalojo. |
| `RIOT_CONNECT_TIMEOUT` | Float | `5.0` | Tiempo de espera de conexión con Riot Games (segundos). |
| `RIOT_READ_TIMEOUT` | Float | `10.0` | Tiempo de espera de lectura con Riot Games (segundos). |
| `RIOT_MAX_CONCURRENT_REQUESTS` | Entero | `10` | Límite de peticiones simultáneas hacia la API de Riot. |
| `RIOT_MAX_RETRIES` | Entero | `2` | Número máximo de reintentos en fallos transitorios (5xx/red). |
| `RIOT_BACKOFF_FACTOR` | Float | `0.5` | Factor base de respaldo exponencial para reintentos. |
| `RIOT_MAX_RETRY_DELAY` | Float | `3.0` | Tiempo máximo de espera entre reintentos automáticos. |
| `RATE_LIMIT_PER_MINUTE` | Entero | `60` | Máximo de peticiones por minuto permitidas por IP. |
| `RATE_LIMIT_ENABLED` | Boolean | `true` | Activa o desactiva el limitador de peticiones en backend. |

> 🔒 **Seguridad crítica**: Nunca subas el archivo `.env` con una clave real a repositorios públicos o compartidos.

---

## 🔑 Obtención y Renovación de la Clave de Riot Games

Para consultar datos reales de League of Legends en vivo:

1. **Registrarse / Iniciar Sesión**:
   - Ingresa en [developer.riotgames.com](https://developer.riotgames.com/) con tu cuenta de Riot Games.
2. **Generar la Development API Key**:
   - En el Dashboard principal, haz clic en **Generate Personal API Key** o **Renew**.
   - La clave comienza con el prefijo `RGAPI-` (ej. `RGAPI-XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX`).
3. **Pegar en el archivo `.env`**:
   ```env
   RIOT_API_KEY=RGAPI-XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
   ```
4. **Renovación periódica**:
   - Por política de seguridad oficial de Riot Games, las claves personales de desarrollo **caducan cada 24 horas**. Si expira, simplemente vuelve al portal, haz clic en "Regenerate API Key", actualiza el `.env` y reinicia el backend.

---

## 🚀 Comandos de Ejecución en Windows

Para ejecutar el proyecto en tu máquina local, utiliza dos terminales separadas de PowerShell:

### Terminal 1: Backend (FastAPI + Uvicorn)
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
* Backend activo en: `http://127.0.0.1:8000`
* Documentación Swagger interactiva: `http://127.0.0.1:8000/docs`
* Documentación ReDoc: `http://127.0.0.1:8000/redoc`

### Terminal 2: Frontend (React + Vite)
```powershell
cd frontend
npm install
npm run dev
```
* Aplicación web disponible en: `http://localhost:5173`

---

## 🧪 Comandos de Pruebas y Calidad

### Backend (Pytest y Ruff)
```powershell
# Ejecutar la suite completa de pruebas unitarias y de integración
backend\.venv\Scripts\python -m pytest backend/tests -v

# Ejecutar el linter estático
backend\.venv\Scripts\python -m ruff check backend

# Formatear código
backend\.venv\Scripts\python -m ruff format backend
```

### Frontend (Compilación y Auditoría)
```powershell
# Compilar bundle de producción
npm --prefix frontend run build

# Auditoría de seguridad de paquetes npm
npm audit --prefix frontend
```

---

## 🌐 Endpoints Disponibles en la API

Todos los endpoints están montados tanto en `/api` como en `/api/v1`:

### 1. Sistema y Diagnóstico
- `GET /api/health`: Estado de operatividad del backend y parámetros activos de caché.
- `GET /api/riot/status`: Informa si la clave de Riot Games está configurada o en modo placeholder sin revelar su valor.
- `GET /api/regions`: Lista todas las regiones de plataforma (`la1`, `kr`, `na1`, `euw1`, etc.) y sus clústeres (`americas`, `asia`, `europe`, `sea`). Admite filtro `?cluster=americas`.
- `GET /api/regions/{platform_id}`: Consulta los datos y clúster de una plataforma específica.

### 2. Jugadores y Clasificación
- `GET /api/players/{game_name}/{tag_line}?region={region}`:
  - Resuelve el Riot ID a PUUID con **Account-V1**.
  - Obtiene nivel e icono con **Summoner-V4**.
  - Obtiene ligas clasificatorias (Solo/Duo y Flex) con **League-V4**.
- `GET /api/players/{game_name}/{tag_line}/stats?region={region}&queue={queue}&matches={matches}`:
  - Análisis estadístico consolidado (Victorias, derrotas, porcentaje de victoria, KDA promedio, CS por minuto, oro y visión).
- `GET /api/players/{game_name}/{tag_line}/champions?region={region}&matches={matches}`:
  - Rendimiento por campeón (partidas jugadas, win rate, KDA, CS/min).
- `GET /api/players/{game_name}/{tag_line}/roles?region={region}&matches={matches}`:
  - Distribución de posiciones (TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY) y su win rate.
- `GET /api/players/{game_name}/{tag_line}/matches?region={region}&count={count}`:
  - Historial de partidas recientes con KDA individual, objetos, hechizos y duración.

### 3. Partidas
- `GET /api/matches/{match_id}?region={region}`:
  - Detalle completo oficial de la partida mediante **Match-V5**.

---

## 💡 Ejemplos de Uso

### Ejemplo 1: Consulta de Salud
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health"
```
**Respuesta:**
```json
{
  "status": "healthy",
  "service": "RiftTracker API",
  "version": "0.1.0",
  "timestamp": "2026-10-18T18:52:57Z",
  "cache_ttl_seconds": 300,
  "max_matches": 20
}
```

### Ejemplo 2: Consulta de Perfil de Jugador
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/players/Josedeodo/LAN?region=la1"
```

### Ejemplo 3: Manejo Seguro de Clave Faltante o Expirada (HTTP 403)
Si no se ha configurado una clave personal, la API responde con un formato estándar y consistente:
```json
{
  "detail": "Riot Games API key is not configured or using default placeholder. Please configure RIOT_API_KEY in your .env file.",
  "error_code": "RIOT_API_AUTH_ERROR",
  "status_code": 403,
  "timestamp": "2026-10-18T18:52:57Z"
}
```

---

## ⚠️ Errores Frecuentes y Soluciones

1. **Error HTTP 403 (RIOT_API_AUTH_ERROR)**:
   - **Causa**: La clave `RIOT_API_KEY` en `.env` tiene el valor por defecto (`RGAPI-00000000...`) o han pasado más de 24 horas y ha caducado.
   - **Solución**: Visita [developer.riotgames.com](https://developer.riotgames.com/), renueva tu clave personal y pégala en el `.env`.
2. **Error HTTP 400 (INVALID_REGION)**:
   - **Causa**: La plataforma especificada (ej. `moon1`) no existe en League of Legends.
   - **Solución**: Utiliza una plataforma válida (`la1`, `la2`, `na1`, `br1`, `euw1`, `eun1`, `kr`, `jp1`, etc.).
3. **Error HTTP 400 (INVALID_RIOT_ID)**:
   - **Causa**: El nombre del Riot ID contiene caracteres especiales no admitidos o supera 24 caracteres.
   - **Solución**: Ingresa el nombre oficial de Riot ID sin símbolos extraños.
4. **Error HTTP 404 (PLAYER_NOT_FOUND)**:
   - **Causa**: La combinación de `game_name` y `tag_line` no está registrada en los servidores de Riot en esa región.
   - **Solución**: Confirma el nombre y tag en el cliente de Riot Games.
5. **Error HTTP 429 (RATE_LIMIT_EXCEEDED)**:
   - **Causa**: Se han enviado más de 60 peticiones en 1 minuto desde la misma IP o la clave de Riot superó su límite oficial.
   - **Solución**: Espera los segundos indicados en la cabecera `Retry-After` de la respuesta.

---

## 📌 Limitaciones Conocidas

- **Duración de Claves Gratuitas**: Las claves personales de desarrollo de Riot expiran cada 24 horas.
- **Límites de Tasa de Riot Games**: Las claves personales tienen un límite estricto de 20 peticiones por segundo y 100 peticiones cada 2 minutos. Para mitigar esto, RiftTracker incluye una caché en memoria y un semáforo de concurrencia.
- **Partidas Históricas en Modos Temporales**: Ciertos modos temporales o partidas muy antiguas pueden omitir datos de objetivos detallados en el payload de Match-V5; RiftTracker maneja estos datos de forma segura sin generar fallos en el cálculo.

---

## 🚢 Instrucciones para Despliegue en Producción

Si se decide desplegar la aplicación posteriormente:

1. **Backend**:
   - Desplegar en cualquier servidor Linux (Ubuntu/Debian) o servicio PaaS (Render, Railway, Fly.io, AWS Elastic Beanstalk).
   - Utilizar Gunicorn con workers de Uvicorn:
     ```bash
     pip install -r backend/requirements.txt
     gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
     ```
   - Configurar variables de entorno seguras (`RIOT_API_KEY`, `FRONTEND_ORIGIN`, etc.) en el panel del proveedor.
2. **Frontend**:
   - Generar el bundle de producción optimizado:
     ```bash
     cd frontend
     npm run build
     ```
   - Alojar la carpeta `frontend/dist` en cualquier servicio estático de alto rendimiento como **Vercel**, **Netlify**, **Cloudflare Pages** o **AWS S3 + CloudFront**.
   - En el frontend, configurar la variable de entorno `VITE_API_BASE_URL` apuntando al dominio de producción del backend.
