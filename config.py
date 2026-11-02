import json
import os

CONFIG_FILE = "config.json"


def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return {}

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return {}


def save_config(data: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def get_guild_config(guild_id: int) -> dict:
    data = load_config()
    return data.get(str(guild_id), {})


def set_scheduled_check_channel(guild_id: int, channel_id: int) -> None:
    data = load_config()
    guild_id = str(guild_id)

    if guild_id not in data:
        data[guild_id] = {}

    data[guild_id]["scheduled_check_channel_id"] = channel_id

    save_config(data)


def get_scheduled_check_channel(guild_id: int):
    guild_config = get_guild_config(guild_id)
    return guild_config.get("scheduled_check_channel_id")


def set_honeypot_channel(guild_id: int, channel_id: int | None) -> None:
    data = load_config()
    guild_id = str(guild_id)

    if guild_id not in data:
        data[guild_id] = {}

    if channel_id is None:
        data[guild_id].pop("honeypot_channel_id", None)
    else:
        data[guild_id]["honeypot_channel_id"] = channel_id

    save_config(data)


def get_honeypot_channel(guild_id: int):
    guild_config = get_guild_config(guild_id)
    return guild_config.get("honeypot_channel_id")


def set_honeypot_logs_channel(guild_id: int, channel_id: int | None) -> None:
    data = load_config()
    guild_id = str(guild_id)

    if guild_id not in data:
        data[guild_id] = {}

    if channel_id is None:
        data[guild_id].pop("honeypot_logs_channel_id", None)
    else:
        data[guild_id]["honeypot_logs_channel_id"] = channel_id

    save_config(data)


def get_honeypot_logs_channel(guild_id: int):
    guild_config = get_guild_config(guild_id)
    return guild_config.get("honeypot_logs_channel_id")