web: gunicorn japanese_to_python.wsgi --log-file -
release: python manage.py migrate && python manage.py collectstatic --noinput