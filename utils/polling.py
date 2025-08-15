import asyncio, os, time, json, threading
from utils.utils import *

console_buffer = []

def poll_log_file(filepath, loop, console, chat, bot):
    global usernames
    usernames = get_usernames()
    last_position = os.path.getsize(filepath)

    while True:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                f.seek(0, os.SEEK_END)
                file_size = f.tell()

                if file_size < last_position:
                    # Log rotated or truncated
                    last_position = 0

                f.seek(last_position)
                new_lines = f.readlines()
                last_position = f.tell()

            for line in new_lines:
                line = line.strip()
                if line:
                    asyncio.run_coroutine_threadsafe(
                        send_log_to_discord(line, console, chat, bot),
                        loop
                    )

        except Exception as e:
            print(f"[ERROR] Log reader crashed: {e}")

        time.sleep(1)

async def send_log_to_discord(message, consolechannel, chatchannel, botchannel):
    usernames = get_usernames()
    if not message.strip():
        return
    if consolechannel:
        if "NetworkRegistry/]: No registration for payload oritech:particles; refusing to decode." in message and "<" not in message:
            return
        console_buffer.append(message)
    if chatchannel:
        if "<" in message and ">" in message and "[Rcon] <" not in message:
            newmessage = message[message.index('<'):]
            await chatchannel.send(f"```{newmessage}```")
    if botchannel:
        if "[Server thread/INFO] [net.minecraft.server.MinecraftServer/]: " in message and "<" not in message:
            newmessage = message[message.index('[Server thread/INFO] [net.minecraft.server.MinecraftServer/]:') + 62:]
            if newmessage.startswith(tuple(usernames)):
                await botchannel.send(f"```{newmessage}```")
                return

def get_usernames():
    path = build_whitelist(get_server_info().get("serverid"))
    with open(path, "r") as f:
        data = json.load(f)
    usernames = [entry["name"] for entry in data]
    return usernames

# Start buffer flushing coroutine once at bot startup
async def start_log_buffer_task(bot, consolechannel):
    while True:
        if console_buffer:
            joined = "\n".join(console_buffer)
            if len(joined) > 2000:
                left = joined[:1900]
                right = joined[1900:]
                console_buffer.append(right)
                joined = left
            console_buffer.clear()
            await consolechannel.send(f"```{joined}```")
        await asyncio.sleep(1)  # flush every 1 second

async def startlogging(self, guild_id):
    update_server_info("logging", 1)
    loop = asyncio.get_running_loop()
    config = load_config()

    botchannel = await self.bot.fetch_channel(config.get("guilds").get(str(guild_id)).get("mc_bot_channel_id"))
    console = await self.bot.fetch_channel(config.get("guilds").get(str(guild_id)).get("mc_console_channel_id"))
    chat = await self.bot.fetch_channel(config.get("guilds").get(str(guild_id)).get("mc_chat_channel_id"))

    threading.Thread(target=poll_log_file, args=(build_log(get_server_info().get("serverid")), loop, console, chat, botchannel), daemon=True).start()
    loop.create_task(start_log_buffer_task(self.bot, console))