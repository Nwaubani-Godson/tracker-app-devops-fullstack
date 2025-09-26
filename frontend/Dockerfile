FROM nginx:alpine

COPY index.html /usr/share/nginx/html/

COPY script.js /usr/share/nginx/html/
COPY config.js /usr/share/nginx/html/

CMD /bin/sh -c "sed -i 's|PLACEHOLDER_FOR_BACKEND_URL|${BACKEND_URL:-backend:8000/tasks}|' /usr/share/nginx/html/config.js && nginx -g 'daemon off;'"





