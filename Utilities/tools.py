import base64, uuid, time, json, hmac, hashlib, re



def generate_ms_cv():
    """
    Generate a MS Vector code
    """
    return f"{uuid.uuid4().hex[:8]}.{int(time.time() % 100)}"


def generate_signature(auth_token, request_body):
    """
    Generates a sha256 encoded signature, Not sure if this is even needed?
    """
    secret_key = b'xbox_sucks'
    message = (auth_token + json.dumps(request_body)).encode('utf-8')
    signature = hmac.new(secret_key, message, hashlib.sha256).digest()
    return base64.b64encode(signature).decode('utf-8')

def get_code(url):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, url)
    if len(url) == 0:
        return False
    print(url[0])
    match = re.search(r'code=([A-Za-z0-9._-]+)', url[0][0])
    if match:
        code = match.group(1)
        print("Returning code: ")
        print(code)
        return code
    else:
        return False
    
