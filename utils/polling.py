import asyncio, os, time, json, threading
from utils.utilities import get_server_info, update_server_info, load_config
from collections import defaultdict

VERBOSE = False

console_buffer = []
log_dict = defaultdict(list)

console_emptier = 0

def poll_log_file(guild_id, loop, console, chat, bot):
    from utils.minecraft import build_log
    filepath = build_log(get_server_info(guild_id).get("serverid"))
    last_position = os.path.getsize(filepath)
    if(VERBOSE): print("reading... " + filepath)
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
                if(VERBOSE): print("newlines found in guildid " + guild_id)
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
        print("adding to logdict")
        log_dict[guild_id].append(message)
        print(f"Guild {guild_id} now has {len(log_dict[guild_id])} messages.")
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
        print("wpiesports checking message " + message + " for \" INFO]:\", and \"<\" not in message. Checking serverid " + get_server_info(guild_id).get("serverid") + " against WPIEsports")
        if "] [Server thread/INFO]: " in message and "<" not in message and get_server_info(guild_id).get("serverid") == "WPIEsports":
            newmessage = message[message.index('] [Server thread/INFO]: ') + 24:]
            print("oldmessage = " + message)
            print("newmessage = " + newmessage)
            if newmessage.startswith(tuple(u + " " for u in usernames)) and not ":" in newmessage :
                if(VERBOSE): print("6")
                await chatchannel.send(f"```{newmessage}```")
                return


def get_usernames(guild_id):
    from utils.minecraft import build_whitelist
    path = build_whitelist(get_server_info(guild_id).get("serverid"))
    with open(path, "r") as f:
        data = json.load(f)
    usernames = [entry["name"] for entry in data]
    return usernames

#async def start_log_buffer_task():
#    while True:
#        if log_dict:
#            print(log_dict)
#            return
#            joined = "\n".join(console_buffer)
#            if len(joined) > 2000:
#                left = joined[:1900]
#                right = joined[1900:]
#                console_buffer.append(right)
#                joined = left
#            console_buffer.clear()
#            await consolechannel.send(f"```{joined}```")
#        await asyncio.sleep(1)

async def start_log_buffer_task(self):
    config = load_config()
    while True:
        for guild_id, messages in log_dict.items():
            # Send the grouped messages to the appropriate channels
            console_channel = await self.bot.fetch_channel(config.get("guilds").get(str(guild_id)).get("mc_console_channel_id"))

            # Join the messages and send them to Discord (adjust size limit if needed)
            joined_messages = "\n".join(messages)
            if len(joined_messages) > 2000:
                # Split the message if it's too long (Discord message limit is 2000 characters)
                part1 = joined_messages[:1900]
                part2 = joined_messages[1900:]
                await console_channel.send(f"```{part1}```")
                await console_channel.send(f"```{part2}```")
            else:
                await console_channel.send(f"```{joined_messages}```")

        # Clear the log_dict after sending
        log_dict.clear()
        await asyncio.sleep(1)

async def startlogging(self, guild_id):
    #print("attempting to start logging")
    update_server_info("logging", 1, guild_id)
    loop = asyncio.get_running_loop()
    #print("this was fine 1")
    config = load_config()
    #print("this was fine 2")

    botchannel = await self.bot.fetch_channel(config.get("guilds").get(str(guild_id)).get("mc_bot_channel_id"))
    console = await self.bot.fetch_channel(config.get("guilds").get(str(guild_id)).get("mc_console_channel_id"))
    chat = await self.bot.fetch_channel(config.get("guilds").get(str(guild_id)).get("mc_chat_channel_id"))
    #print("this was fine 3")

    threading.Thread(target=poll_log_file, args=(guild_id, loop, console, chat, botchannel), daemon=True).start()
    print("this was fine 4")
    loop.create_task(start_log_buffer_task(self))
    print("this was fine 5")