#!/usr/bin/env bash
set -o errexit

echo "=== INSTALANDO DEPENDENCIAS ==="
pip install -r requirements.txt

echo "=== APLICANDO MIGRACIONES ==="
python manage.py migrate

echo "=== RECOLECTANDO ARCHIVOS ESTATICOS ==="
python manage.py collectstatic --noinput

echo "=== ¡CONSTRUCCION COMPLETADA! ==="
