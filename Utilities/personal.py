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
import discord, requests
from config import Config
from discord import app_commands
characters = list(string.ascii_lowercase + '123456789')



async def send_message_command(interaction:discord.Interaction, target:str, text_message:str, client=None):
    if interaction.guild == None:
        print(interaction.user.name+' tried to execute command privately')
        await interaction.response.send_message("Please use this command in a discord server")
        return
    sisu_tokens = await check_xbox_token_exists(interaction, client, True)
    session = SignedSession()
    auth_mgr = AuthenticationManager(session, Config.client_id, Config.client_secret, "")
    with open(('./accounts'+f'/{interaction.user.id}.json')) as f:
            tokens = f.read()
            auth_mgr.oauth = OAuth2TokenResponse.model_validate_json(tokens)
    await auth_mgr.refresh_tokens()
    xbl_client = XboxLiveClient(auth_mgr)
    try:
        target = await xbl_client.profile.get_profile_by_gamertag(target)
    except HTTPStatusError:
        await interaction.followup.send("Could not find a user by that gamertag!")
        return
    target = target.model_dump()['profile_users']
    auth_token = 'XBL3.0 x=' + sisu_tokens.user_token.display_claims.xui[0]['uhs'] + ';' + sisu_tokens.authorization_token.token
    #await xbl_client.message.send_message(target[0]['id'], text_message)
    url = f'https://xblmessaging.xboxlive.com/network/xbox/users/xuid({sisu_tokens.authorization_token.xuid})/conversations/users/xuid({target[0]['id']})'
    payload = {"parts":[{"contentType":"text","text":text_message,"version":0}]}
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
    put_response = requests.post(url, headers=headers_put, json=payload)
    if put_response.status_code == 200:
        await interaction.followup.send(f"Successfully sent message")
    else:
        print("Failed to send message:", put_response.status_code, put_response.text)
        await interaction.followup.send("Operation failed, try again!")


async def createlfg(interaction:discord.Interaction, game:app_commands.Choice[str], description:str, players_needed:int=1, client=None):
    sisu_tokens = await check_xbox_token_exists(interaction, client, True)
    print(sisu_tokens)
    auth_token = 'XBL3.0 x=' + sisu_tokens.user_token.display_claims.xui[0]['uhs'] + ';' + sisu_tokens.authorization_token.token
    def sessiongenerator():
        session = f'{"".join(random.choices(characters, k=8))}-{"".join(random.choices(characters, k=4))}-{"".join(random.choices(characters, k=4))}-{"".join(random.choices(characters, k=4))}-{"".join(random.choices(characters, k=12))}'
        return session
    session2 = sessiongenerator()
    response = requests.put(f'https://sessiondirectory.xboxlive.com/serviceconfigs/{game.value}/sessiontemplates/global(lfg)/sessions/{session2}', headers={
                     'x-xbl-contract-version': '107',
                     'Accept-Encoding': 'gzip, deflate',
                     'Accept': 'application/json',
                     'User-Agent': 'XboxGameBazyWidgets/2404.1001.25.0',
                     'Accept-Language': 'en-US',
                     'Authorization': auth_token,
                     'Content-Length': '873',
                     'Content-Type': 'application/json; charset=UTF-8',
                     'Host': 'sessiondirectory.xboxlive.com',
                     'Connection': 'Keep-Alive',
                     'Cache-Control': 'no-cache',
                 }, json=
                 {"members":{"me":{"properties":{"system":{"active":True,"connection":str(uuid.uuid4()),"subscription":{"id":str(uuid.uuid4()),"changeTypes":["membersList","membersStatus","joinability","customProperty","membersCustomProperty","roles","scheduledtime"]},"secondarySubscriptions":{str(uuid.uuid4()):{"changeTypes":["membersList","membersStatus","joinability","customProperty","membersCustomProperty","roles","scheduledtime"],"rta":{"connection":str(uuid.uuid4())}}}}},"constants":{"system":{"xuid":sisu_tokens.authorization_token.xuid,"initialize":True}}}},"properties":{"system":{"joinRestriction":"followed","readRestriction":"followed","searchHandleVisibility":"xboxlive","description":{"text":description,"locale":"en"}}},"roleTypes":{"lfg":{"ownerManaged":True,"roles":{"confirmed":{"target":players_needed,"max":15}}}}
                 })
    print(response.content)
    print(response.status_code)
    finalize_request = requests.post('https://sessiondirectory.xboxlive.com/handles',
                     headers={
                     'x-xbl-contract-version': '107',
                     'Accept': 'application/json',
                     'Accept-Language': 'en-US',
                     'Authorization': auth_token},
                     json={"searchAttributes":{"tags":[],"achievementIds":[],"locale":"en"},"sessionRef":{"scid":game.value,"templateName":"global(lfg)","name":session2},"type":"search","version":1})
    if response.status_code == 201 and finalize_request.status_code == 201:
        await interaction.followup.send("Successfully create LFG post")
    elif response.status_code != 201:
        await interaction.followup.send("Something went wrong when generating the post")
    elif finalize_request.status_code != 201:
        print(finalize_request.content)
        print(finalize_request.status_code)
        await interaction.followup.send("Something went wrong when handling the post")
