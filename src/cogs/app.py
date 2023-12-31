import discord
from discord.ext import commands, tasks
import os
from aiohttp import web
from resources.database import get_roblox_info_by_rbxid
from resources import webhook_manager
import datetime
import dotenv

dotenv.load_dotenv()

# app = Flask(__name__)
app = web.Application()
routes = web.RouteTableDef()
api_key = os.getenv("ROBLOX_API_KEY")


class App(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.web_server.start()
        app.bot: commands.Bot = bot

        app.add_routes(routes)

    @routes.get("/")
    async def index(request: web.Request):
        resp = {'success': True, 'message': "Server is live"}
        return web.json_response(resp)

    @routes.get("/roblox/is-blacklisted")
    async def is_blacklisted(request: web.Request):
        roblox_id = request.rel_url.query.get("roblox_id", None)
        if not roblox_id:
            return web.json_response({'blacklisted': True, 'message': 'Improper request made'}, status=404)

        roblox_data = await get_roblox_info_by_rbxid(roblox_id)

        if not roblox_data:
            message = "User is not verified with Sally"
            resp = {'discord_id': None,
                    'blacklisted': True, 'message': message}

        elif roblox_data["blacklisted"]:
            message = roblox_data["message"]
            resp = {'discord_id': roblox_data["user_id"],
                    'blacklisted': True, 'message': message}

        else:
            resp = {'discord_id': roblox_data["user_id"],
                    'blacklisted': False, 'message': "User is not blacklisted"}

        return web.json_response(resp)

    @routes.get("/roblox/is-booster")
    async def is_booster(request: web.Request):
        roblox_id = request.rel_url.query.get("roblox_id", None)
        if not roblox_id:
            return web.json_response({'booster': False, 'message': 'Improper request made'}, status=404)

        roblox_data = await get_roblox_info_by_rbxid(roblox_id)
        if roblox_data == None:
            resp = {"booster": False}

        else:
            inkigayo: discord.Guild = app.bot.get_guild(1170821546038800464)
            server_booster = inkigayo.get_role(1177467255802564698)
            member = inkigayo.get_member(int(roblox_data["user_id"]))

            if not inkigayo or not member:
                resp = {"booster": False}

            elif server_booster in member.roles:
                resp = {"booster": True}

            else:
                resp = {"booster": False}

        return web.json_response(resp)

    @routes.get("/roblox/get-info")
    async def get_info(request: web.Request):
        roblox_id = request.rel_url.query.get("roblox_id", None)
        if not roblox_id:
            return web.json_response({'success': False, 'message': 'Improper request made'}, status=404)
        roblox_data = await get_roblox_info_by_rbxid(roblox_id)
        roblox_data["_id"] = "."
        return web.json_response(roblox_data)

    @routes.post("/roblox/join")
    async def roblox_join(request: web.Request):
        roblox_id = await request.json()
        roblox_id = roblox_id["roblox_id"]

        roblox_data = await get_roblox_info_by_rbxid(roblox_id)
        embed = discord.Embed(
            color=discord.Color.nitro_pink(), title="<:user:988229844301131776> User Join Triggered", timestamp=datetime.datetime.now())

        if roblox_data:
            embed.add_field(name="Discord Account",
                            value=f"<@{roblox_data['user_id']}> ({roblox_data['user_id']})")
            embed.add_field(name="Roblox Account",
                            value=f"{roblox_data['data']['name']} ({roblox_data['data']['id']})")
            embed.set_thumbnail(url=roblox_data["data"]["avatar"])

        else:
            embed.add_field(name="Discord Account",
                            value=f"Unknown")
            embed.add_field(name="Roblox Account",
                            value=str(roblox_id))

        await webhook_manager.send_join_log(embed)
        return web.json_response({"success": True})

    @routes.get("/roblox/test-join")
    async def roblox_join(request: web.Request):
        roblox_id = request.rel_url.query.get("roblox_id")

        roblox_data = await get_roblox_info_by_rbxid(roblox_id)
        embed = discord.Embed(
            color=discord.Color.nitro_pink(), title="<:user:988229844301131776> User Join Triggered", timestamp=datetime.datetime.now())
        embed.add_field(name="Discord Account",
                        value=f"<@{roblox_data['user_id']}> ({roblox_data['user_id']})")
        embed.add_field(name="Roblox Account",
                        value=f"{roblox_data['data']['name']} ({roblox_data['data']['id']})")
        embed.set_thumbnail(url=roblox_data["data"]["avatar"])

        logs = app.bot.get_channel(1183581233821790279)  # 1183581233821790279
        await logs.send(embed=embed)
        return web.json_response({"success": True})

    @tasks.loop()
    async def web_server(self):
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(
            runner, port=int(os.getenv("PORT")))
        await site.start()
        print("Started")

    @web_server.before_loop
    async def web_server_before_loop(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(App(bot))
