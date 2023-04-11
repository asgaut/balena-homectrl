FROM eclipse-mosquitto

# Balena does not support bind mounts, so we must copy
# the config file into the image
COPY mosquitto.conf /mosquitto/config
