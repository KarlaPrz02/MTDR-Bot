<<<<<<< HEAD
from mcstatus import JavaServer


async def check_minecraft_server(address: str) -> dict:
    """
    Checks whether a Minecraft Java server is online.

    address can be:
    - play.example.net
    - play.example.net:25565
    - 123.123.123.123
    - 123.123.123.123:25565
    """

    try:
        server = await JavaServer.async_lookup(address)
        status = await server.async_status()

        return {
            "online": True,
            "latency": round(status.latency, 2),
            "players": f"{status.players.online}/{status.players.max}",
            "version": status.version.name,
            "error": None,
        }

    except Exception as error:
        return {
            "online": False,
            "latency": None,
            "players": None,
            "version": None,
            "error": str(error),
=======
from mcstatus import JavaServer


async def check_minecraft_server(address: str) -> dict:
    """
    Checks whether a Minecraft Java server is online.

    address can be:
    - play.example.net
    - play.example.net:25565
    - 123.123.123.123
    - 123.123.123.123:25565
    """

    try:
        server = await JavaServer.async_lookup(address)
        status = await server.async_status()

        return {
            "online": True,
            "latency": round(status.latency, 2),
            "players": f"{status.players.online}/{status.players.max}",
            "version": status.version.name,
            "error": None,
        }

    except Exception as error:
        return {
            "online": False,
            "latency": None,
            "players": None,
            "version": None,
            "error": str(error),
>>>>>>> bcff39e50b31f9d72de0811fafd3e1e472a18e10
        }