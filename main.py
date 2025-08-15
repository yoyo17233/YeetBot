import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from utils.utilities import update_server_info, get_server_info, load_config
from utils.minecraft import is_server_up
from cogs.yeetbot import startlogging

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
YEET = os.getenv("YEET")

CONFIG_FILE = os.getenv("CONFIG_FILE")
config = load_config()

intents = discord.Intents.default()
intents.message_content = True  
intents.guilds = True           

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔁 Synced {len(synced)} slash commands")
        update_server_info("serverstarting", 0)
        if is_server_up():
            await bot.change_presence(
                activity=discord.Game(f"{get_server_info().get('serverid')} ✅"),
                status=discord.Status.online
            )
            await startlogging(bot.get_cog("YeetBot"), YEET)
        else:
            await bot.change_presence(
                activity=discord.Game("Server Offline ❌"),
                status=discord.Status.online,
            )
            update_server_info("logging", 0)
        
    except Exception as e:
        print(f"⚠️ Error syncing commands: {e}")

async def load_cogs():
    await bot.load_extension("cogs.snoopiebot")
    await bot.load_extension("cogs.yeetbot")
    await bot.load_extension("cogs.idsetter")

@bot.event
async def setup_hook():
    await load_cogs()

bot.run(TOKEN)
