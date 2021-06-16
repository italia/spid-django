python -B ./manage.py migrate
python -B ./manage.py collectstatic --noinput

# python -B ./manage.py runserver 0.0.0.0:8000
uwsgi --https 0.0.0.0:8000,./certificates/public.cert,./certificates/private.key --module example.wsgi:application --env example.settings --chdir .

