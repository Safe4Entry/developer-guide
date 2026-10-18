#!/usr/bin/env python3
"""
Gets an access token with an API key and prints it.

    cp config.example.json config.json   # then fill it in
    python3 get_token.py                 # prints the token

Only the token goes to stdout, so this works: TOKEN=$(python3 get_token.py)
No extra packages needed.
"""
import argparse
import base64
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def post_form(url, form, headers):
    request = urllib.request.Request(url, data=urllib.parse.urlencode(form).encode(), headers=headers)
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description="Get a Safe4Entry access token with an API key.")
    parser.add_argument("--config", default=Path(__file__).with_name("config.json"), help="default: config.json")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        sys.exit(f"{config_path} not found. Copy config.example.json to config.json and fill it in.")
    config = json.loads(config_path.read_text())

    # HTTP Basic authentication: base64("client_id:api_key")
    basic = base64.b64encode(f"{config['client_id']}:{config['api_key']}".encode()).decode()
    try:
        body = post_form(config["token_endpoint"], {"grant_type": "client_credentials"},
                         {"Authorization": f"Basic {basic}"})
    except urllib.error.HTTPError as e:
        sys.exit(f"Token request failed: {e.code} {e.read().decode()}")

    print(f"Token OK. Scopes: {body.get('scope')}. Expires in {body['expires_in']} s.", file=sys.stderr)
    print(body["access_token"])


if __name__ == "__main__":
    main()
