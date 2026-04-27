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
DOUBLE_CHECK_WAIT = 5 
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

        no_words = [
            "sin disponibilidad",
            "sold out",
            "agotado",
            "no hay boletos"
        ]

        yes_words = [
            "comprar boletos",
            "buy tickets",
            "seleccionar boletos",
            "tickets available",
            "find tickets"
            "poca disponibilidad"
        ]

        if any(word in text for word in no_words):
            return "no"

        if any(word in text for word in yes_words):
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
            print("Estado actual:", state)

            # SOLO si cambia de NO a YES
            if last_state == "no" and state == "yes":

                print("Cambio detectado: no -> yes")

                # doble verificación
                await asyncio.sleep(DOUBLE_CHECK_WAIT)

                confirm = check_site()
                print("Segunda revisión:", confirm)

                if confirm == "yes":

                    now = time.time()

                    if now - last_alert > COOLDOWN:
                        await send_alert(channel)
                        last_alert = now
                        print("🚨 ALERTA ENVIADA")
                    else:
                        print("Cooldown activo")

            last_state = state

        except Exception as e:
            print("Error loop:", e)


client.run(TOKEN)
