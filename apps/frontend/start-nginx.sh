#!/bin/sh
# Start script for nginx with Railway's dynamic PORT

# Use Railway's PORT or default to 80
PORT=${PORT:-80}

# Replace PORT placeholder in nginx config
sed -i "s/listen 80;/listen $PORT;/g" /etc/nginx/conf.d/default.conf

# Start nginx
exec nginx -g 'daemon off;'
