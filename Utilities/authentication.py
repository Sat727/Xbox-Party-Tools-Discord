from .tools import *
from .phrases import *
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.authentication.xal import XALManager, XalAppParameters, XalClientParameters
from xbox.webapi.authentication.models import OAuth2TokenResponse
from config import Config
from xbox.webapi.common.signed_session import SignedSession
import re
from httpx import HTTPStatusError
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

async def check_xbox_token_exists(interaction, client, do_sisu:bool=False):
    async with SignedSession() as session:
        tokens_file = ('./accounts'+f'/{interaction.user.id}.json')
        auth_mgr = AuthenticationManager(session, Config.client_id, Config.client_secret, "")
        try:
            with open(tokens_file) as f:
                tokens = f.read()
            print("Validating Token")
            auth_mgr.oauth = OAuth2TokenResponse.model_validate_json(tokens)
            print("Refreshing token")
            await auth_mgr.refresh_tokens()
            print(do_sisu)
            if do_sisu == True:
                print("Doing SISU")
                xalmanager = XALManager(session, uuid.uuid4(), APP_PARAMS_XBOX_APP, CLIENT_PARAMS_ANDROID)
                with open(('./accounts'+f'/{interaction.user.id}_sisu.json')) as f:
                    code_verifier = xalmanager._generate_code_verifier()
                    code_challenge = xalmanager._get_code_challenge_from_code_verifier(code_verifier)
                    device_token = await xalmanager.request_device_token()
                    state = xalmanager._generate_random_state()
                    test = await xalmanager.request_sisu_authentication(device_token.token, code_challenge, state)
                    print(f"User previously authenticated with SISU")
                    data = json.loads(f.read())
                    print(data)
                    sisu_tokens = await xalmanager.refresh_token(data['refresh_token'])
                    print("Refreshed SISU")
                    sisu_tokens = await xalmanager.do_sisu_authorization(test[1], json.loads(sisu_tokens.content)['access_token'], device_token.token, data['refresh_token'])
                print("Token found (SISU)")
                return sisu_tokens
            else:
                print("Token found (NOT SISU)")
                return auth_mgr
        except FileNotFoundError as e:
            print(
                f"File {tokens_file} isn`t found or it doesn`t contain tokens! err={e}"
            )
            print("Token not found in check token exists returning get_xbox_auth")
            return await get_xbox_auth(interaction, client, do_sisu)
        except Exception as e:
            return None
        
async def check_xbox_token_exists_admin(identifier, client, do_sisu:bool=False):
    async with SignedSession() as session:
        tokens_file = ('./accounts'+f'/{identifier}.json')
        auth_mgr = AuthenticationManager(session, Config.client_id, Config.client_secret, "")
        try:
            with open(tokens_file) as f:
                tokens = f.read()
            auth_mgr.oauth = OAuth2TokenResponse.model_validate_json(tokens)
            await auth_mgr.refresh_tokens()
            if do_sisu:
                xalmanager = XALManager(session, uuid.uuid4(), APP_PARAMS_XBOX_APP, CLIENT_PARAMS_ANDROID)
                with open(('./accounts'+f'/{identifier}_sisu.json')) as f:
                    code_verifier = xalmanager._generate_code_verifier()
                    code_challenge = xalmanager._get_code_challenge_from_code_verifier(code_verifier)
                    device_token = await xalmanager.request_device_token()
                    state = xalmanager._generate_random_state()
                    test = await xalmanager.request_sisu_authentication(device_token.token, code_challenge, state)
                    print(f"User previously authenticated with SISU")
                    data = json.loads(f.read())
                    print(data)
                    sisu_tokens = await xalmanager.refresh_token(data['refresh_token'])
                    print("Refreshed SISU")
                    sisu_tokens = await xalmanager.do_sisu_authorization(test[1], json.loads(sisu_tokens.content)['access_token'], device_token.token, data['refresh_token'])
                print("Token found")
                return sisu_tokens
            print("Token found")
            return auth_mgr
        except FileNotFoundError as e:
            return False
        except HTTPStatusError:
            print("HTTP ERROR")
            return False
        

