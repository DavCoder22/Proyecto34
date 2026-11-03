# Desplegar el dashboard HTML en Northflank (igual que local)

Esta es la opción recomendada para ver en la nube **exactamente** el mismo dashboard que se abre en local:

- Mapa SVG fijo de las 24 provincias.
- Provincias clicables para filtrar todos los gráficos.
- Sin zoom, sin mapas interactivos y sin depender de Mapbox.
- Mismas tarjetas, pastel, rankings y gráficos que la ejecución local.

## Arquitectura

```text
Servicio proyecto34-dashboard (Dockerfile.dashboard, puerto 8080)
  └── build: ejecuta el ETL y genera dashboard.html
  └── runtime: nginx sirve dashboard.html
```

No requiere Neon ni variables de entorno. La imagen ejecuta el ETL con los datos del repositorio y genera el HTML durante el build.

## Paso 1. Subir los cambios a GitHub

Northflank construye desde GitHub. Verifica que el commit esté en `main`:

```bash
git add docker/Dockerfile.dashboard docker/nginx-dashboard.conf deploy/NORTHFLANK_DASHBOARD.md README.md
git commit -m "feat: desplegar dashboard HTML en Northflank"
git push origin main
```

## Paso 2. Crear el servicio en Northflank

1. En el proyecto `proyecto34`: **Create new → Service → Combined service**.
2. Nombre: `proyecto34-dashboard`.
3. Fuente: **Git repository**.
4. Repositorio: `DavCoder22/Proyecto34`.
5. Rama: `main`.
6. Build type: **Dockerfile**.
7. Dockerfile path: `docker/Dockerfile.dashboard`.
8. Build context: `.` (raíz del repositorio).
9. Networking:
   - Puerto: `8080`.
   - Protocolo: `HTTP`.
   - Accesibilidad: `Public`.
10. Health check:
    - Protocolo: `HTTP`.
    - Path: `/`.
    - Puerto: `8080`.
11. Recursos recomendados: `0.5 vCPU` y `1 GB` de RAM.
12. Crea el servicio y espera el build.

> Si tu plan solo permite un servicio y prefieres reemplazar Superset, edita el servicio existente `proyecto34-superset`: cambia el Dockerfile a `docker/Dockerfile.dashboard` y el puerto público a `8080`. Dejará de servir Superset y servirá el dashboard HTML.

## Paso 3. Abrir el dashboard

Usa la URL pública del servicio `proyecto34-dashboard`. Debe verse igual que:

```bash
python 04_dashboard/build_dashboard.py
python -m http.server 8000 --directory 04_dashboard
# http://localhost:8000/dashboard.html
```

## Actualizar el dashboard

Cada vez que cambien los datos, el ETL o los gráficos:

1. Haz commit y push a `main`.
2. En Northflank, redespliega `proyecto34-dashboard`.
3. El build vuelve a ejecutar el ETL y regenera `dashboard.html`.

## Por qué no usar Superset para este mapa

Superset usa `deck.gl`/Mapbox para su mapa provincial. Eso implica:

- Requiere un token de Mapbox (`MAPBOX_API_KEY`).
- El mapa es interactivo (zoom y desplazamiento).
- Las provincias no funcionan como filtro global del dashboard.

El dashboard HTML usa un SVG embebido: no necesita token, es fijo y las provincias sí filtran todos los gráficos. Superset queda disponible como dashboard alternativo con tarjetas, evolución, ranking provincial y pastel.
