#!/usr/bin/env python3
"""
Gets an access token with a signing key and prints it.

    pip install "pyjwt[crypto]"
    cp config.example.json config.json   # then fill it in
    python3 get_token.py                 # prints the token

Only the token goes to stdout, so this works: TOKEN=$(python3 get_token.py)
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

import jwt


def make_assertion(config, private_key):
    """A short JWT signed with your private key. It proves who you are."""
    now = int(time.time())
    payload = {
        "iss": config["client_id"],
        "sub": config["client_id"],
        "aud": config["token_endpoint"],
        "iat": now,
        "exp": now + 60,
        "jti": str(uuid.uuid4()),  # new for every request
    }
    return jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": config["key_id"]})


def post_form(url, form):
    request = urllib.request.Request(url, data=urllib.parse.urlencode(form).encode())
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description="Get a Safe4Entry access token with a signing key.")
    parser.add_argument("--config", default=Path(__file__).with_name("config.json"), help="default: config.json")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        sys.exit(f"{config_path} not found. Copy config.example.json to config.json and fill it in.")
    config = json.loads(config_path.read_text())

    # a relative key path is relative to the config file
    key_path = config_path.parent / Path(config["private_key_file"]).expanduser()
    private_key = key_path.read_text()

    try:
        body = post_form(config["token_endpoint"], {
            "grant_type": "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": make_assertion(config, private_key),
        })
    except urllib.error.HTTPError as e:
        sys.exit(f"Token request failed: {e.code} {e.read().decode()}")

    print(f"Token OK. Scopes: {body.get('scope')}. Expires in {body['expires_in']} s.", file=sys.stderr)
    print(body["access_token"])


if __name__ == "__main__":
    main()
