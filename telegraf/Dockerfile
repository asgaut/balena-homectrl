# telegraf is a multi-arch image not fully supported by Balena
# See https://forums.balena.io/t/balenacloud-emulated-build-breaks-application/194951
# Need to specify arch or image hash, using arch below.

FROM arm64v8/telegraf:latest

# Balena does not support bind mounts, so we must copy
# the config file into the image
COPY telegraf.conf /etc/telegraf/telegraf.conf
