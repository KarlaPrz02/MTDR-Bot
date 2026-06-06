import os
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from minecraft_ping import check_minecraft_server
import storage
import config


env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

TOKEN = os.getenv("TOKEN")


class MinecraftArchiveBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()

        super().__init__(
            command_prefix="!",
            intents=intents,
        )

    async def setup_hook(self):
        print("Running setup_hook...")

        self.tree.clear_commands(guild=None)
        self.tree.add_command(ip_group)
        self.tree.add_command(config_group)
        self.tree.add_command(help_command)
        synced = await self.tree.sync()

        print("Slash commands synced:")
        for command in synced:
            print(f"- /{command.name}")


bot = MinecraftArchiveBot()


ip_group = app_commands.Group(
    name="ip",
    description="Manage archived Minecraft server IPs",
)


config_group = app_commands.Group(
    name="config",
    description="Configure bot settings for this server",
)


def create_success_embed(title: str, description: str | None = None) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=description,
        color=discord.Color.green(),
    )


def create_error_embed(title: str, description: str | None = None) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=description,
        color=discord.Color.red(),
    )


def create_warning_embed(title: str, description: str | None = None) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=description,
        color=discord.Color.orange(),
    )


def create_info_embed(title: str, description: str | None = None) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=description,
        color=discord.Color.blurple(),
    )


def add_server_fields(
    embed: discord.Embed,
    name: str,
    address: str,
    result: dict | None = None,
) -> None:
    embed.add_field(name="Name", value=f"`{name}`", inline=True)
    embed.add_field(name="Address", value=f"`{address}`", inline=True)

    if result is None:
        return

    status = "Online" if result.get("online") else "Offline"
    embed.add_field(name="Status", value=status, inline=True)

    if result.get("latency") is not None:
        embed.add_field(name="Latency", value=f"`{result['latency']} ms`", inline=True)

    if result.get("players") is not None:
        embed.add_field(name="Players", value=f"`{result['players']}`", inline=True)

    if result.get("version") is not None:
        embed.add_field(name="Version", value=f"`{result['version']}`", inline=True)

    if result.get("error") is not None and not result.get("online"):
        embed.add_field(name="Error", value=f"`{result['error']}`", inline=False)


def format_server_status(info: dict) -> str:
    last_online = info.get("last_online")

    if last_online is True:
        status = "Online"
    elif last_online is False:
        status = "Offline"
    else:
        status = "Unchecked"

    value = (
        f"Address: `{info['address']}`\n"
        f"Status: `{status}`"
    )

    if info.get("last_latency") is not None:
        value += f"\nLatency: `{info['last_latency']} ms`"

    if info.get("last_players") is not None:
        value += f"\nPlayers: `{info['last_players']}`"

    if info.get("last_version") is not None:
        value += f"\nVersion: `{info['last_version']}`"

    return value


