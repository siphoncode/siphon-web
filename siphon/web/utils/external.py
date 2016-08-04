
import json
import base64
from urllib.parse import quote, unquote, unquote_to_bytes

import rsa
from django.conf import settings

ALLOWED_ACTIONS = ('push', 'pull', 'submit')


class HandshakeError(Exception):
    pass

def get_private_key():
    with open(settings.HANDSHAKE_PRIVATE_KEY, 'rb') as fp:
        return rsa.PrivateKey.load_pkcs1(fp.read())

def get_public_key():
    with open(settings.HANDSHAKE_PUBLIC_KEY, 'rb') as fp:
        return rsa.PublicKey.load_pkcs1_openssl_pem(fp.read())

def make_handshake(obj):
    payload = json.dumps(obj).encode('utf8')
    # Sign that bad boy
    key = get_private_key()
    signature = rsa.sign(payload, key, 'SHA-256')
    # Escape it so that it's suitable to be put in a URL.
    s = base64.b64encode(payload).decode('ascii')
    return map(quote, (s, signature))

def make_development_handshake(action, user_id, app_id):
    """
    Returns (<base64 encoded handshake token>, <base64 encoded signature>)
    where the token has been signed by our handshake private key. Each
    base64-encoded value has been suitably escaped to use in a URL.

    The token is JSON in the form:

        {"action": "push", "user_id": "some-user", "app_id": "arbABAa"}

    Note: the `user_id` referred to here is in fact User.username
    """
    assert action in ALLOWED_ACTIONS or action is None
    obj = {'user_id': user_id, 'app_id': app_id}
    if action:
        obj['action'] = action
    return make_handshake(obj)

def make_production_handshake(action, submission_id, app_id):
    """
    Returns (<base64 encoded handshake token>, <base64 encoded signature>)
    where the token has been signed by our handshake private key. Each
    base64-encoded value has been suitably escaped to use in a URL.

    The token is JSON in the form:

        {"action": "pull", "submission_id": "arbABAa", "app_id": "abc123"}
    """
    assert action in ALLOWED_ACTIONS
    return make_handshake({
        'action': action,
        'submission_id': submission_id,
        'app_id': app_id
    })

def verify_handshake(token, signature, action):
    """
    Decodes a handshake token (X-Siphon-Handshake-Token header) and verifies
    it against the given signature (X-Siphon-Handshake-Signature header).

    If it passes verification it decodes the payload's JSON. If this is a
    development handshake (i.e. tying a username to an app ID) it returns
    a tuple containing two strings:

        (<username>, <app-id>)

    The given app ID is guaranteed to be owned by the user. Otherwise,
    if this is a production handshake it returns:

        (<submission-id>, <app-id>)

    Note that production handshake's are not tied to a user.
    """
    # Note that rsa.verify() detects the SHA-256 hashing method for us
    payload = base64.b64decode(unquote(token))
    signature_bytes = unquote_to_bytes(signature)
    ok = rsa.verify(payload, signature_bytes, get_public_key())
    if not ok:
        raise HandshakeError()
    try:
        obj = json.loads(payload.decode('utf8'))
        if 'action' in obj and obj['action'] != action:
            raise HandshakeError()
        if 'user_id' in obj and 'app_id' in obj:
            return (obj['user_id'], obj['app_id'])
        else:
            return (obj['submission_id'], obj['app_id'])
    except (ValueError, KeyError):
        raise HandshakeError()
