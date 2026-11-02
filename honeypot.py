import logging

import discord

import config


logger = logging.getLogger(__name__)


async def _report_error(
    log_channel: discord.TextChannel | None,
    message: str,
) -> None:
    if log_channel is None:
        return

    try:
        await log_channel.send(message)
    except (discord.Forbidden, discord.HTTPException):
        logger.exception("Failed to send a honeypot status message.")


async def handle_message(message: discord.Message) -> bool:
    """Handle honeypot messages, returning whether the message was consumed."""
    guild = message.guild
    if message.author.bot:
        return False

    honeypot_channel_id = (
        config.get_honeypot_channel(guild.id) if guild is not None else None
    )
    if (
        guild is None
        or honeypot_channel_id is None
        or message.channel.id != int(honeypot_channel_id)
    ):
        return False

    member = message.author
    if member.id == guild.owner_id or member.guild_permissions.administrator:
        return False

    guild_config = config.get_guild_config(guild.id)
    staff_role_id = guild_config.get(
        "staff_role_id",
        guild_config.get("staffrole"),
    )
    if staff_role_id is None:
        staff_role_id = config.load_config().get("staffrole")

    if staff_role_id is not None and any(
        str(role.id) == str(staff_role_id) for role in member.roles
    ):
        return False

    log_channel_id = config.get_honeypot_logs_channel(guild.id)
    log_channel = guild.get_channel(int(log_channel_id)) if log_channel_id else None

    if log_channel is not None:
        message_content = message.content[:500]
        if not message_content and message.attachments:
            attachment_names = ", ".join(
                attachment.filename for attachment in message.attachments
            )
            message_content = f"Archivo(s) adjunto(s): {attachment_names}"[:500]
        elif not message_content:
            message_content = "*(empty)*"

        embed = discord.Embed(
            title="Honeypot Trigger Detected",
            color=0xE74C3C,
            description="An action was detected in the honeypot channel.",
        )
        embed.add_field(
            name="User",
            value=f"{member.name} (`{member.id}`)",
            inline=False,
        )
        embed.add_field(name="Channel", value=message.channel.mention, inline=False)
        embed.add_field(
            name="Message",
            value=message_content,
            inline=False,
        )
        embed.add_field(name="Action", value="Automatic softban", inline=False)

        try:
            await log_channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            logger.exception("Failed to send a honeypot trigger log.")

    try:
        await guild.ban(
            member,
            reason="Automatic softban: wrote in honeypot channel",
            delete_message_seconds=86400,
        )
        await guild.unban(member, reason="End of honeypot softban")
    except discord.Forbidden:
        logger.exception("Bot lacks permission to softban %s.", member)
        await _report_error(
            log_channel,
            f"⚠️ I don't have permission to softban {member.mention}.",
        )
    except discord.HTTPException as error:
        logger.exception("Failed to softban %s.", member)
        await _report_error(
            log_channel,
            f"⚠️ Error softbanning {member.mention}: `{error}`",
        )

    return True
