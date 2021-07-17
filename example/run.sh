#!/usr/bin/env bash
# 
# Run the demo project with uwsgi web server (https, the default) or the development server (http)
#  

# Default run settings
address="0.0.0.0:8000"
protocol="https"

# Parse cli arguments provided with -p PROTOCOL or -a ADDRESS (take the lasts)
while getopts p:a: flag
do
    case "${flag}" in
        p) protocol=${OPTARG};;
        a) address=${OPTARG};;
    esac
done

# Select and run the proper server and settings
if [[ $protocol = "http" ]]
then
  echo "Run on http with Django's development server ..."
  python -B ./manage.py migrate
  DJANGO_SETTINGS_MODULE='example.develop_settings' python -B ./manage.py runserver $address

elif [[ $protocol != "https" ]]
then
  echo -e "\033[1;31mWrong protocol '$protocol' provided (use 'https' or 'http').\033[0m"
  exit 1

elif [[ $address != "0.0.0.0:8000" ]]
then
  echo "Run on https with uwsgi server and dynamic SPID_BASE_URL ..."
  python -B ./manage.py migrate
  python -B ./manage.py collectstatic --noinput

  DJANGO_SETTINGS_MODULE='example.dynamic_settings' uwsgi \
    --http-keepalive \
    --https $address,./certificates/public.cert,./certificates/private.key \
    --module example.wsgi:application \
    --env example.dynamic_settings \
    --chdir .

else
  echo "Run on https with uwsgi server and fixed SPID_BASE_URL ..."
  python -B ./manage.py migrate
  python -B ./manage.py collectstatic --noinput

  uwsgi \
    --http-keepalive \
    --https 0.0.0.0:8000,./certificates/public.cert,./certificates/private.key \
    --module example.wsgi:application \
    --env example.settings \
    --chdir . \
#    --honour-stdin
fi
