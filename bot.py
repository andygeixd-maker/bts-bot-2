import discord
from discord.ext import commands
import requests
import asyncio
import time
from bs4 import BeautifulSoup
import os


TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ROLE_ID = os.getenv("ROLE_ID")
URL = os.getenv("URL")

CHECK_EVERY = 4
COOLDOWN = 120
DOUBLE_CHECK_WAIT = 5 
BASE_DELAY = 3
MAX_DELAY = 8
  

intents = discord.Intents.default()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix="!", intents=intents)

last_state = None
last_alert = 0
MAX_ALERT = 5
alert_count = 0

AGENTS = [
    "Mozilla/5.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        ]
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
  
def make_status():
    uptime = int(time.time() - started_at)

    embed = discord.Embed(
        title="💜 Estado del Bot",
        color=0xA020F0
    )

    embed.add_field(name="Último estado", value=last_state)
    embed.add_field(name="Uptime", value=f"{uptime}s")
    embed.add_field(name="Check rate", value=f"{CHECK_MIN}-{CHECK_MAX}s")

    return embed
  
async def send_alert(channel):
    role_ping = f"<@&{ROLE_ID}>"

    for i in range(5):
        await channel.send(
            content=role_ping,
            embed=make_alert()
        )
        await asyncio.sleep(2)


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

@bot.event
async def on_ready():
    print(f"Conectado como {bot.user}")
    bot.loop.create_task(monitor())

@bot.command()
async def test(ctx):
    await ctx.send("🔥 Test manual iniciado")
    await send_alert(ctx.channel)

@bot.command()
async def status(ctx):
    await ctx.send(embed=make_status())



client.run(TOKEN)
