
from httpx import HTTPStatusError
from discord.ext import commands
from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.authentication.models import OAuth2TokenResponse
from xbox.webapi.common.signed_session import SignedSession
from xbox.webapi.authentication.xal import XALManager, XalAppParameters, XalClientParameters
from xbox.webapi.api.provider.profile.models import ProfileUser, ProfileResponse
from xbox.webapi.authentication.xal import XALManager, XalAppParameters, XalClientParameters
from xbox.webapi.api.client import Session
from xbox.webapi.scripts import TOKENS_FILE
from aiohttp import ClientSession
from discord import app_commands
from discord.app_commands import Choice
from ms_cv import CorrelationVector
import string, discord, time
from concurrent.futures import ThreadPoolExecutor
characters = list(string.ascii_lowercase + '123456789')
from asyncio import create_task, gather, run, sleep
from pydantic.json import pydantic_encoder
from urllib import parse

import Utilities.party as party
import Utilities.personal as personal
import Utilities.admin as admin
import Utilities.authentication as integrated_authorization



"""

I planned on adding remote authentication so users wouldn't need to copy/paste their own authentication code.
However, I am moving on from this project. You may see slight refactorization in the future. (Maybe not)


You can assume all values are HARD-CODED and needing changed. You can contact me @b0nggo on discord if you have any questions

Heavy refactoring is needed for utility files, and modules. Most code is non-optimized and non-async. You are welcome to fork, or request a push


The Roles are supposed to signify tiers in the Discord server. This project is for learning purposes only, use responsibily.

"""






staff = {"Moderators", "Admins"}

basic = {"Moderators", "Admins"}

free = {"Moderators", "Admins"}

user_cooldowns = {}

def apply_cooldown(user, duration):
    roles = {role.name.lower() for role in user.roles}
    """Manually apply cooldown based on user ID and duration"""
    #user_cooldowns[user.id] = time.time() + duration  # Store the end time of the cooldown
    print(roles)
    if user.id in super_users or "super" in roles:
        return None
    elif "vip" in roles:
        user_cooldowns[user.id] = time.time() + duration + 100

def check_cooldown(user_id):
    """Check if the user is currently on cooldown"""
    if user_id in user_cooldowns:
        if time.time() < user_cooldowns[user_id]:
            return True
    return False

super_users = [] # Add your SU here.


def cooldown_invites(interaction: discord.Interaction, duration: int = None):
    roles = {role.name for role in interaction.user.roles}
    if interaction.user.id in super_users or "Super" in roles:
        return None
    
    elif "VIP" in roles:
        return app_commands.Cooldown(1, 100.0)
    else:
        if duration is not None:
            return app_commands.Cooldown(1, duration + 30.0) 
        else:
            return app_commands.Cooldown(1, 1200.0)

blacklisted = (2535453581119827 , )

whitelist = {"Moderators", "Admins"}


server_list = () # Tuple


CLIENT_PARAMS_ANDROID = XalClientParameters(
    user_agent="XAL Android 2020.07.20200714.000",
    device_type="Android",
    client_version="8.0.0",
    query_display="android_phone",
)
APP_PARAMS_XBOX_APP = XalAppParameters(
    app_id="000000004c12ae6f",
    title_id="328178078",
    redirect_uri="https://login.live.com/oauth20_desktop.srf",
)

client_id = ''
client_secret = ''
tokens_file = './accounts'

