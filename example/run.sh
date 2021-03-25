export SPID_CURRENT_INDEX=0

python -B ./manage.py migrate
python -B ./manage.py runserver 0.0.0.0:8000
