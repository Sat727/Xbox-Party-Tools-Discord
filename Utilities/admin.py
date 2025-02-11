from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.authentication.models import OAuth2TokenResponse
from xbox.webapi.common.signed_session import SignedSession
from xbox.webapi.authentication.xal import XALManager, XalAppParameters, XalClientParameters
from xbox.webapi.api.provider.profile.models import ProfileUser, ProfileResponse
from xbox.webapi.authentication.xal import XALManager, XalAppParameters, XalClientParameters
from xbox.webapi.api.client import Session
from .authentication import *
import aiohttp, asyncio, random, string
from discord import Interaction
import discord, requests, os
from config import Config
from discord import app_commands
characters = list(string.ascii_lowercase + '123456789')


async def forceinvite(interaction:discord.Interaction, target:int, recipient:str, client):
    auth_mgr = await check_xbox_token_exists(interaction, client, False)
    session = SignedSession()
    auth_mgr = AuthenticationManager(session, Config.client_id, Config.client_secret, "")
    with open(('./accounts'+f'/{target}.json')) as f:
            tokens = f.read()
            auth_mgr.oauth = OAuth2TokenResponse.model_validate_json(tokens)
    xbl_client = XboxLiveClient(auth_mgr)
    await auth_mgr.refresh_tokens()
    print("Did authentication")
    auth_token = 'XBL3.0 x=' + auth_mgr.user_token.display_claims.xui[0]['uhs'] + ';' + auth_mgr.xsts_token.token # make a device token id
    try:
        target = await xbl_client.profile.get_profile_by_gamertag(recipient)
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
        await interaction.followup.send("You are not detected in a party.")
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
    successful_invites, rate_limits = await execute_requests(url, 1, json_request, headers_get)
    await interaction.followup.send(f"Completed:\n\nSuccessful invites: {successful_invites}\n\nUnsuccessful invites: {rate_limits}")

async def addresses(session, url, json_request, headers_get, handle=False):
                try:
                    if handle ==False:
                        async with session.put(url, json=json_request, headers=headers_get, timeout=5) as response:
                            return response.status
                    else:
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




async def advertise(interaction: discord.Interaction, description: str, client=None):
    f = []
    games = ["4c5b0100-b87d-4442-9d9b-cb81373d69b4", "6fcb0100-847a-4a22-933c-1b902e51b7c2"]
    
    for (dirpath, dirnames, filenames) in os.walk('./accounts'):
        f.extend([i[:19].replace('_', '') for i in filenames if 'sisu' in i])
        break

    successful_invites = 0
    rate_limits = 0

    async with aiohttp.ClientSession() as session:
        def sessiongenerator():
            return f'{"".join(random.choices(characters, k=8))}-{"".join(random.choices(characters, k=4))}-{"".join(random.choices(characters, k=4))}-{"".join(random.choices(characters, k=4))}-{"".join(random.choices(characters, k=12))}'

        for i in f:
            game = random.choice(games)
            sisu_tokens = await check_xbox_token_exists_admin(i, client, True)

            if not sisu_tokens:
                print("Skipping due to missing tokens.")
                continue

            auth_token = 'XBL3.0 x=' + sisu_tokens.user_token.display_claims.xui[0]['uhs'] + ';' + sisu_tokens.authorization_token.token
            session2 = sessiongenerator()


            url1 = f'https://sessiondirectory.xboxlive.com/serviceconfigs/{game}/sessiontemplates/global(lfg)/sessions/{session2}'
            json_request1 = {
                "members": {
                    "me": {
                        "properties": {
                            "system": {
                                "active": True,
                                "connection": str(uuid.uuid4()),
                                "subscription": {
                                    "id": str(uuid.uuid4()),
                                    "changeTypes": [
                                        "membersList", "membersStatus", "joinability",
                                        "customProperty", "membersCustomProperty",
                                        "roles", "scheduledtime"
                                    ]
                                },
                                "secondarySubscriptions": {
                                    str(uuid.uuid4()): {
                                        "changeTypes": [
                                            "membersList", "membersStatus", "joinability",
                                            "customProperty", "membersCustomProperty",
                                            "roles", "scheduledtime"
                                        ],
                                        "rta": {
                                            "connection": str(uuid.uuid4())
                                        }
                                    }
                                }
                            }
                        },
                        "constants": {
                            "system": {
                                "xuid": sisu_tokens.authorization_token.xuid,
                                "initialize": True
                            }
                        }
                    }
                },
                "properties": {
                    "system": {
                        "joinRestriction": "followed",
                        "readRestriction": "followed",
                        "searchHandleVisibility": "xboxlive",
                        "description": {"text": description, "locale": "en"}
                    }
                },
                "roleTypes": {
                    "lfg": {
                        "ownerManaged": True,
                        "roles": {
                            "confirmed": {"target": 3, "max": 15}
                        }
                    }
                }
            }
            headers1 = {
                'x-xbl-contract-version': '107',
                'Authorization': auth_token,
                'Content-Type': 'application/json'
            }

            try:
                async with session.put(url1, json=json_request1, headers=headers1, timeout=5) as response:
                    if response.status == 201:
                        successful_invites += 1
                    elif response.status == 429:
                        rate_limits += 1
            except asyncio.TimeoutError:
                print(f"Request timed out for URL: {url1}")

            url2 = f'https://sessiondirectory.xboxlive.com/handles'
            json_request2 = {
                "searchAttributes": {"tags": [], "achievementIds": [], "locale": "en"},
                "sessionRef": {"scid": game, "templateName": "global(lfg)", "name": session2},
                "type": "search",
                "version": 1
            }
            headers2 = {
                'x-xbl-contract-version': '107',
                'Authorization': auth_token
            }

            try:
                async with session.post(url2, json=json_request2, headers=headers2, timeout=5) as response:
                    if response.status == 201:
                        successful_invites += 1
                    else:
                        rate_limits += 1
            except asyncio.TimeoutError:
                print(f"Request timed out for URL: {url2}")

    await interaction.followup.send(
        f"Completed:\n\nSuccessful invites: {successful_invites}\n\nUnsuccessful invites (rate limited): {rate_limits}"
    )



    await interaction.followup.send(f"Completed:\n\nSuccessful invites: {successful_invites}\n\nUnsuccessful invites: {rate_limits}")
