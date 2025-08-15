import os, asyncio, socket, time, discord
from dotenv import load_dotenv
from mcrcon import MCRcon
from utils.utilities import update_server_info, animate, get_server_info

load_dotenv()
CONFIG_FILE = os.getenv("CONFIG_FILE")

SERVER_DIR = os.getenv("SERVER_DIR")
LOG_LOCATION = os.getenv("LOG_LOCATION")
RUNFILE = os.getenv("RUNFILE")
WHITELIST = "whitelist.json"

POLLSECONDS = 3

hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
RCON_IP = local_ip
RCON_PASSWORD = os.getenv("RCON_PASSWORD")
RCON_PORT = int(os.getenv("RCON_PORT"))

def is_server_up():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.1)
        result = sock.connect_ex(('127.0.0.1', 25565))
        return result == 0

def build_run(text):
    return f'start "" "{SERVER_DIR}{text}/{RUNFILE}"'

def build_log(text):
    return f"{SERVER_DIR}{text}/{LOG_LOCATION}"

def build_whitelist(text):
    return f"{SERVER_DIR}{text}/{WHITELIST}"

def command(command_name):
        try:
            print(f"Executing command: {command_name}")
            with MCRcon(RCON_IP, RCON_PASSWORD, port=RCON_PORT) as mcr:
                response = mcr.command(command_name)
            print(f"Command response: {response}")
            return response
        except Exception as e:
            return
        
async def server_status_check(self, msg, guild_id):
    update_server_info("serverstarting", 1)
    starttime = time.time()
    asyncio.create_task(animate(msg))
    while get_server_info().get("serverstarting"):
        if time.time() - starttime > 300:
            await msg.edit(content=f"❌ Server failed to start within 5 minutes.")
            update_server_info("serverstarting", 0)
            return
        if is_server_up():
            print("server is up")
            if not get_server_info().get("logging"):
                print("log is off, starting log")
                from utils.polling import startlogging
                await startlogging(self, guild_id)
            print("serverstarting setting to 0...")
            update_server_info("serverstarting", 0)
            print("serverstarting successfully set to 0")
            await msg.edit(content=f"✅ {get_server_info().get("serverid")} Server is now online! ✅")
            await self.bot.change_presence(activity=discord.Game(f"{get_server_info().get("serverid")}✅"))
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