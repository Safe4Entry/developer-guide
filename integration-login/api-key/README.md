# Login with an API key

You send your Client ID and API key. You get an access token back.

## What you need

The Safe4Entry administrator gives you:

| Value | Example |
|---|---|
| Client ID | `s4e_cl_7f3a9c…` |
| API key | `s4e_ak_Qm9vb…` — **secret** |
| Token endpoint | `https://<s4e-host>/api/integration/oauth2/token` |

Treat the API key like a password. The administrator sees it only once. If you lose it, they create a new one.

## The request

- Method: `POST` to the token endpoint.
- Authentication: HTTP **Basic** — username = Client ID, password = API key.
- Body: a **form** (`application/x-www-form-urlencoded`), **not JSON**: `grant_type=client_credentials`.

```http
POST /api/integration/oauth2/token
Authorization: Basic base64(<client id>:<api key>)
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
```

`base64(...)` is not literal text. Replace it with the Base64 of `<client id>:<api key>`: the two values joined with a colon (`:`, not a space).
To make it yourself: `echo -n "<client id>:<api key>" | base64` (keep the `-n`, otherwise a newline is encoded too and login fails).
The real header looks like `Authorization: Basic czRlX2NsXzdmM2E5YzpzNGVfYWtfUW05dmI=`.

Most HTTP clients build it for you: you give them the Client ID (username) and the API key (password) separately.
In Postman or Insomnia, don't write the header yourself. Open the **Authorization** tab, choose **Basic Auth** and fill in both fields.

If your client can't send Basic authentication, put `client_id` and `client_secret` (the API key) into the form body instead.

The response is described in [The token](../README.md#the-token).

## Quick test with the script

1. Copy the config template and fill in your values:

   ```bash
   cp config.example.json config.json
   ```

   ```json
   {
     "client_id": "s4e_cl_...",
     "api_key": "s4e_ak_...",
     "token_endpoint": "https://<s4e-host>/api/integration/oauth2/token"
   }
   ```

   `config.json` is in `.gitignore`, so it won't be committed.

2. Run the script (Python 3.9+, no extra packages):

   ```bash
   python3 get_token.py          # prints the token
   TOKEN=$(python3 get_token.py) # store the token in a variable
   ```

Source: [`get_token.py`](get_token.py).

## Examples

All examples get a token and call `GET /me`. Replace the values with yours.
In real code, read the API key from a secret manager or an environment variable.

### curl

```bash
# 1. get a token (needs jq to read the JSON; otherwise copy "access_token" from the response)
TOKEN=$(curl -s -u "s4e_cl_7f3a9c…:s4e_ak_Qm9vb…" \
  -d grant_type=client_credentials \
  https://<s4e-host>/api/integration/oauth2/token | jq -r .access_token)

# 2. call the API with it
curl -H "Authorization: Bearer $TOKEN" https://<s4e-host>/api/integration/v1/me
```

`-u` sends Basic authentication. `-d` sends a form.

### Python

```bash
pip install requests
```

```python
import os
import requests

CLIENT_ID = "s4e_cl_7f3a9c…"
API_KEY = os.environ["S4E_API_KEY"]
TOKEN_ENDPOINT = "https://<s4e-host>/api/integration/oauth2/token"
API = "https://<s4e-host>/api/integration/v1"

response = requests.post(
    TOKEN_ENDPOINT,
    auth=(CLIENT_ID, API_KEY),                   # Basic authentication
    data={"grant_type": "client_credentials"},   # data= sends a form, not JSON
)
response.raise_for_status()
token = response.json()["access_token"]

me = requests.get(f"{API}/me", headers={"Authorization": f"Bearer {token}"})
print(me.json())
```

### Node.js (18+)

```javascript
const CLIENT_ID = 's4e_cl_7f3a9c…';
const API_KEY = process.env.S4E_API_KEY;
const TOKEN_ENDPOINT = 'https://<s4e-host>/api/integration/oauth2/token';
const API = 'https://<s4e-host>/api/integration/v1';

const basic = Buffer.from(`${CLIENT_ID}:${API_KEY}`).toString('base64');
const response = await fetch(TOKEN_ENDPOINT, {
  method: 'POST',
  headers: { Authorization: `Basic ${basic}` },
  body: new URLSearchParams({ grant_type: 'client_credentials' }), // sends a form, not JSON
});
if (!response.ok) throw new Error(`${response.status} ${await response.text()}`);
const { access_token } = await response.json();

const me = await fetch(`${API}/me`, { headers: { Authorization: `Bearer ${access_token}` } });
console.log(await me.json());
```

### Java (11+)

No extra libraries needed.

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class ApiKeyLogin {
    static final String CLIENT_ID = "s4e_cl_7f3a9c…";
    static final String API_KEY = System.getenv("S4E_API_KEY");
    static final String TOKEN_ENDPOINT = "https://<s4e-host>/api/integration/oauth2/token";
    static final String API = "https://<s4e-host>/api/integration/v1";

    public static void main(String[] args) throws Exception {
        String basic = Base64.getEncoder()
                .encodeToString((CLIENT_ID + ":" + API_KEY).getBytes(StandardCharsets.UTF_8));

        HttpRequest request = HttpRequest.newBuilder(URI.create(TOKEN_ENDPOINT))
                .header("Authorization", "Basic " + basic)
                .header("Content-Type", "application/x-www-form-urlencoded")
                .POST(HttpRequest.BodyPublishers.ofString("grant_type=client_credentials"))
                .build();

        HttpClient client = HttpClient.newHttpClient();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() != 200) throw new RuntimeException(response.statusCode() + " " + response.body());

        // Quick extraction to avoid a dependency. In real code use a JSON library (Jackson, Gson, …).
        Matcher m = Pattern.compile("\"access_token\"\\s*:\\s*\"([^\"]+)\"").matcher(response.body());
        if (!m.find()) throw new RuntimeException("No access_token in " + response.body());
        String token = m.group(1);

        HttpRequest me = HttpRequest.newBuilder(URI.create(API + "/me"))
                .header("Authorization", "Bearer " + token)
                .build();
        System.out.println(client.send(me, HttpResponse.BodyHandlers.ofString()).body());
    }
}
```

### Postman, Insomnia

These tools get and refresh the token for you:

- **Postman** — *Authorization* → *OAuth 2.0* → *Grant type*: *Client Credentials*.
  *Access Token URL*: the token endpoint. *Client ID*: your Client ID. *Client Secret*: the API key.
  *Client Authentication*: *Send as Basic Auth header*. Then *Get New Access Token*.
- **Insomnia** — *Auth* → *OAuth 2.0* → *Grant Type*: *Client Credentials*, the same fields.

## Replace the API key

Do it before the key expires, or right away if it may have leaked. You can have up to 5 active keys, so there is no downtime:

1. The administrator creates a new API key and sends it to you.
2. You switch your system to the new key.
3. The administrator revokes the old key.
