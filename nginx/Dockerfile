FROM nginx

# Copy generated files from the host to the container
COPY dhparam.pem /etc/ssl/certs/dhparam.pem
COPY localhost.crt /etc/ssl/certs/localhost.crt
COPY localhost.key /etc/ssl/private/localhost.key

# Copy the nginx configuration file from the host to the container
COPY nginx.conf /etc/nginx/conf.d/default.conf
