FROM nginx:alpine

COPY index.html /usr/share/nginx/html/
COPY script.js /usr/share/nginx/html/
COPY config.template.js /usr/share/nginx/html/

# At container startup, generate config.js from template using BACKEND_URL
CMD /bin/sh -c "\
  envsubst '\$BACKEND_URL' < /usr/share/nginx/html/config.template.js > /usr/share/nginx/html/config.js && \
  exec nginx -g 'daemon off;'\
"
