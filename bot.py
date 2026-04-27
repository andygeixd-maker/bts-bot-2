import discord
import requests
import asyncio
import time
from bs4 import BeautifulSoup

import os

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ROLE_ID = os.getenv("ROLE_ID")
URL = os.getenv("URL")

CHECK_EVERY = 5
COOLDOWN = 120

BASE_DELAY = 3
MAX_DELAY = 8
  

intents = discord.Intents.default()
client = discord.Client(intents=intents)

last_state = None
last_alert = 0
MAX_ALERT = 5
alert_count = 0

def check_site():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        r = requests.get(URL, headers=headers, timeout=10)
        text = r.text.lower()

        # señales negativas
        if "sin disponibilidad" in text or "sold out" in text or "agotado" in text:
            return "no"

        # señales positivas
        if "comprar boletos" in text or "buy tickets" in text or "comprar" in text:
            return "yes"

        return "unknown"

    except Exception as e:
        print("Error web:", e)
        return "unknown"


def make_embed():
    embed = discord.Embed(
        title="🚨 BTS CDMX - BOLETOS DETECTADOS 🚨",
        description="Se detectó posible disponibilidad en Ticketmaster.",
        color=0xA020F0
    )

    embed.add_field(
        name="🎟️ Estado",
        value="Revisa Ticketmaster inmediatamente.",
        inline=False
    )

    embed.add_field(
        name="🔗 Link",
        value="https://www.ticketmaster.com.mx/bts-boletos/artist/2110227",
        inline=False
    )

    embed.set_footer(text="Sistema automático de alertas BTS 💜")
    return embed


@client.event
async def on_ready():
    global last_state, last_alert

    print(f"Bot listo como {client.user}")

    channel = client.get_channel(CHANNEL_ID)

    if channel is None:
        print("No se encontró el canal.")
        return

    await channel.send("💜 Bot conectado y monitoreando Ticketmaster.")

    while True:
        try:
            state = check_site()
            print("Estado:", state)

            if state == "yes" and last_state != "yes":
                now = time.time()

                if now - last_alert > COOLDOWN:
                    role_ping = f"<@&{ROLE_ID}>"

                    for i in range(5):
                        await channel.send(
                            content=role_ping,
                            embed=make_embed()
                        )
                        await asyncio.sleep(1.5)

                    last_alert = now

            last_state = state

        except Exception as e:
            print("Error loop:", e)

        await asyncio.sleep(CHECK_EVERY)



client.run(TOKEN)
