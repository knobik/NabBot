from typing import List, Optional

import discord
from discord.abc import PrivateChannel, Messageable
from discord.ext import commands
import re

from config import lite_servers
from .messages import EMOJI

# Discord length limit
CONTENT_LIMIT = 2000
DESCRIPTION_LIMIT = 2048
FIELD_NAME_LIMIT = 256
FIELD_VALUE_LIMIT = 1024
FIELD_AMOUNT = 25


def get_role(guild: discord.Guild, role_id: int = None, role_name: str = None) -> Optional[discord.Role]:
    """Returns a role matching the id in a server"""
    if guild is None:
        raise ValueError("guild is None")
    if role_id is None and role_name is None:
        raise ValueError("Either role_id or role_name must be specified")
    for role in guild.roles:
        if role.id == role_id or role.name.lower() == role_name.lower():
            return role
    return None


def get_role_list(guild: discord.Guild) -> List[discord.Role]:
    """Lists all role within the discord server and returns to caller."""
    roles = []
    for role in guild.roles:
        # Ignore @everyone and NabBot
        if role.name not in ["@everyone", "Nab Bot"]:
            roles.append(role)
    return roles


def get_user_color(user: discord.Member, guild: discord.Guild) -> discord.Colour:
    """Gets the user's color based on the highest role with a color"""
    # If it's a PM, server will be none
    if guild is None:
        return discord.Colour.default()
    member = guild.get_member(user.id)  # type: discord.Member
    if member is not None:
        return member.colour
    return discord.Colour.default()


def get_region_string(region: discord.ServerRegion) -> str:
    """Returns a formatted string for a given ServerRegion"""
    regions = {"us-west": EMOJI[":flag_us:"]+"US West",
               "us-east": EMOJI[":flag_us:"]+"US East",
               "us-central": EMOJI[":flag_us:"]+"US Central",
               "us-south": EMOJI[":flag_us:"]+"US South",
               "eu-west": EMOJI[":flag_eu:"]+"West Europe",
               "eu-central": EMOJI[":flag_eu:"]+"Central Europe",
               "singapore": EMOJI[":flag_sg:"]+"Singapore",
               "london": EMOJI[":flag_gb:"]+"London",
               "sydney": EMOJI[":flag_au:"]+"Sydney",
               "amsterdam": EMOJI[":flag_nl:"]+"Amsterdam",
               "frankfurt": EMOJI[":flag_de:"]+"Frankfurt",
               "brazil": EMOJI[":flag_br:"]+"Brazil"
               }
    return regions.get(str(region), str(region))


def is_private(channel: Messageable) -> bool:
    return isinstance(channel, PrivateChannel)


def clean_string(ctx: commands.Context, string: str) -> str:
    """Turns mentions into plain text

    For message object, there's already a property that odes this: message.clean_content"""
    def repl_channel(match):
        channel_id = match.group(0).replace("<", "").replace("#", "").replace(">", "")
        channel = ctx.message.guild.get_channel(channel_id)
        return "#deleted_channel" if channel is None else "#"+channel.name

    def repl_role(match):
        role_id = match.group(0).replace("<", "").replace("@", "").replace("&", "").replace(">", "")
        role = get_role(ctx.message.guild, role_id)
        return "@deleted_role" if role is None else "@"+role.name

    def repl_user(match):
        user_id = match.group(0).replace("<", "").replace("@", "").replace("!", "").replace(">", "")
        user = ctx.message.guild.get_member(user_id)
        return "@deleted_role" if user is None else "@" + user.display_name
    # Find channel mentions:
    string = re.sub(r"<#\d+>", repl_channel, string)
    # Find role mentions
    string = re.sub(r"<@&\d+>", repl_role, string)
    # Find user mentions
    string = re.sub(r"<@!\d+>", repl_user, string)
    string = re.sub(r"<@\d+>", repl_user, string)
    # Clean @everyone and @here
    return string.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")


def is_lite_mode(ctx: commands.Context) -> bool:
    """Checks if the current command context is limited to lite mode.
    
    If the guild is in the lite_guilds list, the context is in lite mode.
    If the guild is in private message, and the message author is in at least ONE guild that is not in lite_guilds, 
    then context is not lite"""
    if is_private(ctx.message.channel):
        for g in ctx.bot.get_user_guilds(ctx.message.author.id):
            if g.id not in lite_servers:
                return False
    else:
        return ctx.message.guild in lite_servers
