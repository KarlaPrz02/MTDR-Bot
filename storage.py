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
    return True