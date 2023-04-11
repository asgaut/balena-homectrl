import asyncio
import datetime as dt
import os
import paho.mqtt.client as mqtt
import signal
import sys
import tibber
from socket import gethostname
from time import sleep

"""
From: https://developer.tibber.com/docs/reference#pricelevel

PriceLevel
Price level based on trailing price average (3 days for hourly values and 30 days for daily values)

VERY_CHEAP: The price is smaller or equal to 60 % compared to average price.
CHEAP: The price is greater than 60 % and smaller or equal to 90 % compared to average price.
NORMAL: The price is greater than 90 % and smaller than 115 % compared to average price.
EXPENSIVE: The price is greater or equal to 115 % and smaller than 140 % compared to average price.
VERY_EXPENSIVE: The price is greater or equal to 140 % compared to average price.
"""

want_disconnect = False

def on_connect(client, obj, flags, rc):
    print("on_connect: "+str(rc))

def on_disconnect(client, userdata, rc):
    print("on_disconnect: "+str(rc))
    if want_disconnect:
        client.loop_stop()

def on_log(client, obj, level, string):
    # print(string)
    pass

async def control(dry_run: bool):
    mqttc = mqtt.Client("control.py@" + gethostname())
    mqttc.on_connect = on_connect
    mqttc.on_disconnect = on_disconnect
    mqttc.on_log = on_log
    mqttc.connect(mqtt_server, 1883, 60)
    mqttc.loop_start()

    while True:
        tibber_connection = tibber.Tibber(access_token)
        await tibber_connection.update_info()
        print("Tibber user:", tibber_connection.name)
        homes = tibber_connection.get_homes()
        if len(homes) == 0:
            sys.stderr.write("No tibber homes found")
            sys.exit(1)
        home = tibber_connection.get_homes()[0]
        await home.update_info()
        if len(homes) > 1:
            print("Using home address:", home.address1)
        await home.update_price_info()
        await tibber_connection.close_connection()

        old_price_level = ""
        now = dt.datetime.utcnow().astimezone(dt.timezone.utc)
        print("Todays and next 12 hours prices:")
        for key in home.price_level:
            if dt.datetime.fromisoformat(key).astimezone(dt.timezone.utc) <= now + dt.timedelta(hours=12):
                now_price_level = home.price_level[key]
                if now_price_level != old_price_level:
                    print(key, '->', home.price_level[key], home.price_total[key], 'kr')
                    old_price_level = now_price_level

        start_day = dt.datetime.utcnow().day
        old_price_level = ""
        print("Controlling power usage:")
        while True:
            global want_disconnect

            if want_disconnect:
                mqttc.disconnect()
                sleep(1)
                sys.exit(0)

            now = dt.datetime.utcnow()
            now_hour = dt.datetime(now.year, now.month, now.day, now.hour, tzinfo=dt.timezone.utc)
            now_price_level = ""
            for key in home.price_level:
                if dt.datetime.fromisoformat(key).astimezone(dt.timezone.utc) == now_hour:
                    if home.price_total[key] <= 1.0:
                        now_price_level = "NORMAL"
                    else:
                        now_price_level = home.price_level[key]
                    if now_price_level != old_price_level:
                        print(key, '->', now_price_level)
                        old_price_level = now_price_level
                    break;

            if not dry_run:
                if now_price_level == "VERY_CHEAP" or now_price_level == "CHEAP" or now_price_level == "NORMAL":
                    payload = '{"away_mode":"OFF"}'
                    payload_power = '{"state": "ON"}'
                else:
                    payload = '{"away_mode":"ON"}'
                    payload_power = '{"state": "OFF"}'

                # VK Entré
                mqttc.publish("zigbee2mqtt/0x1fff0001000001f2/set", payload, qos=0, retain=False)
                sleep(3)
                # VK Bad (kjeller)
                mqttc.publish("zigbee2mqtt/0x1fff000100000220/set", payload, qos=0, retain=False)
                sleep(3)
                # VK Bad (2. etg)
                mqttc.publish("zigbee2mqtt/0x1fff000100000217/set", payload, qos=0, retain=False)
                sleep(3)

                # VV-bereder power
                # APEX smart plug 16A (Datek HLU2909K)
                mqttc.publish("zigbee2mqtt/0x086bd7fffeb6ac3c/set", payload_power, qos=0, retain=False)

                for x in range(0, 60):
                    if want_disconnect:
                        break
                    sleep(1)

                if start_day != now.day:
                    break
            else:
                want_disconnect = True
                mqttc.disconnect()
                sleep(1)
                sys.exit(0)


def signal_handler(sig, frame):
    # remove our handler
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    print('Exiting...')
    global want_disconnect
    want_disconnect = True

if __name__ ==  '__main__':
    access_token = os.environ.get('TIBBER_TOKEN', tibber.DEMO_TOKEN)
    mqtt_server = os.environ.get('MQTT_SERVER', 'mqtt')

    dry_run = len(sys.argv) > 1 and sys.argv[1] == '--dry'

    want_disconnect = False
    signal.signal(signal.SIGINT, signal_handler)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(control(dry_run))
