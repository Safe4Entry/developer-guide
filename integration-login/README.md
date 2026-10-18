# Integration login

Your system logs in to Safe4Entry with **client credentials** and gets an **access token**.
Then it sends the token with every API call.

The standard is OAuth 2.0 *client credentials*, so most OAuth libraries support it.

## Choose a method

The Safe4Entry administrator picks the method when they create your API access. Ask them which one you have.

| | [API key](api-key/) | [Signing key](signing-key/) |
|---|---|---|
| You get | Client ID + API key | Client ID + Key ID |
| The secret | the API key (the administrator sends it to you) | your private key (it never leaves your system) |
| Get a token | 1 HTTP request | sign a short JWT, then 1 HTTP request |

## The token

Both methods return the same response:

```json
{
  "access_token": "s4e_at_Xk2…",
  "token_type": "Bearer",
  "expires_in": 1800,
  "scope": "suppliers:read suppliers:write"
}
```

- The token is valid for **30 minutes** (`expires_in` is in seconds).
- **Reuse it** until it is about to expire. You can get at most **10 tokens per minute** (DDOS protection).
- `scope` lists what you may do. The administrator decides it, if you need more or different permissions, please contact the company administrator  

## Use the token

Send it in the `Authorization` header:

```bash
curl -H "Authorization: Bearer s4e_at_Xk2…" https://<s4e-host>/api/integration/v1/me
```

`GET /me` is the best first test. It needs no scope and shows who you are:

```json
{
  "clientId": "s4e_cl_7f3a9c…",
  "name": "SAP HR sync",
  "company": { "id": "…", "name": "Example s.r.o." },
  "scopes": ["suppliers:read", "suppliers:write"],
  "token": { "expiresAt": "2026-10-08T10:30:00Z", "keyId": "k1" }
}
```

If an API call returns `401`, the token has expired or was revoked. Get a new token and retry once.

## When login fails

The token endpoint returns an OAuth error:

```json
{ "error": "invalid_client", "error_description": "Client authentication failed" }
```

| Status | `error` | Meaning |
|---|---|---|
| 400 | `invalid_request` | Bad request. Check if all information are present and correct. |
| 400 | `unsupported_grant_type` | `grant_type` is not `client_credentials`. |
| 401 | `invalid_client` | Login failed. See below. |
| 429 | `slow_down` | Too many token requests.  |

`invalid_client` never says **why**, for security. The administrator sees the exact reason in the
**activity log** of your API access. Common causes:

- wrong Client ID or key;
- an API key sent to a signing-key access, or the other way round;
- your IP address is not on the allowed list;
- the key expired or was revoked, or the API access is deactivated.

## Keep it safe

- Store the API key or private key in a secret manager or an environment variable. Never commit it to Git.
- Never log tokens or keys.
- If a key may have leaked, ask the administrator to revoke it. It stops working immediately.
