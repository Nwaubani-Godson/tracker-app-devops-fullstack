FROM nginx:alpine

RUN apk add --no-cache bash

COPY index.html /usr/share/nginx/html/

COPY script.js /usr/share/nginx/html/

COPY entrypoint.sh /docker-entrypoint.sh

RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
