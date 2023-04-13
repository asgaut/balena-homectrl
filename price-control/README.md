# price-control

Connects to tibber API, gets price levels and controls Namron Zigbee Touch thermostats.

## Test setting away mode

```shell
mosquitto_pub -h 192.168.86.27 -t 'zigbee2mqtt/0x1fff0001000001f2/set' -m '{"away_mode":"OFF"}'
mosquitto_pub -h 192.168.86.27 -t 'zigbee2mqtt/0x1fff0001000001f2/set' -m '{"away_mode":"ON"}'
```

## Configuration

Create a .env file with these lines and edit to reflect your setup

```shell
TIBBER_TOKEN="tibber token from https://developer.tibber.com/settings/access-token"
MQTT_SERVER="MQTT broker IP"
```

Tip: under Powershell use https://www.powershellgallery.com/packages/Set-PsEnv
and run `Set-PsEnv` to set the variables in the current process.
