import asyncio
from datetime import datetime, timedelta
from random import randint

import discord
import taxoniq
from discord.ext import tasks

token = "MTA1OTA5NTA3NzU2NzM0ODc5Ng.Gk9aBz.l_yWnjITlwT0oxHoqTVh52_GW64HqOd4pCYp6E"
channel_id = 1234513123436920913

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


current_time = datetime.now()
if current_time.hour >= 7:
    target_time = current_time.replace(hour=7, minute=0, second=0, microsecond=0) + timedelta(days=1)
else:
    target_time = current_time.replace(hour=7, minute=0, second=0, microsecond=0)

@client.event
async  def on_ready():
    print(f"We have logged in as {client.user}")
    daily.start()

@tasks.loop(hours=24)
async def daily():
    done = False
    fail_count = 0
    while not done:
        fail_count += 1
        try:
            target_species = taxoniq.Taxon(randint(0, 100000000))
            if target_species.rank == taxoniq.Rank.genus:
                sci = target_species.scientific_name
                com = target_species.common_name
                done = True
        except:
            done = False

    message_channel = client.get_channel(channel_id)
    await message_channel.send(f"Today's genus-code is: {target_species.tax_id**2}")
    print(f"code sent! ({target_species.tax_id**2})")

@daily.before_loop
async def before():
    await client.wait_until_ready()
    print(f"time left: {target_time - current_time}")
    await asyncio.sleep((target_time - current_time).total_seconds())
    print("Finished waiting...")

# @client.event
# async def on_message(message):
#     print(f"message from {message.author}, content:\n{message.content}")
#     if message.author == client.user:
#         return
#     await message.channel.send("Leave me alone, I've got a lot of genera to search through 'til tomorrow!")

client.run(token)