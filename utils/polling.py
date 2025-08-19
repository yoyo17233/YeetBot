import asyncio, os, time, json, threading
from utils.utilities import get_server_info, update_server_info, load_config

VERBOSE = True

console_buffer = []

def poll_log_file(guild_id, loop, console, chat, bot):
    from utils.minecraft import build_log
    filepath = build_log(get_server_info(guild_id).get("serverid"))
    last_position = os.path.getsize(filepath)
    if(VERBOSE): print("reading...")
    while True:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                f.seek(0, os.SEEK_END)
                file_size = f.tell()

                if file_size < last_position:
                    last_position = 0

                f.seek(last_position)
                new_lines = f.readlines()
                last_position = f.tell()

            for line in new_lines:
                if(VERBOSE): print("newlines found")
                line = line.strip()
                if line:
                    if(VERBOSE): print("line found = " + line)
                    asyncio.run_coroutine_threadsafe(
                        send_log_to_discord(guild_id, line, console, chat, bot),
                        loop
                    )

        except Exception as e:
            print(f"[ERROR] Log reader crashed: {e}")

        time.sleep(1)

async def send_log_to_discord(guild_id, message, consolechannel, chatchannel, botchannel):
    if(VERBOSE): print("sending line to discord...")
    usernames = get_usernames(guild_id)
    if(VERBOSE): print("usernames are: " + str(usernames))
    if(VERBOSE): print("1")
    if not message.strip():
        return
    if(VERBOSE): print("2")
    if consolechannel:
        if "NetworkRegistry/]: No registration for payload oritech:particles; refusing to decode." in message and "<" not in message:
            return
        if(VERBOSE): print("3")
        console_buffer.append(message)
    if chatchannel:
        if(VERBOSE): print("4")
        if "<" in message and ">" in message and "[Rcon] <" not in message:
            if(VERBOSE): print("5")
            newmessage = message[message.index('<')+1:]
            if(VERBOSE): print("newmessage is: " + newmessage)
            if(VERBOSE): print("usernames are: " + str(usernames))
            if newmessage.startswith(tuple(usernames)):
                if(VERBOSE): print("6")
                await chatchannel.send(f"```{message[message.index('<'):]}```")
                return
    if botchannel:
        if "[Server thread/INFO] [net.minecraft.server.MinecraftServer/]: " in message and "<" not in message:
            newmessage = message[message.index('[Server thread/INFO] [net.minecraft.server.MinecraftServer/]:') + 62:]
            if newmessage.startswith(tuple(usernames)):
                if(get_server_info(guild_id).get("deathmsg") == "bot"):
                    await botchannel.send(f"```{newmessage}```")
                    return
                elif(get_server_info(guild_id).get("deathmsg") == "chat"):
                    await chatchannel.send(f"```{newmessage}```")
                    return
                else:
                    print("server has no setup location for death messages")
                    return

def get_usernames(guild_id):
    from utils.minecraft import build_whitelist
    path = build_whitelist(get_server_info(guild_id).get("serverid"))
    with open(path, "r") as f:
        data = json.load(f)
    usernames = [entry["name"] for entry in data]
    return usernames

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
        await asyncio.sleep(1)

async def startlogging(self, guild_id):
    print("attempting to start logging")
    update_server_info("logging", 1)
    print("logging started")
    loop = asyncio.get_running_loop()
    config = load_config()

    botchannel = await self.bot.fetch_channel(config.get("guilds").get(str(guild_id)).get("mc_bot_channel_id"))
    console = await self.bot.fetch_channel(config.get("guilds").get(str(guild_id)).get("mc_console_channel_id"))
    chat = await self.bot.fetch_channel(config.get("guilds").get(str(guild_id)).get("mc_chat_channel_id"))

    threading.Thread(target=poll_log_file, args=(guild_id, loop, console, chat, botchannel), daemon=True).start()
    loop.create_task(start_log_buffer_task(self.bot, console))