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

        # Create a new dict with only the prices for the previous and next 12 hours
        prices = {}
        current_time = dt.datetime.utcnow().astimezone(dt.timezone.utc)
        for key in home.price_total.keys():
            key_time = dt.datetime.fromisoformat(key).astimezone(dt.timezone.utc)
            if key_time <= current_time + dt.timedelta(hours=12) and \
                key_time >= current_time - dt.timedelta(hours=12):
                prices[key] = home.price_total[key]

        # Create a new dict with the price index for each price
        price_index = {}
        index = 0
        for kv in sorted(prices.items(), key=lambda kv: kv[1]):
            price_index[kv[0]] = index
            index += 1
        print('Number of hours considered: ', len(price_index))

        print("Current prices:")
        for key in home.price_level:
            level = "#" * (price_index.get(key, -1) + 1)
            print(f'{key} -> {price_index.get(key, -1):02d} {home.price_level[key]:14s} {home.price_total[key]:.2f} kr {level}')

        start_day = dt.datetime.utcnow().day
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
            now_price_index = -1
            for key in home.price_level:
                if dt.datetime.fromisoformat(key).astimezone(dt.timezone.utc) == now_hour:
                    now_price_level = home.price_level[key]
                    now_price_index = price_index.get(key, -1)
                    break;

            if now_price_level == "VERY_CHEAP" or now_price_index < 18:
                payload = '{"away_mode":"OFF"}'
                payload_power = '{"state": "ON"}'
            else:
                payload = '{"away_mode":"ON"}'
                payload_power = '{"state": "OFF"}'

            if dry_run:
                print(f'Now (UTC): {now_hour} {now_price_level} price_index:{now_price_index:02d}')
                print(f'Payload: {payload}')
                want_disconnect = True
                mqttc.disconnect()
                sleep(1)
                sys.exit(0)

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
