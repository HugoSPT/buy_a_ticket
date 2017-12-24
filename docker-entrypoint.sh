#!/bin/bash

touch /opt/buy_a_ticket/logs/gunicorn.log
touch /opt/buy_a_ticket/logs/access.log
tail -n 0 -f /opt/buy_a_ticket/logs/*.log &

echo Starting Gunicorn.

exec gunicorn buy_a_ticket.wsgi:application \
    --name buy_a_ticket \
    --bind=0.0.0.0:8000 \
    --workers 3 \
    --log-level=info \
    --log-file=/opt/buy_a_ticket/logs/gunicorn.log \
    --access-logfile=/opt/buy_a_ticket/logs/access.log \
    --env DJANGO_SETTINGS_MODULE=buy_a_ticket.settings &

echo Starting nginx
exec service nginx start
