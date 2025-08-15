import os, discord
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands
from discord.app_commands import AppCommandError, CheckFailure
from utils.polling import *
from utils.utilities import *
from utils.perms import *
from utils.minecraft import *

load_dotenv()

CONFIG_FILE = os.getenv("CONFIG_FILE")
config = load_config()

RCON_PASSWORD = os.getenv("RCON_PASSWORD")
RCON_PORT = int(os.getenv("RCON_PORT"))
LOGFILE = os.getenv("LOGFILE")
POLLSECONDS = 3

servers_str = os.getenv("SERVERS")
servers = [(x.strip()) for x in servers_str.split(",") if x.strip()] 
        
async def handle_message(self, message):
    if message.author == self.bot.user:
        return
    if message.channel.id == config.get("guilds").get(str(message.guild.id)).get("mc_chat_channel_id"):
        command(f"say <{message.author.global_name}> {message.content}")
    
    elif message.channel.id == config.get("guilds").get(str(message.guild.id)).get("mc_console_channel_id"):
        if has_mc_console_perm(message.guild, message.author):
            response = command(message.content)
            if response.strip():
                await message.channel.send(f"```{response}```")

class YeetBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @commands.Cog.listener()
    @has_mc_perm()
    async def on_message(self, message):
        await handle_message(self, message)

    @app_commands.command(name="start", description="Starts the currently selected minecraft server")
    @has_mc_perm()
    async def start(self, interaction: discord.Interaction):
        if interaction.channel_id != config.get("guilds").get(str(interaction.guild.id)).get("mc_bot_channel_id"):
            await interaction.response.send_message("This channel is not set up for this command", ephemeral=True)
            return
        if is_server_up():
            await interaction.response.send_message("Server is already running!")
            return

        if get_server_info().get("serverstarting"):
            await interaction.response.send_message("Server is already starting up, calm your tits!")
            return

        await interaction.response.defer()
        msg = await interaction.followup.send(f"Starting {get_server_info(interaction.guild.id).get("server_")} server...", wait=True)
        await startserver(self, msg, interaction.guild_id)

    @app_commands.command(name="stop", description="Stops the currently selected minecraft server")
    @has_mc_perm()
    async def stop(self, interaction: discord.Interaction):
        if interaction.channel_id != config.get("guilds").get(str(interaction.guild.id)).get("mc_bot_channel_id"):
            await interaction.response.send_message("This channel is not set up for this command", ephemeral=True)
            return
        if not is_server_up():
            await interaction.response.send_message("Server isn't running? Dumbass")
            return
        command("stop")
        await interaction.response.send_message(f"❌ {get_server_info().get("serverid")} Server is now offline! ❌")
        await self.bot.change_presence(
            activity=discord.Game("Server Offline ❌"),
        )

    @app_commands.command(name="restart", description="Restarts the currently selected minecraft server")
    @has_mc_perm()
    async def restart(self, interaction: discord.Interaction):
        msg = await interaction.original_response()
        if interaction.channel_id != config.get("guilds").get(str(interaction.guild.id)).get("mc_bot_channel_id"):
            await interaction.response.send_message("This channel is not set up for this command", ephemeral=True)
            return

        if not is_server_up() and not get_server_info().get("serverstarting"):
            await interaction.response.send_message("Server wasn't running... I suppose I'll start it though")
            await startserver(self.bot, interaction, interaction.guild_id)
        elif not is_server_up() and get_server_info().get("serverstarting"):
            await interaction.response.send_message("Let it finish starting, goddamn it")
            return
        else:
            command("stop")
            await interaction.response.send_message(f"❌ {get_server_info().get("serverid")} Server is now offline! ❌")
            await self.bot.change_presence(
                activity=discord.Game("Server Offline ❌"),
            )
            await interaction.response.send_message("Server stopped, now starting it again...")
            await startserver(self.bot, msg, interaction.guild_id)

    @app_commands.command(name="server", description="Select a server to set as Active")
    @app_commands.describe(server="Pick a server to set as active...")
    @app_commands.choices(
    server=[
        app_commands.Choice(name="-", value="check"),
        *[app_commands.Choice(name=server, value=server) for server in servers],
        ]
    )
    @has_mc_perm()
    async def server(self, interaction: discord.Interaction, server: app_commands.Choice[str]):
        if interaction.channel_id != config.get("guilds").get(str(interaction.guild.id)).get("mc_bot_channel_id"):
            await interaction.response.send_message("This channel is not set up for this command", ephemeral=True)
            return
        serverid = get_server_info().get("serverid")
        if server.value == "check":
            await interaction.response.send_message(f"Current server is set to: {serverid}")
            return
        else:
            update_server_info("serverid", server.value)
            await interaction.response.send_message(f"Server has been changed to: {server.value}!")
            return

    @app_commands.command(name="ping", description="Responds \"Pong!\" - Used to test connection to the bot")
    async def ping(self, interaction: discord.Interaction):
        if interaction.channel_id != config.get("guilds").get(str(interaction.guild.id)).get("mc_bot_channel_id"):
            await interaction.response.send_message("This channel is not set up for this command", ephemeral=True)
            return
        await interaction.response.send_message("Pong!")

    @app_commands.command(name="status", description="Responds with the current status of the active server")
    @has_mc_perm()
    async def status(self, interaction: discord.Interaction):
        if interaction.channel_id != config.get("guilds").get(str(interaction.guild.id)).get("mc_bot_channel_id"):
            await interaction.response.send_message("This channel is not set up for this command", ephemeral=True)
            return
        await interaction.response.defer()
        message = await interaction.followup.send("Pinging server...", wait=True)
        if is_server_up():
            update_server_info("serverstarting", 0)
            await self.bot.change_presence(
                activity=discord.Game(f"{get_server_info().get("serverid")}✅"),
            )
            await message.edit(content=f"✅ {get_server_info().get("serverid")} Server is online! ✅")
        else:
            await self.bot.change_presence(
                activity=discord.Game("Server Offline ❌"),
            )
            await message.edit(content=f"❌ {get_server_info().get("serverid")} Server is offline! ❌")

    @app_commands.command(name="list", description="Lists the current players on the active server")
    @has_mc_perm()
    async def list(self, interaction: discord.Interaction):
        if interaction.channel_id != config.get("guilds").get(str(interaction.guild.id)).get("mc_bot_channel_id"):
            await interaction.response.send_message("This channel is not set up for this command", ephemeral=True)
            return
        if not is_server_up():
            await interaction.response.send_message("Server isn't on")
            return
        await interaction.response.send_message(f"```{command("list")}```")

    @app_commands.command(name="tps", description="Sends information regarding Ticks Per Second of the server (SkyFactory only)")
    @has_mc_perm()
    async def tps(self, interaction: discord.Interaction):
        if interaction.channel_id != config.get("guilds").get(str(interaction.guild.id)).get("mc_bot_channel_id"):
            await interaction.response.send_message("This channel is not set up for this command", ephemeral=True)
            return
        if not is_server_up():
            await interaction.response.send_message("Server isn't on")
            return
        if get_server_info().get("serverid") != "SkyFactory5":
            await interaction.response.send_message(f"```{command("neoforge tps")}```")
            return
        await interaction.response.send_message(f"```{command("forge tps")}```")

    @app_commands.command(name="say", description="Says a message in minecraft chat")
    @has_mc_perm()
    async def say(self, interaction: discord.Interaction, message: str):
        if interaction.channel_id != config.get("guilds").get(str(interaction.guild.id)).get("mc_bot_channel_id"):
            await interaction.response.send_message("This channel is not set up for this command", ephemeral=True)
            return
        if not is_server_up():
            await interaction.response.send_message("Server isn't on")
            return
        fullmessage = f"say {message}"
        command(fullmessage)

    @app_commands.command(name="help", description="Gives information about possible commands")
    @has_mc_perm()
    async def help(self, interaction: discord.Interaction):
        if interaction.channel_id != config.get("guilds").get(str(interaction.guild.id)).get("mc_bot_channel_id"):
            await interaction.response.send_message("This channel is not set up for this command", ephemeral=True)
            return

        await interaction.response.send_message("```\n"
                       "Commands:\n\n"
                       "/start                 - Start the server\n"
                       "/stop                  - Stop the server\n"
                       "/restart               - Restart the server\n"
                       "/server                - Changes the active server\n"
                       "/ping                  - Ping the bot\n"
                       "/status                - Check server status\n"
                       "/list                  - List players on the server\n"
                       "/tps                   - Get TPS of the server (20 tps is good, anything lower means laggy)\n"
                       "/say <message>         - Say a message in the server chat\n"

                       "/snoopiefact           - Get a random Snoopie fact in your server\n"
                       "/gemini <message>      - Ask Gemini anything!\n"

                       "/setmcpermsrole        - Set the role that can use the minecraft commands\n"
                       "/setmcconsolepermsrole - Set the role that can use the minecraft console commands\n"
                       "/setmcconsolechannel   - Set the channel for Minecraft console messages\n"
                       "/setmcchatchannel      - Set the channel for Minecraft chat messages\n"
                       "/setmcbotchannel       - Set the channel for the Minecraft bot messages\n"
                       "/setfactchannel        - Set the channel for Snoopie facts\n"
                       "/setfactrole           - Set the role to ping for Snoopie facts\n"
                       "/setpermsrole          - Set the role to have Snoopie fact permissions\n"
                       "/help                  - Show this message\n```\n")
                       
    async def cog_app_command_error(self, interaction: discord.Interaction, error: AppCommandError):
        if isinstance(error, CheckFailure):
            if interaction.response.is_done():
                await interaction.followup.send("❌ You don't have permission to use this command.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        else:
            print(f"Unhandled error: {error}")
    
async def setup(bot: commands.Bot):
    await bot.add_cog(YeetBot(bot))