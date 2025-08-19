import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from utils.utilities import update_server_info, get_server_info, load_config, save_config
from utils.minecraft import is_server_up
from cogs.yeetbot import startlogging

DEFAULT_GUILD_CONFIG = {
    "snoopie_channel_id": 1,
    "snoopie_role_id": 1,
    "snoopie_perms_role_id": 1,
    "mc_perms_role_id": 1,
    "mc_console_perms_role_id": 1,
    "mc_bot_channel_id": 1,
    "mc_chat_channel_id": 1,
    "mc_console_channel_id": 1,
    "ServerInfo": {
        "logging": 0,
        "serverstarting": 0,
        "serverid": "servername",
        "serverport": 25567
    },
    "ServerList":["servername"]
}

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
        
        await bot.change_presence(
            activity=discord.Game(f"Minecraft ✅"),
            status=discord.Status.online
        )
        for guild in bot.guilds:
            update_server_info("serverstarting", 0, guild.id)
            if is_server_up(guild.id):
                print(f"Starting logging for guild {guild.id}")
                await startlogging(bot.get_cog("YeetBot"), YEET)
            else:
                update_server_info("logging", 0)

    except Exception as e:
        print(f"⚠️ Error syncing commands: {e}")
    global config
    updated = False

    for guild in bot.guilds:
        print("checking guild", guild.id)
        if str(guild.id) not in config["guilds"]:
            config["guilds"][str(guild.id)] = DEFAULT_GUILD_CONFIG
            updated = True

    if updated:
        save_config(config)

async def load_cogs():
    await bot.load_extension("cogs.snoopiebot")
    await bot.load_extension("cogs.yeetbot")
    await bot.load_extension("cogs.idsetter")

@bot.event
async def setup_hook():
    await load_cogs()

bot.run(TOKEN)
input("Press Enter to exit...")