async def get_xbox_auth(interaction, client, do_sisu:bool=False):
    async with SignedSession() as session:
        tokens_file = ('./accounts'+f'/{interaction.user.id}.json')
        """
        Initialize with global OAUTH parameters from above
        """
        auth_mgr = AuthenticationManager(session, Config.client_id, Config.client_secret, "")
        """
        Read in tokens that you received from the `xbox-authenticate`-script previously
        See `xbox/webapi/scripts/authenticate.py`
        """
        try:
            with open(tokens_file) as f:
                tokens = f.read()
            if do_sisu != True:
                auth_mgr.oauth = OAuth2TokenResponse.model_validate_json(tokens)
        except FileNotFoundError as e:
            print(
                f"File {tokens_file} isn`t found or it doesn`t contain tokens! err={e}"
            )
            print("Authorizing via OAUTH")
            url = auth_mgr.generate_authorization_url()
            print(f"Auth via URL: {url}")
            if interaction.guild:
                await interaction.channel.send(LinkPhrases.Notify_User)
            antique_message = await interaction.user.send(LinkPhrases.Instructions.format(url))
            def check(m):
                return m.author.id == interaction.user.id
            msg = await client.wait_for("message", check = check)
            if msg.guild:
                await msg.delete()
                await msg.channel.send(f"{msg.author.mention} I have deleted your response token as it was detected to be posted in a public channel. Please avoid posting this in a public channel in the future!")
            regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
            url = re.findall(regex, msg.content)
            if len(url) == 0:
                await interaction.followup.send(LinkError.InvalidLink)
            print(url[0])
            match = re.search(r'code=([A-Za-z0-9._-]+)', url[0][0])
            if match:
                code = match.group(1)
                print(code)
            else:
                await interaction.followup.send(LinkError.ParsingError)
                await interaction.user.send(LinkError.ParsingError)
                return
            try:
                tokens = await auth_mgr.request_oauth_token(code)
            except HTTPStatusError:
                await interaction.followup.send(LinkError.AuthenticationError)
                await interaction.user.send(LinkError.AuthenticationError)
                print("Wasn't able to verify with link!")
                return
            print(tokens.model_dump_json)
            if tokens:
                file = open(tokens_file, 'w+')
                file.write(tokens.model_dump_json())
                auth_mgr.oauth = OAuth2TokenResponse.model_validate_json(tokens.model_dump_json())
                await antique_message.delete()
                if do_sisu == False:
                    await interaction.user.send(LinkPhrases.Success_1)
                else:
                    await interaction.user.send(LinkPhrases.Success_1_Queue)
            print("Completed message auth")
        if do_sisu == False:
            await auth_mgr.refresh_tokens()
            with open(tokens_file, mode="w") as f:
                f.write(auth_mgr.oauth.json())


        if do_sisu == True:
            xalmanager = XALManager(session, uuid.uuid4(), APP_PARAMS_XBOX_APP, CLIENT_PARAMS_ANDROID)
            try:
                with open(('./accounts'+f'/{interaction.user.id}_sisu.json')) as f:
                    code_verifier = xalmanager._generate_code_verifier()
                    code_challenge = xalmanager._get_code_challenge_from_code_verifier(code_verifier)
                    device_token = await xalmanager.request_device_token()
                    state = xalmanager._generate_random_state()
                    test = await xalmanager.request_sisu_authentication(device_token.token, code_challenge, state)
                    print(f"User previously authenticated with SISU")
                    data = json.loads(f.read())
                    print(data)
                    sisu_tokens = await xalmanager.refresh_token(data['refresh_token'])
                    print("Refreshed SISU")
                    sisu_tokens = await xalmanager.do_sisu_authorization(test[1], json.loads(sisu_tokens.content)['access_token'], device_token.token, data['refresh_token'])
            except FileNotFoundError as e:
                print("No SISU authentication detected.")
                try:
                    code_verifier = xalmanager._generate_code_verifier()
                    code_challenge = xalmanager._get_code_challenge_from_code_verifier(code_verifier)
                    device_token = await xalmanager.request_device_token()
                    state = xalmanager._generate_random_state()
                    test = await xalmanager.request_sisu_authentication(device_token.token, code_challenge, state)
                    request_id = test[1]
                    print(test[0].msa_oauth_redirect)
                    await interaction.user.send("Doing SISU authentication now. Please follow the previous instructions again: " + LinkPhrases.Notify_User)
                    antique_message = await interaction.user.send(f"# SISU AUTHENTICATION: \n\n" + LinkPhrases.Instructions.format(test[0].msa_oauth_redirect))
                    def check(m):
                        return m.author.id == interaction.user.id
                    msg = await client.wait_for("message", check = check)
                    code = get_code(msg.content)
                    if code:
                        sisu_auth = await xalmanager.exchange_code_for_token(code, code_verifier)
                        refresh_sisu = sisu_auth.refresh_token
                        sisu_tokens = await xalmanager.do_sisu_authorization(request_id, sisu_auth.access_token, device_token.token, refresh_sisu)
                        print(sisu_tokens.model_dump_json())
                        file = open(('./accounts'+f'/{interaction.user.id}_sisu.json'), 'w+')
                        file.write(sisu_tokens.model_dump_json())
                    else:
                        await interaction.user.send(LinkError.ParsingError)
                except Exception as e:
                    print(e)
                    await interaction.user.send("Something went wrong when trying SISU authentication, please try again!")
        print("Reached end of auth")
        if do_sisu == True:
            return sisu_tokens
        else:
            print(auth_mgr)
            print("Printing finalized auth manager")
            return auth_mgr