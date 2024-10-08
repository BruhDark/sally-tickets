import discord
from discord.ext import commands
import aiohttp
import os
import dotenv
import traceback
from datetime import datetime
from resources import aesthetic

dotenv.load_dotenv()
url = os.getenv("WEBHOOK_URL")
roblox_log_url = os.getenv("ROBLOX_LOG_WEBHOOK_URL")


async def send(webhook_url=url, *args, **kwargs):
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(webhook_url, session=session)
        return await webhook.send(*args, **kwargs)


def parse_status(status: str) -> tuple[str, discord.Color]:
    if status == "success":
        return "<:Operational:882404710148083724>", aesthetic.Colors.success
    elif status == "error":
        return "<:MajorOutage:882404641286000681>", aesthetic.Colors.error
    elif status == "warning":
        return "<:PartialOutage:882404755949895730>", discord.Color.orange()
    elif status == "pending":
        return "<a:load:881972395626348648>", discord.Color.greyple()
    else:
        return status, aesthetic.Colors.secondary


async def send_log(user: discord.Member | int, actions: list[str], status: str) -> tuple[int, discord.Embed]:
    embed = discord.Embed()
    if isinstance(user, discord.Member):
        embed.title = f"<:link:986648044525199390> Verification process status for: {user} ({user.id})"
    else:
        embed.title = f"<:link:986648044525199390> Verification process status for: {user}"

    embed.timestamp = datetime.utcnow()
    embed.description = f"Started: {discord.utils.format_dt(datetime.utcnow(), 'R')}"

    p_status, p_color = parse_status(status)
    if status != "pending":
        embed.description = embed.description + \
            f", Finished: {discord.utils.format_dt(datetime.utcnow(), 'R')}"

    embed.color = p_color
    embed.add_field(name="Real-time Status",
                    value=p_status, inline=True)
    embed.add_field(name="Last Action",
                    value=actions[-1] + f" - {discord.utils.format_dt(datetime.utcnow(), 'R')}", inline=True)
    embed.add_field(name="Past Status", value="None", inline=True)
    embed.add_field(name="Detailed Actions",
                    value=", ".join(actions), inline=False)
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(url, session=session)
        webhook_message = await webhook.send(embed=embed, wait=True)
        return webhook_message.id, embed


async def update_log(webhook_message: int, actions: list[str], status: str, embed: discord.Embed) -> tuple[int, discord.Embed]:
    p_status, p_color = parse_status(status)
    if status == "success" or status == "error":
        embed.description = embed.description + \
            f", Finished: {discord.utils.format_dt(datetime.utcnow(), 'R')}"

    embed.fields[2].value = embed.fields[0].value
    embed.fields[0].value = p_status

    embed.color = p_color
    embed.fields[1].value = actions[-1] + \
        f" - {discord.utils.format_dt(datetime.utcnow(), 'R')}"
    embed.fields[3].value = embed.fields[3].value + ", " + ", ".join(actions)
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(url, session=session)
        webhook_message = await webhook.edit_message(webhook_message, embed=embed)
        return webhook_message.id, embed


async def send_join_log(embed: discord.Embed):
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(roblox_log_url, session=session)
        await webhook.send(embed=embed)


async def send_command_error(ctx: commands.Context | discord.ApplicationContext, error: Exception):
    async with aiohttp.ClientSession() as session:

        webhook = discord.Webhook.from_url(url, session=session)
        tb = ''.join(traceback.format_exception(
            error, error, error.__traceback__))
        tb = tb + "\n"

        embed = discord.Embed(
            title=f"{aesthetic.Emojis.error} Something went wrong", color=aesthetic.Colors.error, timestamp=datetime.utcnow())
        embed.description = f"```py\n{tb}```"

        embed.add_field(name="Author", value=f"{ctx.author} ({ctx.author.id})")
        embed.add_field(
            name="Command", value=f"{ctx.command.qualified_name}")

        embed.add_field(
            name="Guild", value=f"{ctx.guild.name} ({ctx.guild.id})" if ctx.guild else "None")

        await webhook.send(embed=embed)


async def send_verification_error(interaction: discord.Interaction, error):
    async with aiohttp.ClientSession() as session:

        webhook = discord.Webhook.from_url(url, session=session)
        tb = ''.join(traceback.format_exception(
            error, error, error.__traceback__))
        tb = tb + "\n"
        tb = tb[-4050:]

        embed = discord.Embed(
            title=f"{aesthetic.Emojis.error} Verification failed", color=aesthetic.Colors.error, timestamp=datetime.utcnow())
        embed.description = f"```py\n{tb}```"

        embed.add_field(
            name="Author", value=f"{interaction.user} ({interaction.user.id})")
        await webhook.send(embed=embed)
