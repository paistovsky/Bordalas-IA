# Bordalás IA — GitHub Actions deployment

Archivos para la primera fase online en modo OBSERVER.

## Instalación

Copia estos archivos en la raíz del repositorio:

- `requirements.txt`
- `.gitignore`
- `.env.example`
- `scripts/prune_github_state.py`
- `.github/workflows/bordalas-observer.yml`

Después configura en GitHub:

Settings → Secrets and variables → Actions → New repository secret

Crea:

- `BIWENGER_USERNAME`
- `BIWENGER_PASSWORD`
- `API_FOOTBALL_KEY`

El workflow NO ejecuta `--live`. Solo observa.

Puede ejecutarse manualmente desde:
Actions → Bordalas IA Observer → Run workflow

Y programado a los minutos 07 y 37 de cada hora.
