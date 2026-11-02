<<<<<<< HEAD
import json
import os
from datetime import datetime, timezone

DATA_FILE = "ips.json"

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def get_guild_servers(guild_id: int):
    data = load_data()
    return data.get(str(guild_id), {})

def get_server(guild_id: int, name: str):
    data = load_data()
    guild_id = str(guild_id)

    if guild_id not in data:
        return None

    return data[guild_id].get(name)

def get_all_servers() -> dict:
    return load_data()


def add_server(guild_id: int, channel_id: int, name: str, address: str, added_by: int):
    data = load_data()
    guild_id = str(guild_id)

    if guild_id not in data:
        data[guild_id] = {}

    if name in data[guild_id]:
        return False

    data[guild_id][name] = {
        "address": address,
        "channel_id": channel_id,
        "added_by": added_by,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_checked": None,
        "last_online": None,
        "last_latency": None,
        "last_players": None,
        "last_version": None,
        "last_error": None
    }

    save_data(data)
    return True


def remove_server(guild_id: int, name: str):
    data = load_data()
    guild_id = str(guild_id)

    if guild_id not in data or name not in data[guild_id]:
        return None

    removed = data[guild_id].pop(name)
    save_data(data)
    return removed


def edit_server(guild_id: int, name: str, new_name: str | None = None, new_address: str | None = None):
    data = load_data()
    guild_id = str(guild_id)

    if guild_id not in data or name not in data[guild_id]:
        return None

    final_name = new_name if new_name else name

    if final_name != name and final_name in data[guild_id]:
        return "NAME_EXISTS"

    server_data = data[guild_id][name]

    if new_address:
        server_data["address"] = new_address

    if final_name != name:
        data[guild_id][final_name] = server_data
        del data[guild_id][name]

    save_data(data)
    return data[guild_id][final_name]


def update_server_status(
    guild_id: int,
    name: str,
    online: bool,
    latency=None,
    players=None,
    version=None,
    error=None,
) -> bool:
    data = load_data()
    guild_id = str(guild_id)

    if guild_id not in data:
        return False

    if name not in data[guild_id]:
        return False

    data[guild_id][name]["last_checked"] = utc_now()
    data[guild_id][name]["last_online"] = online
    data[guild_id][name]["last_latency"] = latency
    data[guild_id][name]["last_players"] = players
    data[guild_id][name]["last_version"] = version
    data[guild_id][name]["last_error"] = error

    save_data(data)
=======
import requests

API_URL = "http://127.0.0.1:8000"


def get_guild_servers(guild_id: int):
    response = requests.get(
        f"{API_URL}/minecraft/servers/{guild_id}",
        timeout=10,
    )

    if response.status_code == 404:
        return {}

    response.raise_for_status()
    return response.json()


def get_server(guild_id: int, name: str):
    response = requests.get(
        f"{API_URL}/minecraft/servers/{guild_id}/{name}",
        timeout=10,
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()
    return response.json()


def get_all_servers() -> dict:
    response = requests.get(
        f"{API_URL}/minecraft/servers",
        timeout=10,
    )

    if response.status_code == 404:
        return {}

    response.raise_for_status()
    return response.json()


def add_server(
    guild_id: int,
    channel_id: int,
    name: str,
    address: str,
    added_by: int,
):
    payload = {
        "guild_id": str(guild_id),
        "channel_id": str(channel_id),
        "name": name,
        "address": address,
        "added_by": str(added_by),
    }

    response = requests.post(
        f"{API_URL}/minecraft/servers",
        json=payload,
        timeout=10,
    )

    if response.status_code == 409:
        return False

    response.raise_for_status()
    return True


def remove_server(guild_id: int, name: str):
    response = requests.delete(
        f"{API_URL}/minecraft/servers/{guild_id}/{name}",
        timeout=10,
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()
    return response.json()


def edit_server(
    guild_id: int,
    name: str,
    new_name: str | None = None,
    new_address: str | None = None,
):
    payload = {
        "new_name": new_name,
        "new_address": new_address,
    }

    response = requests.put(
        f"{API_URL}/minecraft/servers/{guild_id}/{name}",
        json=payload,
        timeout=10,
    )

    if response.status_code == 404:
        return None

    if response.status_code == 409:
        return "NAME_EXISTS"

    response.raise_for_status()
    return response.json()


def update_server_status(
    guild_id: int,
    name: str,
    online: bool,
    latency=None,
    players=None,
    version=None,
    error=None,
) -> bool:
    payload = {
        "online": online,
        "latency": latency,
        "players": players,
        "version": version,
        "error": error,
    }

    response = requests.patch(
        f"{API_URL}/minecraft/servers/{guild_id}/{name}/status",
        json=payload,
        timeout=10,
    )

    if response.status_code == 404:
        return False

    response.raise_for_status()
>>>>>>> bcff39e50b31f9d72de0811fafd3e1e472a18e10
    return True