@ip_group.command(
    name="add",
    description="Add a Minecraft IP to the archive",
)
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.describe(
    name="Server name",
    address="IP or domain. Example: play.example.net or play.example.net:25565",
)
async def ip_add(
    interaction: discord.Interaction,
    name: str,
    address: str,
):
    name = name.lower().strip()
    address = address.strip()

    if interaction.guild_id is None:
        embed = create_error_embed(
            title="Command unavailable",
            description="This command can only be used inside a server.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    await interaction.response.defer()

    added = storage.add_server(
        guild_id=interaction.guild_id,
        channel_id=interaction.channel_id,
        name=name,
        address=address,
        added_by=interaction.user.id,
    )

    if not added:
        embed = create_error_embed(
            title="Server already exists",
            description=f"A server with the name `{name}` already exists.",
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    result = await check_minecraft_server(address)

    storage.update_server_status(
        guild_id=interaction.guild_id,
        name=name,
        online=result["online"],
        latency=result["latency"],
        players=result["players"],
        version=result["version"],
        error=result["error"],
    )

    if result["online"]:
        embed = create_success_embed(
            title="Server added",
            description="The server has been successfully added to the archive.",
        )
    else:
        embed = create_warning_embed(
            title="Server added",
            description="The server has been saved, but it is currently not responding.",
        )

    add_server_fields(embed, name, address, result)

    await interaction.followup.send(embed=embed)


@ip_group.command(
    name="remove",
    description="Remove a saved IP",
)
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.describe(
    name="Name of the server you want to remove",
)
async def ip_remove(
    interaction: discord.Interaction,
    name: str,
):
    name = name.lower().strip()

    if interaction.guild_id is None:
        embed = create_error_embed(
            title="Command unavailable",
            description="This command can only be used inside a server.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    removed = storage.remove_server(
        guild_id=interaction.guild_id,
        name=name,
    )

    if removed is None:
        embed = create_error_embed(
            title="Server not found",
            description=f"No saved server was found with the name `{name}`.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    embed = create_success_embed(
        title="Server removed",
        description="The server has been successfully removed from the archive.",
    )

    embed.add_field(name="Name", value=f"`{name}`", inline=True)
    embed.add_field(name="Removed address", value=f"`{removed['address']}`", inline=True)

    await interaction.response.send_message(embed=embed)


@ip_group.command(
    name="edit",
    description="Edit the name or IP of a saved server",
)
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.describe(
    name="Current server name",
    new_name="New server name",
    new_address="New IP or domain",
)
async def ip_edit(
    interaction: discord.Interaction,
    name: str,
    new_name: str | None = None,
    new_address: str | None = None,
):
    name = name.lower().strip()

    if new_name:
        new_name = new_name.lower().strip()

    if new_address:
        new_address = new_address.strip()

    if interaction.guild_id is None:
        embed = create_error_embed(
            title="Command unavailable",
            description="This command can only be used inside a server.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if new_name is None and new_address is None:
        embed = create_error_embed(
            title="Insufficient data",
            description="You must change either the server name or the server address.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    edited = storage.edit_server(
        guild_id=interaction.guild_id,
        name=name,
        new_name=new_name,
        new_address=new_address,
    )

    if edited is None:
        embed = create_error_embed(
            title="Server not found",
            description=f"No saved server was found with the name `{name}`.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if edited == "NAME_EXISTS":
        embed = create_error_embed(
            title="Name unavailable",
            description=f"A server named `{new_name}` already exists.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    final_name = new_name if new_name else name

    embed = create_success_embed(
        title="Server updated",
        description="The server data has been updated successfully.",
    )

    embed.add_field(name="Name", value=f"`{final_name}`", inline=True)
    embed.add_field(name="Address", value=f"`{edited['address']}`", inline=True)

    await interaction.response.send_message(embed=embed)


@ip_group.command(
    name="list",
    description="Show saved IPs and check their current status",
)
async def ip_list(
    interaction: discord.Interaction,
):
    if interaction.guild_id is None:
        embed = create_error_embed(
            title="Command unavailable",
            description="This command can only be used inside a server.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    servers = storage.get_guild_servers(interaction.guild_id)

    if not servers:
        embed = create_info_embed(
            title="No saved servers",
            description="There are no archived Minecraft servers yet.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    await interaction.response.defer()

    embed = create_info_embed(
        title="Saved servers",
        description="Current status of archived Minecraft servers in this server.",
    )

    for name, info in servers.items():
        address = info["address"]
        result = await check_minecraft_server(address)

        storage.update_server_status(
            guild_id=interaction.guild_id,
            name=name,
            online=result["online"],
            latency=result["latency"],
            players=result["players"],
            version=result["version"],
            error=result["error"],
        )

        if result["online"]:
            value = (
                f"Address: `{address}`\n"
                f"Status: `Online`\n"
                f"Latency: `{result['latency']} ms`\n"
                f"Players: `{result['players']}`\n"
                f"Version: `{result['version']}`"
            )
        else:
            value = (
                f"Address: `{address}`\n"
                f"Status: `Offline`\n"
            )

            if result.get("error"):
                value += f"\nError: `{result['error']}`"

        embed.add_field(
            name=name,
            value=value,
            inline=False,
        )

    await interaction.followup.send(embed=embed)
    if interaction.guild_id is None:
        embed = create_error_embed(
            title="Command unavailable",
            description="This command can only be used inside a server.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    servers = storage.get_guild_servers(interaction.guild_id)

    if not servers:
        embed = create_info_embed(
            title="No saved servers",
            description="There are no archived Minecraft servers yet.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    embed = create_info_embed(
        title="Saved servers",
        description="List of archived Minecraft servers in this server.",
    )

    for name, info in servers.items():
        embed.add_field(
            name=name,
            value=format_server_status(info),
            inline=False,
        )

    await interaction.followup.send(embed=embed)


@ip_group.command(
    name="check",
    description="Check a saved server or test a custom Minecraft IP",
)
@app_commands.describe(
    name="Name of the saved server you want to check",
    address="IP or domain to check without saving it",
)
async def ip_check(
    interaction: discord.Interaction,
    name: str | None = None,
    address: str | None = None,
):
    if interaction.guild_id is None:
        embed = create_error_embed(
            title="Command unavailable",
            description="This command can only be used inside a server.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if name is None and address is None:
        embed = create_error_embed(
            title="Missing data",
            description="Use either `name` to check a saved server or `address` to check a custom IP.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if name is not None and address is not None:
        embed = create_error_embed(
            title="Too many options",
            description="Use only one option: either `name` or `address`, not both.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    await interaction.response.defer()

    if name is not None:
        name = name.lower().strip()

        server = storage.get_server(
            guild_id=interaction.guild_id,
            name=name,
        )

        if server is None:
            embed = create_error_embed(
                title="Server not found",
                description=f"No saved server was found with the name `{name}`.",
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        address = server["address"]
        result = await check_minecraft_server(address)

        storage.update_server_status(
            guild_id=interaction.guild_id,
            name=name,
            online=result["online"],
            latency=result["latency"],
            players=result["players"],
            version=result["version"],
            error=result["error"],
        )

        if result["online"]:
            embed = create_success_embed(
                title="Server online",
                description="The saved server is responding correctly.",
            )
        else:
            embed = create_error_embed(
                title="Server offline",
                description="The saved server is not responding or is not accessible.",
            )

        add_server_fields(embed, name, address, result)
        await interaction.followup.send(embed=embed)
        return

    address = address.strip()
    result = await check_minecraft_server(address)

    if result["online"]:
        embed = create_success_embed(
            title="Custom IP online",
            description="The provided server address is responding correctly.",
        )
    else:
        embed = create_error_embed(
            title="Custom IP offline",
            description="The provided server address is not responding or is not accessible.",
        )

    add_server_fields(
        embed=embed,
        name="Not saved",
        address=address,
        result=result,
    )

    await interaction.followup.send(embed=embed)



@config_group.command(
    name="channel",
    description="Set the channel for scheduled check messages",
)
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.describe(
    channel="Channel where scheduled check messages will be sent",
)
async def config_channel(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
):
    if interaction.guild_id is None:
        embed = create_error_embed(
            title="Command unavailable",
            description="This command can only be used inside a server.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    config.set_scheduled_check_channel(
        guild_id=interaction.guild_id,
        channel_id=channel.id,
    )

    embed = create_success_embed(
        title="Configuration updated",
        description="Scheduled check messages will now be sent to the selected channel.",
    )
    embed.add_field(name="Scheduled check channel", value=channel.mention, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@config_group.command(
    name="view",
    description="View the current bot configuration",
)
@app_commands.checks.has_permissions(manage_guild=True)
async def config_view(
    interaction: discord.Interaction,
):
    if interaction.guild_id is None:
        embed = create_error_embed(
            title="Command unavailable",
            description="This command can only be used inside a server.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    channel_id = config.get_scheduled_check_channel(interaction.guild_id)

    embed = create_info_embed(
        title="Current configuration",
        description="Bot settings for this server.",
    )

    if channel_id is None:
        embed.add_field(
            name="Scheduled check channel",
            value="Not configured. The bot will use each server's original channel.",
            inline=False,
        )
    else:
        channel = interaction.guild.get_channel(int(channel_id))

        if channel is None:
            value = f"Configured channel not found. ID: `{channel_id}`"
        else:
            value = channel.mention

        embed.add_field(
            name="Scheduled check channel",
            value=value,
            inline=False,
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)



@ip_add.error
@ip_remove.error
@ip_edit.error
@config_channel.error
@config_view.error
async def permission_error_handler(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
):
    if isinstance(error, app_commands.MissingPermissions):
        embed = create_error_embed(
            title="Missing permissions",
            description="You need the `Manage Server` permission to use this command.",
        )

        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    raise error

@bot.tree.command(
    name="help",
    description="Show the main bot commands and usage",
)
async def help_command(interaction: discord.Interaction):
    embed = create_info_embed(
        title="MTDRBot Help",
        description="Main commands available in this bot.",
    )

    embed.add_field(
        name="/ip add",
        value=(
            "Add a Minecraft server to the archive.\n"
            "Usage: `/ip add name:<server_name> address:<ip_or_domain>`\n"
            "Requires: `Manage Server`"
        ),
        inline=False,
    )

    embed.add_field(
        name="/ip remove",
        value=(
            "Remove a saved Minecraft server from the archive.\n"
            "Usage: `/ip remove name:<server_name>`\n"
            "Requires: `Manage Server`"
        ),
        inline=False,
    )

    embed.add_field(
        name="/ip edit",
        value=(
            "Edit the name or address of a saved server.\n"
            "Usage: `/ip edit name:<current_name> new_name:<new_name> new_address:<new_address>`\n"
            "Requires: `Manage Server`"
        ),
        inline=False,
    )

    embed.add_field(
        name="/ip list",
        value=(
            "Show all saved servers and check their current status.\n"
            "Usage: `/ip list`"
        ),
        inline=False,
    )

    embed.add_field(
        name="/ip check",
        value=(
            "Check a saved server or test a custom IP without saving it.\n"
            "Saved server: `/ip check name:<server_name>`\n"
            "Custom IP: `/ip check address:<ip_or_domain>`"
        ),
        inline=False,
    )

    embed.add_field(
        name="/config channel",
        value=(
            "Set the channel used for scheduled check messages if this feature is enabled later.\n"
            "Usage: `/config channel channel:<channel>`\n"
            "Requires: `Manage Server`"
        ),
        inline=False,
    )

    embed.add_field(
        name="/config view",
        value=(
            "View the current bot configuration for this server.\n"
            "Usage: `/config view`\n"
            "Requires: `Manage Server`"
        ),
        inline=False,
    )

    embed.set_footer(text="Minecraft Tech Discord Recollector")

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


if TOKEN is None:
    raise ValueError("TOKEN not found in the .env file")

bot.run(TOKEN)