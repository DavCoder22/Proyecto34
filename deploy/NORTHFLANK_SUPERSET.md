# Desplegar Apache Superset en Northflank

Guía paso a paso para publicar el dashboard **Sales Analytics** de la PoC en Northflank.

## Arquitectura en Northflank

```text
PostgreSQL addon  ->  Job ETL (carga el DW)  ->  Servicio Superset (dashboard)
```

El job ETL crea las tablas `dim_*`, `fact_ventas` y las vistas `v_ventas_*` en PostgreSQL. El servicio Superset se conecta a esas vistas y crea automáticamente el dashboard con sus cuatro gráficos.

## Paso 0. Subir los archivos a GitHub

Northflank construye desde el repositorio, no desde tu computadora. En este momento hay archivos del despliegue que aún no están versionados. Súbelos antes de crear los servicios:

```bash
git add docker/superset docker/Dockerfile.etl 04_dashboard/kpi_views_postgres.sql 03_dw/schema.sql 02_etl/load.py requirements.txt
git commit -m "feat: preparar despliegue de Superset en Northflank"
git push origin main
```

Archivos mínimos que deben existir en la rama `main`:

- `docker/superset/Dockerfile`
- `docker/superset/entrypoint.sh`
- `docker/superset/superset_config.py`
- `docker/superset/bootstrap_dashboard.py`
- `docker/Dockerfile.etl`
- `04_dashboard/kpi_views_postgres.sql`
- `03_dw/schema.sql`
- `02_etl/load.py`
- `requirements.txt`

Sin esos archivos, el build de Northflank falla o el dashboard no se crea.

## Paso 1. Crear el proyecto

