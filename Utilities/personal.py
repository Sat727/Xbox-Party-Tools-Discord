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
from .tools import *
from discord import app_commands
import sqlite3, difflib
conn = sqlite3.connect("games.db")
cursor = conn.cursor()
characters = list(string.ascii_lowercase + '123456789')
cursor.execute("""
CREATE TABLE IF NOT EXISTS games (
    name TEXT UNIQUE,
    service_config_id TEXT
)
""")
def normalize(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)  # Remove punctuation
    return set(text.split())

def jaccard_similarity(set1, set2):
    intersection = set1 & set2
    union = set1 | set2
    return len(intersection) / len(union) if union else 0

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


async def createlfg(interaction:discord.Interaction, game:str, description:str, players_needed:int=1, client=None):
    sisu_tokens = await check_xbox_token_exists(interaction, client, True)
    print(sisu_tokens)
    auth_token = 'XBL3.0 x=' + sisu_tokens.user_token.display_claims.xui[0]['uhs'] + ';' + sisu_tokens.authorization_token.token
    def sessiongenerator():
        session = f'{"".join(random.choices(characters, k=8))}-{"".join(random.choices(characters, k=4))}-{"".join(random.choices(characters, k=4))}-{"".join(random.choices(characters, k=4))}-{"".join(random.choices(characters, k=12))}'
        return session
    print("Doing lookup")
    print(sisu_tokens.authorization_token.display_claims.xui[0]['xid'])
    game_data = requests.get(f'https://titlehub.xboxlive.com/users/xuid({sisu_tokens.authorization_token.display_claims.xui[0]['xid']})/titles/titleHistory/decoration/Scid', headers={
                      "x-xbl-contract-version": "2",
                      "Accept-Encoding": "gzip, deflate",
                      "Signature": generate_signature(auth_token, request_body=json.dumps({})),
                      "accept": "application/json",
                      "ms-cv": generate_ms_cv(),
                      "x-xbl-market": "US",
                      "accept-language": "en-US",
                     'Authorization': auth_token,
                 })
    print("Finished?")
    print(game_data.content)
    def jaccard_similarity(set1, set2):
        intersection = set1 & set2
        union = set1 | set2
        return len(intersection) / len(union) if union else 0
    if game_data.status_code == 200:
        print("Success")
        print("Successfully retrieved game data for scraping.")
        parsed_data = json.loads(game_data.content)
        games = parsed_data.get("titles", [])
        for game_raw in games:
            name = game_raw.get("name")
            service_config_id = game_raw.get("serviceConfigId")
            devices = game_raw.get("devices", [])
            if len(devices) == 1 and devices[0].lower() == "pc":
                continue
            if name and service_config_id:
                try:
                    cursor.execute("INSERT OR IGNORE INTO games (name, service_config_id) VALUES (?, ?)", (name, service_config_id))
                except sqlite3.IntegrityError:
                    print("Error")
                    pass 
    conn.commit()
    cursor.execute("SELECT name, service_config_id FROM games")
    all_games = cursor.fetchall()
    game = game.lower()
    game = re.sub(r"[^\w\s]", "", game)
    query_tokens = set(game.split())
    cutoff = 0.4
    scores = []
    for name, service_id in all_games:
        title_tokens = normalize(name)
        score = jaccard_similarity(query_tokens, title_tokens)
        if score >= cutoff:
            scores.append((score, name, service_id))
    if scores:
        scores.sort(reverse=True)
        best_match = max(scores, key=lambda x: x[0])
        best_name = best_match[1]
        service_id = best_match[2]
    else:
        await interaction.followup.send(f"No games with the name '{game}' found in database. Try spelling the game better, or the game is PC only.")
        return
    session2 = sessiongenerator()
    response = requests.put(f'https://sessiondirectory.xboxlive.com/serviceconfigs/{service_id}/sessiontemplates/global(lfg)/sessions/{session2}', headers={
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
                     json={"searchAttributes":{"tags":[],"achievementIds":[],"locale":"en"},"sessionRef":{"scid":service_id,"templateName":"global(lfg)","name":session2},"type":"search","version":1})
    if response.status_code == 201 and finalize_request.status_code == 201:
        await interaction.followup.send(f"Successfully create LFG post for {best_name}")
    elif response.status_code != 201:
        await interaction.followup.send("Something went wrong when generating the post")
    elif finalize_request.status_code != 201:
        print(finalize_request.content)
        print(finalize_request.status_code)
        await interaction.followup.send("Something went wrong when handling the post")
