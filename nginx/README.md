# NGINX TLS setup

The following steps must be performed before running `balena push`.

## Create and sign a new certificate

Copy the `openssl.conf.default` to a new file without the .default suffix and edit
the file with the required hostnames or IPs of the Raspberry Pi.

Then run:
```
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout localhost.key -out localhost.crt -config openssl.conf
```

## Diffie-Hellman key

The default OpenSSL DH key is only 1024, we want a stronger key:

```
openssl dhparam -out dhparam.pem 2048
```

## Testing on the host

```
docker build -t "localnginx" .
docker run --rm -d -p 8080:80 -p 8081:443 localnginx
```

Import the localhost.crt into the "Trusted Root Certification Authorities" store on Windows
to trust the certificate of the web server.

The contents of the certificate can be shown with `openssl x509 -in ./localhost.crt -text`.
