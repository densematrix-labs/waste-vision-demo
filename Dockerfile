FROM nginx:1.27-alpine

COPY index.html /usr/share/nginx/html/index.html
COPY customer-scenes /usr/share/nginx/html/customer-scenes
RUN chmod -R a+rX /usr/share/nginx/html
