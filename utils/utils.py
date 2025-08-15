import json, os, asyncio, socket, time, discord
from datetime import datetime, timedelta
from google import genai
from dotenv import load_dotenv
from mcrcon import MCRcon
from utils.polling import startlogging

load_dotenv()
CONFIG_FILE = os.getenv("CONFIG_FILE")
GEMINIKEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINIKEY)
YEET = os.getenv("YEET")

SERVER_DIR = os.getenv("SERVER_DIR")
LOG_LOCATION = os.getenv("LOG_LOCATION")
RUNFILE = os.getenv("RUNFILE")
WHITELIST = "whitelist.json"

SLEEPTIME = 0.5
POLLSECONDS = 3

hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
RCON_IP = local_ip
RCON_PASSWORD = os.getenv("RCON_PASSWORD")
RCON_PORT = int(os.getenv("RCON_PORT"))


def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_server_info(guild_id=None):
    if guild_id is None:
        guild_id = YEET
    config = load_config()
    return config["guilds"][str(guild_id)].get("ServerInfo", {})

def update_server_info(key, value, guild_id=None):
    if guild_id is None:
        guild_id = YEET
    config = load_config()
    guild = config["guilds"][str(guild_id)]
    if "ServerInfo" not in guild:
        guild["ServerInfo"] = {}
    guild["ServerInfo"][key] = value
    save_config(config)

def get_facts() -> str:
    with open("facts.txt", "r", encoding="utf-8") as f:
        return f.read()

def set_random_fact(new_fact: str):
    facts_file = "facts.txt"
    try:
        with open(facts_file, "r", encoding="utf-8") as f:
            facts = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        facts = []

    facts.insert(0, new_fact)
    facts = facts[:60]

    with open(facts_file, "w", encoding="utf-8") as f:
        f.write("\n".join(facts) + "\n")

async def wait_until_10am():
    now = datetime.now()
    target = now.replace(hour=10, minute=0, second=0, microsecond=0)
    #target = now + timedelta(seconds=10)  # For testing, set to 10 seconds later
    if now >= target:
        target += timedelta(days=1)
    await asyncio.sleep((target - now).total_seconds())

async def wait_until_serverup():
    now = datetime.now()
    while not is_server_up():
        await asyncio.sleep(3)
        if (datetime.now() - now).total_seconds() > 300:
            return
    
def ask_gemini(prompt: str) -> str:
    print(f"Sending prompt to Gemini")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    print("Received response from Gemini: ", response.text)
    return response.text

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

async def animate(msg):
    serverid = get_server_info().get("serverid")
    dots = -1
    while get_server_info().get("serverstarting"):
        dots = (dots + 1) % 3
        await msg.edit(content=f"Starting {serverid} server{'.' * (dots + 1)}")
        await asyncio.sleep(SLEEPTIME)

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
            if not get_server_info().get("logging"):
                await startlogging(self, guild_id)
            update_server_info("serverstarting", 0)
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