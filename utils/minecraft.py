import os, asyncio, socket, time, discord
from dotenv import load_dotenv
from discord import app_commands
from mcrcon import MCRcon
from utils.utilities import update_server_info, animate, get_server_info

load_dotenv()

SERVER_DIR = os.getenv("SERVER_DIR")
LOG_LOCATION = os.getenv("LOG_LOCATION")
RUNFILE = os.getenv("RUNFILE")
WHITELIST = "whitelist.json"

POLLSECONDS = 3

hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
RCON_IP = local_ip
RCON_PASSWORD = os.getenv("RCON_PASSWORD")

def is_server_up(guild_id):
    port = get_server_info(guild_id).get("serverport")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.1)
        result = sock.connect_ex(('127.0.0.1', port))
        return result == 0

def build_run(text):
    return f'start "" "{SERVER_DIR}{text}/{RUNFILE}"'

def build_log(text):
    return f"{SERVER_DIR}{text}/{LOG_LOCATION}"

def build_whitelist(text):
    return f"{SERVER_DIR}{text}/{WHITELIST}"

def command(command_name, guild_id):
        try:
            print(f"Executing command: {command_name}")
            port = get_server_info(guild_id).get("serverport")
            rconport = port + 10
            with MCRcon(RCON_IP, RCON_PASSWORD, port=rconport) as mcr:
                response = mcr.command(command_name)
            print(f"Command response: {response}")
            return response
        except Exception as e:
            return e
        
async def server_status_check(self, msg, guild_id):
    update_server_info("serverstarting", 1)
    starttime = time.time()
    asyncio.create_task(animate(msg))
    while get_server_info(guild_id).get("serverstarting"):
        if time.time() - starttime > 300:
            await msg.edit(content=f"❌ Server failed to start within 5 minutes.")
            update_server_info("serverstarting", 0, guild_id)
            return
        if is_server_up(guild_id):
            print("server is up")
            if not get_server_info(guild_id).get("logging"):
                print("log is off, starting log")
                from utils.polling import startlogging
                await startlogging(self, guild_id)
            print("serverstarting setting to 0...")
            update_server_info("serverstarting", 0)
            print("serverstarting successfully set to 0")
            await msg.edit(content=f"✅ {get_server_info(guild_id).get('serverid')} Server is now online! ✅")
            #await self.bot.change_presence(activity=discord.Game(f"{get_server_info().get("serverid")}✅"))
            return
        await asyncio.sleep(POLLSECONDS)

async def startserver(self, msg, guild_id):
    print("starting " + build_run(get_server_info().get("serverid")) + " server")
    await asyncio.create_subprocess_shell(
        build_run(get_server_info().get("serverid")),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await server_status_check(self, msg, guild_id)