1. Entra a [northflank.com](https://northflank.com).
2. Crea un proyecto, por ejemplo `poc-analisis-comercial`.
3. Selecciona la región más cercana.

## Paso 2. Crear el addon PostgreSQL

1. En el proyecto: **Create new → Addon → PostgreSQL**.
2. Nombre: `poc-postgres`.
3. Versión: 15 o 16.
4. Recursos para Sandbox: 0.2 vCPU y 512 MB de RAM. No actives alta disponibilidad ni acceso público.
5. Crea el addon y espera a que esté **Running/Healthy**.
6. Abre **Connection details** y copia el valor de `POSTGRES_URI`.

Debe verse así:

```text
postgresql+psycopg2://usuario:password@host:5432/basededatos
```

Usa siempre el host interno del addon. No uses `localhost` ni la URL pública para la comunicación entre servicios del mismo proyecto.

### Cómo mantener el addon dentro del plan gratuito

Northflank tiene el plan **Sandbox**, que incluye **2 servicios, 2 jobs y 1 addon**, con hasta **20 USD/mes de recursos** en Northflank Cloud. El precio que muestra el addon es el costo de los recursos; si estás en Sandbox, ese costo se descuenta del crédito de 20 USD.

Para que el despliegue quede dentro del crédito:

| Recurso | Configuración recomendada | Costo aproximado |
|---|---|---:|
| Superset | 0.5 vCPU · 1 GB RAM | ~12,17 USD/mes |
| PostgreSQL | 0.2 vCPU · 512 MB RAM | ~5,47 USD/mes |
| Volumen de Superset | 1 GB | ~0,12 USD/mes |
| Job ETL | Manual, solo cuando cargas datos | Centavos por ejecución |
| **Total** | | **~17,76 USD/mes** |

Con esa combinación quedas por debajo de los 20 USD/mes. Si aun así no quieres usar el addon, salta al **Paso 2B** y usa Neon. Evita estas configuraciones porque superan el crédito:

- Superset con 1 vCPU y 2 GB RAM.
- PostgreSQL con réplicas, alta disponibilidad o más de 1 GB.
- Base de datos pública con IP externa.
- Jobs programados cada hora o servicios adicionales que no uses.

Si el addon sigue mostrando un cobro, revisa primero que tu equipo/proyecto esté en el plan **Sandbox** y no en **Pay as you go**. El precio puede aparecer en la pantalla de configuración, pero el Sandbox lo cubre hasta el límite de 20 USD. Si Northflank solicita una tarjeta, úsala solo para verificación y confirma en **Billing** que el plan activo es Sandbox y que el consumo mensual no supera los 20 USD.

Si necesitas más memoria para Superset, una alternativa es usar un PostgreSQL externo gratuito (por ejemplo, Neon o Supabase) y eliminar el addon de Northflank. En ese caso, el servicio Superset y el job ETL se conectan a la base externa mediante `DATABASE_URL`; el consumo de Northflank baja y el addon deja de existir.

## Paso 2B. Opción sin addon: PostgreSQL gratuito con Neon

Si no quieres pagar el addon de Northflank, usa **Neon**, que tiene un plan gratuito sin tarjeta:

- 1 GB de almacenamiento por proyecto.
- 100 CU-hours de cómputo al mes.
- Hasta 2 CU (≈8 GB de RAM).
- Se suspende automáticamente a los 5 minutos de inactividad.
- Sin tarjeta de crédito.

Pasos:

1. Crea una cuenta en [neon.com](https://neon.com).
2. Crea un proyecto, por ejemplo `poc-analisis-comercial`.
3. Elige la región más cercana a Northflank.
4. En **Connect**, copia la **conexión directa** (sin `-pooler`). Debe verse así:

```text
postgresql+psycopg2://usuario:password@ep-xxxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

5. No actives la conexión pooled para este caso. La conexión directa evita problemas de compatibilidad con Superset y con las migraciones del ETL.
6. En Northflank, crea el secret group y pega esa URL como `DATABASE_URL`. No enlaces ningún addon.
7. Usa el prefijo `postgresql+psycopg2://`. Si Neon te entrega `postgresql://`, cámbialo por `postgresql+psycopg2://`; el código también lo normaliza, pero el prefijo explícito evita el error `No module named 'psycopg'`.
7. Ejecuta el job ETL y luego despliega Superset como se indica en los pasos siguientes.

Con Neon el proyecto de Northflank queda con **1 servicio (Superset) + 1 job (ETL) + 0 addons**, dentro del Sandbox. El único costo es el consumo de Northflank, que debe quedar por debajo de los 20 USD/mes.

Ten en cuenta que Neon suspende el cómputo cuando está inactivo. La primera consulta después de un periodo de inactividad puede tardar unos segundos; es normal. Antes de la exposición, abre el dashboard una vez para despertar Neon y evita que la primera consulta de la demo tenga latencia.

## Paso 3. Crear el grupo de secretos

1. En el proyecto: **Create new → Secret group**.
2. Nombre: `poc-superset-secrets`.
3. Si usas el addon de Northflank, en **Linked addons** selecciona el addon PostgreSQL y enlaza `POSTGRES_URI` con el alias `DATABASE_URL`. Si usas Neon, agrega `DATABASE_URL` manualmente con la cadena de conexión de Neon.
4. Agrega estas variables:

```text
ETL_TARGET=postgres
LOAD_POSTGRES=1
REQUIRE_POSTGRES_LOAD=1
SUPERSET_SECRET_KEY=<clave-larga-y-aleatoria>
SUPERSET_ADMIN_USER=admin
SUPERSET_ADMIN_PASS=<password-fuerte>
SUPERSET_ADMIN_EMAIL=admin@poc.com
SUPERSET_CREATE_ADMIN=1
SUPERSET_METADATA_DATABASE_URL=sqlite:////app/superset_home/superset.db
SUPERSET_TALISMAN_ENABLED=false
SUPERSET_BOOTSTRAP_DASHBOARD=1
SUPERSET_DW_DATABASE_NAME=PoC DW
```

`SUPERSET_SECRET_KEY` debe ser larga y aleatoria. Puedes generarla con:

```bash
openssl rand -hex 32
```

También puedes usar como referencia la plantilla [`northflank.env.example`](northflank.env.example). No subas credenciales reales al repositorio.

`SUPERSET_METADATA_DATABASE_URL` guarda los dashboards y usuarios de Superset. Para la demo se usa SQLite dentro de `/app/superset_home`; por eso el servicio necesita un volumen persistente.

Si prefieres usar PostgreSQL también para la metadata de Superset, crea una base separada llamada `superset` y usa:

```text
SUPERSET_METADATA_DATABASE_URL=postgresql+psycopg2://usuario:password@host:5432/superset
```

No apuntes la metadata a la misma base `bi_dw`: Superset crearía sus tablas junto al data warehouse y podría confundir el modelo analítico.

## Paso 4. Crear el job ETL

Este job carga los datos en PostgreSQL. Debe ejecutarse **antes** de crear el dashboard.

1. En el proyecto: **Create new → Job**.
2. Nombre: `poc-etl-load`.
3. Fuente: **Git repository**.
4. Repositorio: `DavCoder22/Proyecto34`.
5. Rama: `main`.
6. Build type: **Dockerfile**.
7. Dockerfile path: `docker/Dockerfile.etl`.
8. Build context: `.` (raíz del repositorio).
9. Runtime environment: enlaza el secret group `poc-superset-secrets` o agrega manualmente:

```text
DATABASE_URL=<POSTGRES_URI del addon o Neon>
ETL_TARGET=postgres
LOAD_POSTGRES=1
REQUIRE_POSTGRES_LOAD=1
```

10. Crea el job y ejecútalo manualmente (**Run job**).

El job crea en la base las tablas originales `stg_*`, las transformadas `clean_*`, el DW (`dim_*`, `fact_ventas`) y las vistas. El servicio Jupyter debe usar la misma `DATABASE_URL` con `ETL_TARGET=postgres` y `RUN_ETL_ON_START=1` para que el notebook muestre esos datos. En local no definas `ETL_TARGET=postgres`: deja `ETL_TARGET=sqlite` para que Jupyter use `03_dw/dw.db`.

En los logs debes ver:

```text
[LOAD] DW PostgreSQL actualizado en ...
=== PIPELINE OK ===
Ventas fact filas: 6800
```

Si el job falla, revisa que `DATABASE_URL` sea `postgresql+psycopg2://...` y que el addon esté healthy. Vuelve a ejecutar el job después de corregir la variable.

### Alternativa si no tienes job: cargar la base desde tu computadora

Si no ves la opción **Job** o no quieres crearlo, puedes ejecutar el ETL localmente apuntando a Neon. Northflank solo necesita que la base ya tenga las tablas y vistas antes de arrancar Superset.

En Linux o macOS:

```bash
export DATABASE_URL="postgresql+psycopg2://usuario:password@ep-xxxxx.region.aws.neon.tech/neondb?sslmode=require"
export ETL_TARGET=postgres
export LOAD_POSTGRES=1
export REQUIRE_POSTGRES_LOAD=1
.venv/bin/python 02_etl/main.py
```

En Windows PowerShell:

```powershell
$env:DATABASE_URL="postgresql+psycopg2://usuario:password@ep-xxxxx.region.aws.neon.tech/neondb?sslmode=require"
$env:ETL_TARGET="postgres"
$env:LOAD_POSTGRES="1"
$env:REQUIRE_POSTGRES_LOAD="1"
.venv\Scripts\python.exe 02_etl/main.py
```

Debes ver:

```text
[LOAD] DW PostgreSQL actualizado en ...
=== PIPELINE OK ===
Ventas fact filas: 6800
```

Después de cargar Neon desde tu equipo, reinicia el servicio Superset en Northflank. El bootstrap encontrará las vistas y creará el dashboard. Esta alternativa no usa jobs ni addons de Northflank.

## Paso 5. Crear el servicio Superset

1. En el proyecto: **Create new → Service → Combined service**.
2. Nombre: `poc-superset`.
3. Repositorio: `DavCoder22/Proyecto34`.
4. Rama: `main`.
5. Build type: **Dockerfile**.
6. Dockerfile path: `docker/superset/Dockerfile`.
7. Build context: `.` (raíz del repositorio).
8. Networking:
   - Puerto: `8088`.
   - Protocolo: `HTTP`.
   - Accesibilidad: `Public`.
   - Northflank puede detectar el puerto por el `EXPOSE 8088` del Dockerfile; verifica que exista.
9. Health check:
   - Protocolo: `HTTP`.
   - Path: `/health`.
   - Puerto: `8088`.
   - Initial delay: `120` segundos.
   - Interval: `10` segundos.
   - Timeout: `5` segundos.
   - Failure threshold: `5`.
10. Resources:
   - Para el plan Sandbox: 0.5 vCPU y 1 GB de RAM.
   - Si tienes presupuesto: 1 vCPU y 1 GB; solo sube a 2 GB si el dashboard lo necesita y el crédito lo permite.
   - No uses 1 vCPU y 2 GB en Sandbox: el costo mensual supera los 20 USD.
11. Persistent volume:
   - Mount path: `/app/superset_home`.
   - Tamaño: 1 GB.
   - Sin este volumen, el dashboard puede desaparecer en cada redeploy porque la metadata SQLite se pierde.
12. Environment:
   - Enlaza el secret group `poc-superset-secrets`.
   - Verifica que `DATABASE_URL` apunte al addon PostgreSQL.
13. Crea el servicio y espera el build.

El primer arranque tarda más de lo normal porque ejecuta migraciones de Superset y crea el dashboard. Por eso el health check debe tener un initial delay de al menos 120 segundos.

## Paso 6. Verificar los logs

En **Observe → Logs** del servicio Superset busca estas líneas:

```text
[superset] Inicializando base de metadatos...
[superset] Creando/verificando el dashboard Sales Analytics...
[bootstrap] Dashboard Sales Analytics creado correctamente.
Listening at: http://0.0.0.0:8088
```

Si ves:

```text
[bootstrap] Esperando vistas KPI en PostgreSQL...
```

significa que el ETL todavía no cargó las vistas o que `DATABASE_URL` está mal. Ejecuta de nuevo el job ETL y reinicia el servicio Superset.

## Paso 7. Abrir el dashboard

1. Abre la URL pública del servicio Superset (Northflank la muestra en **Overview → Domains**).
2. Inicia sesión con `SUPERSET_ADMIN_USER` y `SUPERSET_ADMIN_PASS`.
3. Ve a **Dashboards**.
4. Abre **Sales Analytics**.
5. Deben aparecer los cuatro gráficos:
   - Evolución de Ventas.
   - Ventas por Categoría.
   - Desempeño por Sucursal.
   - Ventas por Segmento.

La URL directa suele ser:

```text
https://<url-publica-de-northflank>/superset/dashboard/sales-analytics/
```

## Paso 8. Verificar los datos

Si necesitas comprobar que el data warehouse tiene los totales correctos, ejecuta en el addon o en SQL Lab:

```sql
SELECT SUM(venta_neta) AS ingresos,
       SUM(cantidad) AS unidades,
       SUM(margen) AS margen,
       COUNT(DISTINCT id_venta) AS transacciones
FROM fact_ventas;
```

Resultado esperado:

```text
ingresos      | unidades | margen        | transacciones
7452222.71    | 13817    | 1966780.12    | 3587
```

## Problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| El build falla porque no encuentra `docker/superset/Dockerfile` | Los archivos no están en GitHub o el path/contexto está mal | Haz commit y push; usa Dockerfile `docker/superset/Dockerfile` y contexto raíz |
| `No module named psycopg2` | Se está usando la imagen oficial de Superset | Usa el Dockerfile del repositorio, que instala `psycopg2-binary` |
| El servicio reinicia por health check | Superset tarda en arrancar o falta memoria | Initial delay 120 s y al menos 1 GB de RAM |
| El dashboard no aparece | El ETL no cargó PostgreSQL o las vistas no existen | Ejecuta el job ETL o carga la base desde tu equipo, luego reinicia Superset; revisa logs del bootstrap |
| No encuentro la opción Job en Northflank | El menú Create new no está en el proyecto o el plan no lo muestra | Entra al proyecto y usa **Create new → Job**; si no aparece, carga Neon localmente con el ETL |
| `could not connect to server` | `DATABASE_URL` usa `localhost` o una URL externa | Usa el host interno del addon PostgreSQL |
| El dashboard desaparece tras un redeploy | Metadata SQLite sin volumen persistente | Monta `/app/superset_home` o usa PostgreSQL para metadata |
| No puedo entrar con la contraseña nueva | El usuario admin ya existía y `create-admin` no actualiza la contraseña | Usa la shell del servicio y ejecuta `superset fab reset-password --username admin --password ...`, o recrea el volumen de metadata |
| Superset redirige a HTTPS o falla el login | Talisman o cookies seguras detrás del proxy | Mantén `SUPERSET_TALISMAN_ENABLED=false` y `SUPERSET_COOKIE_SECURE=false` |
| `ModuleNotFoundError: No module named 'psycopg'` | SQLAlchemy tomó el driver psycopg3 al usar `postgresql://` | Usa `postgresql+psycopg2://` en `DATABASE_URL` o redepliega el código actualizado |
| Neon rechaza la conexión por SSL | Se eliminó `sslmode=require` de la URL | Conserva `?sslmode=require` en `DATABASE_URL` |
| Neon da error de conexión tras unos minutos inactivo | El compute se suspendió por scale to zero | Recarga el dashboard; la primera consulta reactiva Neon en segundos |
| Quiero recrear el dashboard | El dashboard ya existe y el bootstrap lo omite | Define `SUPERSET_BOOTSTRAP_FORCE=1` y reinicia; esto elimina y recrea el dashboard |

## Checklist para la demo

- [ ] Los archivos de Superset están en la rama `main`.
- [ ] El addon PostgreSQL está healthy.
- [ ] El job ETL terminó con `Ventas fact filas: 6800`.
- [ ] El servicio Superset está healthy.
- [ ] El log muestra `[bootstrap] Dashboard Sales Analytics creado correctamente.`
- [ ] La URL pública abre el login de Superset.
- [ ] El dashboard `Sales Analytics` aparece en **Dashboards**.
- [ ] Los cuatro gráficos cargan con datos.
- [ ] Tienes a mano el usuario y la contraseña de administrador para la exposición.

## Nota sobre acceso público

El dashboard queda protegido por login. Para la exposición, entra con el usuario administrador. Si necesitas un enlace sin login, configura el rol público de Superset y publica el dashboard; no es recomendable para una PoC con datos comerciales.

## Validación local realizada

La misma configuración se probó localmente con Docker:

- El job ETL cargó PostgreSQL y terminó con 6.800 filas en `fact_ventas`.
- Superset creó el dashboard `Sales Analytics` con cuatro gráficos.
- El endpoint `/health` respondió `200`.
- El dashboard respondió `200` después del login.

El problema de Northflank no es la lógica del dashboard, sino la configuración de red, el health check, la memoria y la persistencia de la metadata.
