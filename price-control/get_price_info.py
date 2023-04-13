import asyncio
import datetime as dt
import os
import sys
import tibber

async def main():
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

if __name__ ==  '__main__':
    access_token = os.environ.get('TIBBER_TOKEN', tibber.DEMO_TOKEN)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
