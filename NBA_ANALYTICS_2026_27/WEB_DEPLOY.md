# NBA Analytics 2026-27 — versión web

## Qué incluye
- Panel responsive para celular y computadora.
- Lectura de equipos, jugadores, calendario, box scores, líderes y cuotas ya guardadas.
- Búsqueda y ficha reciente de jugadores.
- Acceso protegido opcional mediante `NBA_WEB_USER` y `NBA_WEB_PASSWORD`.
- La web es de solo lectura: no permite lanzar sincronizaciones públicas ni editar la base de datos.

## Probar en Windows
1. Descomprime esta versión del proyecto.
2. Ejecuta `setup_windows.bat` si aún no instalaste las dependencias.
3. Abre `run_web.bat`.
4. En la computadora entra a `http://localhost:8000`.
5. Para probar desde tu celular en la misma Wi-Fi, abre `http://IP-LOCAL-DE-TU-PC:8000`. Ambos dispositivos deben estar en la misma red y el firewall debe permitir Python en red privada.

## Para acceder con la PC apagada
Hay que desplegar el proyecto en un servidor cloud. El archivo `render.yaml` prepara un servicio de Render con disco persistente. Pasos generales:
1. Sube la carpeta a un repositorio privado de GitHub.
2. En Render crea un Blueprint desde ese repositorio y aplica `render.yaml`.
3. Configura `NBA_WEB_USER` y `NBA_WEB_PASSWORD` con valores fuertes.
4. Copia tu `nba_analytics.db` al disco persistente `/var/data/nba_analytics.db` mediante un procedimiento seguro de migración/transferencia, o inicializa y sincroniza la base desde el servidor.
5. Comprueba `/health` y entra a la URL HTTPS asignada.

**Importante:** el despliegue no se ha realizado por ti. Para que funcione con la PC apagada, el servicio cloud debe estar publicado, protegido y con almacenamiento persistente. El nivel gratuito de algunos hosts puede no ofrecer disco persistente o puede suspender servicios; revisa el plan antes de depender de él.

## Sincronización de datos
La sincronización de NBA Stats debe ejecutarse en el propio servidor cloud o desde un proceso de administración privado. No expongas `main.py sync` como endpoint público. SQLite funciona bien para una instancia y un volumen moderado; si más adelante hay varias instancias o mucha escritura simultánea, conviene migrar a PostgreSQL.

## Seguridad
- No compartas `.env` ni credenciales.
- Configura usuario y contraseña antes de publicar.
- Usa HTTPS del proveedor.
- Haz copias de seguridad de la base.
