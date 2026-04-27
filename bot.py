import discord
from discord.ext import commands, tasks
import requests
import asyncio
import time
import os

# =====================
# CONFIG
# =====================
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ROLE_ID = os.getenv("ROLE_ID")
URL = os.getenv("URL")

CHECK_EVERY = 4
COOLDOWN = 120

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
# CHECK SITE (REQUESTS SIMPLE)
# =====================
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
# EMBED
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
# STATUS
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
# LOOP
# =====================
@tasks.loop(seconds=CHECK_EVERY)
async def monitor():
    global last_state, last_alert

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    try:
        state = check_site()
        print("Estado:", state)

        if last_state == "no" and state == "yes":
            now = time.time()

            if now - last_alert > COOLDOWN:

                await channel.send(
                    content=f"<@&{ROLE_ID}> 🚨",
                    embed=make_embed(),
                    allowed_mentions=discord.AllowedMentions(roles=True)
                )

                await asyncio.sleep(2)

                last_alert = now
                print("🚨 ALERTA ENVIADA")

        last_state = state

    except Exception as e:
        print("Monitor error:", e)
# =====================
# BOTONES (RESTAURADOS)
# =====================
class ControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

  
    @discord.ui.button(label="TEST ALERT", style=discord.ButtonStyle.primary)
    async def test(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            "🔥 Test ejecutado",
            ephemeral=True
        )

        await interaction.channel.send(embed=make_embed())
# =====================
# EVENTS
# =====================
@bot.event
async def on_ready():
    print(f"Conectado como {bot.user}")

    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("💜 BOT BTS ONLINE", view=ControlView())

    monitor.start()

# =====================
# COMMANDS
# =====================
@bot.command()
async def status(ctx):
    await ctx.send(embed=make_status())

# =====================
# RUN
# =====================
bot.run(TOKEN)
