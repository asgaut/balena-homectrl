import asyncio
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

    print("Current prices:")
    for key in home.price_level:
        print(key, '->', home.price_level[key], home.price_total[key], 'kr')

if __name__ ==  '__main__':
    access_token = os.environ.get('TIBBER_TOKEN', tibber.DEMO_TOKEN)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
