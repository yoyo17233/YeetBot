import discord
from discord.app_commands import CheckFailure
from discord import app_commands
from utils.utils import load_config

config = load_config()

def has_snoopie_perm():
    async def predicate(interaction: discord.Interaction) -> bool:
        guild_id = str(interaction.guild.id)
        perms_role_id = config.get("guilds", {}).get(guild_id, {}).get("snoopie_perms_role_id")

        if not perms_role_id:
            raise CheckFailure("Permissions role not set.")

        member = interaction.user
        if isinstance(member, discord.Member):
            if any(role.id == perms_role_id for role in member.roles):
                return True

        raise CheckFailure("You don't have permission to use this command.")
    return app_commands.check(predicate)

def has_mc_perm():
    async def predicate(interaction: discord.Interaction) -> bool:
        perm_id = config.get("guilds").get(str(interaction.guild.id)).get("mc_perms_role_id")

        if not perm_id:
            raise CheckFailure("Permissions role not set.")

        member = interaction.user
        if isinstance(member, discord.Member):
            if any(role.id == perm_id for role in member.roles):
                return True

        raise CheckFailure("You don't have permission to use this command.")
    return app_commands.check(predicate)

def has_mc_console_perm():
    async def predicate(interaction: discord.Interaction) -> bool:
        perm_id = config.get("guilds").get(str(interaction.guild.id)).get("mc_console_perms_role_id")

        if not perm_id:
            raise CheckFailure("Permissions role not set.")

        member = interaction.user
        if isinstance(member, discord.Member):
            if any(role.id == perm_id for role in member.roles):
                return True

        raise CheckFailure("You don't have permission to use this command.")
    return app_commands.check(predicate)

def has_mc_console_perm(guild, member):
    perm_id = config.get("guilds").get(str(guild.id)).get("mc_console_perms_role_id")
    if not perm_id:
        raise CheckFailure("Permissions role not set.")
    if isinstance(member, discord.Member):
        if any(role.id == perm_id for role in member.roles):
            return True
    return False

def is_admin():
    async def predicate(interaction: discord.Interaction) -> bool:
        config = load_config()
        if interaction.user.id in config.get("admins"):
            return True
        else:
            raise CheckFailure("You don't have permission to use this command.")
    return app_commands.check(predicate)

def check_is_admin(interaction: discord.Interaction) -> bool:
    if interaction.author_id in config.get("admins"):
        return True
    else:
        return False
    

    