def create_error_handler(command_name):
    async def error_handler(interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            minutes = int(error.retry_after // 60)
            seconds = int(error.retry_after % 60)

            await interaction.response.send_message(
                f"{command_name} is on cooldown. Try again in {minutes} minutes and {seconds} seconds.\n"
                "Subscribe to reduce or eliminate cooldowns!"
            )
    return error_handler

class MyClient(discord.Client):
    rate_limit_counter = 0
    sent_counter = 0
    intents = discord.Intents.all()
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tree = app_commands.CommandTree(self)



    async def on_ready(self):
        await self.tree.sync()
        for i in self.guilds:
            if i.id not in server_list:
                print(f"Left {i.name}/{i.owner.name} {i.name}")
                await i.leave()
        print('Logged on as', self.user)
        await self.change_presence(activity=discord.CustomActivity(name="The ultimate ignorance is the rejection of something you know nothing about yet refuse to investigate", emoji='🧠'))

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        print(f"Error detected: {error}")
        if isinstance(error, app_commands.CommandOnCooldown):
            if interaction.response.is_done():
                await interaction.followup.send(
                    f"This command is on cooldown. Try again after {error.retry_after:.2f} seconds.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"This command is on cooldown. Try again after {error.retry_after:.2f} seconds.",
                    ephemeral=True
                )
        else:
            if interaction.response.is_done():
                await interaction.followup.send("An error occurred.", ephemeral=True)
            else:
                await interaction.response.send_message("An error occurred.", ephemeral=True)
            raise error


client = MyClient(intents=discord.Intents.all())
#client.on_error



@app_commands.choices(game=[
    Choice(name='Rainbow 6 Siege', value="4c5b0100-b87d-4442-9d9b-cb81373d69b4"),
    Choice(name='Grounded', value="00000000-0000-0000-0000-00007d7cfb3c"),
    Choice(name='Dayz', value="6fcb0100-847a-4a22-933c-1b902e51b7c2"),
    Choice(name="7 Days To Die", value='00000000-0000-0000-0000-0000672c8813')
])
@client.tree.command(name="createlfg",description="Create looking for group post")
@app_commands.checks.dynamic_cooldown(cooldown_invites)
async def createlfg(interaction:discord.Interaction, game:app_commands.Choice[str], description:str, players_needed:int=1):
    if players_needed > 15:
        players_needed = 15
    elif players_needed <= 0:
        players_needed = 1
    await interaction.response.defer()
    await personal.createlfg(interaction, game, description, players_needed, client)

createlfg.error(create_error_handler("Create Looking for Group"))

@client.tree.command(name="forceinvite",description="Force an invite from someone")
@app_commands.default_permissions(manage_messages=True)
@app_commands.checks.has_permissions(manage_messages=True)
async def forceinvite(interaction:discord.Interaction, target:str, recipient:str):
    if interaction.guild == None:
        print(interaction.user.name+' tried to execute command privately')
        await interaction.response.send_message("Please use this command in a discord server")
        return
    await interaction.response.defer()
    await admin.forceinvite(interaction, target, recipient, client)

# This was supposed to track if a user is appearing offline. Doesn't work as intended            @client.tree.command(name="watchstatus",description="...")
# This was supposed to track if a user is appearing offline. Doesn't work as intended            @app_commands.default_permissions(manage_messages=True)
# This was supposed to track if a user is appearing offline. Doesn't work as intended            @app_commands.checks.has_permissions(manage_messages=True)
# This was supposed to track if a user is appearing offline. Doesn't work as intended            async def forceinvite(interaction:discord.Interaction, target:str):
# This was supposed to track if a user is appearing offline. Doesn't work as intended                if interaction.guild == None:
# This was supposed to track if a user is appearing offline. Doesn't work as intended                    print(interaction.user.name+' tried to execute command privately')
# This was supposed to track if a user is appearing offline. Doesn't work as intended                    await interaction.response.send_message("Please use this command in a discord server")
# This was supposed to track if a user is appearing offline. Doesn't work as intended                    return
# This was supposed to track if a user is appearing offline. Doesn't work as intended                await party.stalkuser(interaction, target, client)

@client.tree.command(name="link",description="Link your Xbox account with the bot")
@app_commands.default_permissions(manage_messages=True)
async def link(interaction:discord.Interaction):
    await interaction.response.defer()
    if await integrated_authorization.check_xbox_token_exists(interaction, client, True):
        await interaction.followup.send("Successfully linked!")
    else:
        await interaction.followup.send("Something went wrong while authenticating. You may be banned, or you are trying to use child account (< 18 years old)"
                                        "\n If you think this is a mistake, please contact an administrator")

@client.tree.command(name="unlink",description="Unlink your Xbox account from the bot")
@app_commands.default_permissions(manage_messages=True)
async def unlink(interaction:discord.Interaction):
    await interaction.response.defer()
    await interaction.followup.send("This is not yet implemented. Contact an adminsistrator for removal!")

@app_commands.choices(joinable=[
    Choice(name='Joinable', value="True"),
    Choice(name='Invite Only', value="False")
])
@client.tree.command(name="joinstate",description="Makes your current party joinable, or unjoinable")
@app_commands.checks.dynamic_cooldown(cooldown_invites)
async def unlink(interaction:discord.Interaction, joinable:app_commands.Choice[str]):
    await interaction.response.defer()
    await party.joinable(interaction, client, (True if joinable.value=="True" else False))

unlink.error(create_error_handler("joinstate"))

@client.tree.command(name="crashparty",description="Crash Someone's Party!")
@app_commands.checks.dynamic_cooldown(cooldown_invites)
async def crash(interaction:discord.Interaction, target:str):
    await party.crash(interaction, target, client)

crash.error(create_error_handler("Party Crasher"))



@client.tree.command(name="viewparty",description="View Someone's Party!")
@app_commands.checks.dynamic_cooldown(cooldown_invites)
async def viewparty(interaction:discord.Interaction, target:str):
    await party.viewparty(interaction, target, client)

crash.error(create_error_handler("Party Crasher"))

@client.tree.command(name="crashloop", description="Crash Someone's Party Continuously")
async def crashloop(interaction: discord.Interaction, target: str, duration: int):
    if duration > 1800:
        duration = 1800
    elif duration < 0:
        await interaction.response.send_message("Cannot loop for 0 seconds!")
        return
    elif duration < 30:
        duration = 30


    if check_cooldown(interaction.user.id):
        cooldown_end_time = user_cooldowns[interaction.user.id]

        remaining_time = cooldown_end_time - time.time()

        if remaining_time > 0:
            minutes = int(remaining_time // 60)
            seconds = int(remaining_time % 60)
            await interaction.response.send_message(f"You are on cooldown. Please wait {minutes}m {seconds}s.")
            return

    apply_cooldown(interaction.user, duration)
    if await party.crashloop(interaction, target, duration, client) == False:
        user_cooldowns[interaction.user.id] = max(user_cooldowns[interaction.user.id] - duration, time.time())
    await interaction.response.send_message(f"Starting crashloop for {duration} seconds.")

# Error handler for crashloop command
crashloop.error(create_error_handler("Crash Loop"))

@client.tree.command(name="spaminvite",description="Spam invites the target. Max is 1000 invites")
@app_commands.checks.dynamic_cooldown(cooldown_invites)
async def spaminvite(interaction:discord.Interaction, target:str, amount: app_commands.Range[int, 1, 1800]):
    await interaction.response.defer()
    if amount > 1000:
        amount = 1000
    elif amount <= 0:
        await interaction.followup.send("You cannot send 0 invites...")
        return
    if interaction.guild == None:
        print(interaction.user.name+' tried to execute command privately on ' + target)
        await interaction.response.send_message("Please use this command in a discord server")
        return
    print("Executing command")
    await party.spaminvite(interaction, target, amount, client)

spaminvite.error(create_error_handler("Spam Invite"))


@client.tree.command(name="inviteallfriends",description="invites all of your friends to an xbox party (whitelist only)")
@app_commands.checks.dynamic_cooldown(cooldown_invites)
async def inviteallfriends(interaction:discord.Interaction):
    await party.inviteallfriends(interaction, client)

inviteallfriends.error(create_error_handler("inviteallfriends"))


@client.tree.command(name="sendmessage",description="Send a message to someone!")
@app_commands.checks.dynamic_cooldown(cooldown_invites)
async def send_message_command(interaction:discord.Interaction, target:str, text_message:str):
    if interaction.guild == None:
        print(interaction.user.name+' tried to execute command privately')
        await interaction.response.send_message("Please use this command in a discord server")
        return
    await interaction.response.defer()
    await personal.send_message_command(interaction, target, text_message, client)

send_message_command.error(create_error_handler("Send message"))

@client.tree.command(name="antikick",description="Makes you unkickable in the party")
@app_commands.checks.dynamic_cooldown(cooldown_invites)
async def antikick(interaction:discord.Interaction):
    await party.antikick(interaction, client)

antikick.error(create_error_handler("Anti Kick"))
    
@app_commands.choices(state=[
    Choice(name='Connecting', value=1),
    Choice(name='Normal', value=2),
    Choice(name='Disconnected', value=3),
    Choice(name='Game Chat', value=4),
])
@client.tree.command(name="fakestate",description="Fake a party status")
@app_commands.checks.dynamic_cooldown(cooldown_invites)
async def fakestate(interaction:discord.Interaction, state:app_commands.Choice[int]):
    await interaction.response.defer()
    await party.fakestate(interaction, state, client)

fakestate.error(create_error_handler("Fake State"))




client.run('') # Place discord token.
