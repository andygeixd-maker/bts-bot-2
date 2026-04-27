import discord
from discord.ext import commands, tasks
import asyncio
import time
import os
from playwright.async_api import async_playwright

# =====================
# CONFIG
# =====================
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ROLE_ID = os.getenv("ROLE_ID")
URL = os.getenv("URL")

CHECK_EVERY = 4
COOLDOWN = 120

browser = None
page = None
pw = None

# =====================
# PLAYWRIGHT INIT
# =====================
async def init_browser():
    global browser, page, pw

    pw = await async_playwright().start()

    browser = await pw.chromium.launch(
        headless=True,
        args=["--no-sandbox"]
    )

    context = await browser.new_context()
    page = await context.new_page()

# =====================
# SAFE RESTART
# =====================
async def restart_browser():
    global browser, page, pw

    try:
        if browser:
            await browser.close()
    except:
        pass

    try:
        if pw:
            await pw.stop()
    except:
        pass

    await init_browser()

# =====================
# BOT SETUP
# =====================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

last_state = "no"
last_alert = 0
started_at = time.time()
last_error = None

# =====================
# CHECK SITE (TU LÓGICA MEJORADA)
# =====================
async def check_site():
    try:
        if page is None:
            return "no"

        await page.goto(URL, timeout=30000)
        await asyncio.sleep(2)

        text = (await page.content()).lower()

        no_words = [
            "sin disponibilidad",
            "sold out",
            "agotado",
            "no hay boletos",
            "no disponible",
            "boletos agotados"
        ]

        yes_words = [
            "comprar",
            "buy",
            "tickets",
            "get tickets",
            "seleccionar",
            "available",
            "disponible",
            "ver boletos",
            "poca disponibilidad"
        ]

        if any(w in text for w in no_words):
            return "no"

        if any(w in text for w in yes_words):
            return "yes"

        return "no"

    except Exception as e:
        print("Error check:", e)
        return "no"

# =====================
# EMBED (TU ESTILO)
# =====================
def make_embed():
    embed = discord.Embed(
        title="🚨 BTS CDMX ALERTA 🚨",
        description="Posible disponibilidad detectada",
        color=0xA020F0
    )

    embed.add_field(name="🎟️ Link", value=URL, inline=False)
    embed.set_image(url="https://i.imgur.com/jctrM4G.gif")

    return embed

# =====================
# STATUS PANEL (FIXED)
# =====================
def make_status():
    uptime = int(time.time() - started_at)

    embed = discord.Embed(
        title="💜 BOT STATUS PANEL",
        color=0xA020F0
    )

    embed.add_field(name="Estado", value=last_state, inline=True)
    embed.add_field(name="Uptime", value=f"{uptime}s", inline=True)
    embed.add_field(name="Error", value=last_error or "None", inline=False)

    return embed

# =====================
# LOOP ESTABLE
# =====================
@tasks.loop(seconds=CHECK_EVERY)
async def monitor():
    global last_state, last_alert

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    try:
        state = await check_site()
        print("Estado:", state)

        if last_state == "no" and state == "yes":

            now = time.time()

            if now - last_alert > COOLDOWN:

                role_ping = f"<@&{ROLE_ID}>"

                for _ in range(3):
                    await channel.send(
                        content=role_ping,
                        embed=make_embed()
                    )
                    await asyncio.sleep(2)

                last_alert = now
                print("🚨 ALERTA ENVIADA")

        last_state = state

    except Exception as e:
        print("Monitor error:", e)
        await restart_browser()

# =====================
# EVENTS
# =====================
@bot.event
async def on_ready():
    print(f"Conectado como {bot.user}")

    await init_browser()

    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("💜 BOT BTS ONLINE")

    monitor.start()

# =====================
# COMMANDS
# =====================
@bot.command()
async def status(ctx):
    uptime = int(time.time() - started_at)
    await ctx.send(f"💜 Estado: {last_state} | Uptime: {uptime}s")

# =====================
# RUN
# =====================
bot.run(TOKEN)
