# Login with a signing key

You keep a **private key**. Safe4Entry has your **public key**.
To log in, you sign a short JWT with the private key. Safe4Entry checks the signature and gives you an access token.

No secret ever leaves your system. The standard is *private_key_jwt* ([RFC 7523](https://datatracker.ietf.org/doc/html/rfc7523)).

## Step 1 — Create a key pair

Run this where your integration runs (needs OpenSSL):

```bash
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out s4e-private.pem
openssl pkey -in s4e-private.pem -pubout -out s4e-public.pem
```

| File | What to do with it |
|---|---|
| `s4e-private.pem` | **Keep it secret.** Never send it to anyone, not even to Safe4Entry. |
| `s4e-public.pem` | Send it to the Safe4Entry administrator. It is not secret, e-mail is fine. |

Only P-256 EC keys (algorithm **ES256**) are accepted.

## Step 2 — Get your values

After the administrator registers your public key, they give you:

| Value | Example |
|---|---|
| Client ID | `s4e_cl_7f3a9c…` |
| Key ID | `k1` |
| Token endpoint | `https://<s4e-host>/api/integration/oauth2/token` |

## Step 3 — Sign a JWT

The JWT is called the *client assertion*.

**Header**

```json
{ "alg": "ES256", "kid": "k1" }
```

**Payload**

```json
{
  "iss": "s4e_cl_7f3a9c…",
  "sub": "s4e_cl_7f3a9c…",
  "aud": "https://<s4e-host>/api/integration/oauth2/token",
  "iat": 1760000000,
  "exp": 1760000060,
  "jti": "0b6e2d4a-5c1f-4f0e-9d7b-2a8c3e1f6a90"
}
```

| Field | Value |
|---|---|
| `kid` | your Key ID |
| `iss`, `sub` | your Client ID (both the same) |
| `aud` | the token endpoint, **exactly** as given |
| `iat` | now, in seconds (Unix time) |
| `exp` | `iat` + 60 seconds. At most 5 minutes. |
| `jti` | a **new** random value every time (e.g. a UUID). A used one is refused. |

Use a JWT library. You give it the payload, the private key, `ES256` and the `kid`. It returns the signed string.
See the examples below, or find a library for your language at [jwt.io/libraries](https://jwt.io/libraries).

## Step 4 — Exchange it for a token

Send a **form** (`application/x-www-form-urlencoded`), **not JSON**:

```http
POST /api/integration/oauth2/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer
&client_assertion=eyJhbGciOiJFUzI1NiIsImtpZCI6ImsxIn0…
```

The response is described in [The token](../README.md#the-token).

## Quick test with the script

1. Put `s4e-private.pem` next to the script (or anywhere — see `private_key_file` below).
2. Copy the config template and fill in your values:

   ```bash
   cp config.example.json config.json
   ```

   ```json
   {
     "client_id": "s4e_cl_...",
     "key_id": "k1",
     "private_key_file": "s4e-private.pem",
     "token_endpoint": "https://<s4e-host>/api/integration/oauth2/token"
   }
   ```

   `private_key_file` can be absolute, or relative to `config.json`.
   `config.json` and `*.pem` are in `.gitignore`, so they won't be committed.

3. Run the script (Python 3.9+):

   ```bash
   pip install "pyjwt[crypto]"
   python3 get_token.py          # prints the token
   TOKEN=$(python3 get_token.py) # store the token in a variable
   ```

Source: [`get_token.py`](get_token.py).

## Examples

All examples sign a JWT, get a token and call `GET /me`.

### Python

```bash
pip install "pyjwt[crypto]" requests
```

```python
import time
import uuid

import jwt
import requests

CLIENT_ID = "s4e_cl_7f3a9c…"
KEY_ID = "k1"
TOKEN_ENDPOINT = "https://<s4e-host>/api/integration/oauth2/token"
API = "https://<s4e-host>/api/integration/v1"
PRIVATE_KEY = open("s4e-private.pem").read()

now = int(time.time())
assertion = jwt.encode(
    {"iss": CLIENT_ID, "sub": CLIENT_ID, "aud": TOKEN_ENDPOINT,
     "iat": now, "exp": now + 60, "jti": str(uuid.uuid4())},
    PRIVATE_KEY, algorithm="ES256", headers={"kid": KEY_ID},
)

response = requests.post(TOKEN_ENDPOINT, data={  # data= sends a form, not JSON
    "grant_type": "client_credentials",
    "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
    "client_assertion": assertion,
})
response.raise_for_status()
token = response.json()["access_token"]

me = requests.get(f"{API}/me", headers={"Authorization": f"Bearer {token}"})
print(me.json())
```

### TypeScript (Node.js 18+)

```bash
npm install jose
npm install -D typescript tsx @types/node
```

```typescript
import { readFileSync } from 'node:fs';
import { randomUUID } from 'node:crypto';
import { SignJWT, importPKCS8 } from 'jose';

interface TokenResponse {
  access_token: string;
  token_type: 'Bearer';
  expires_in: number;
  scope: string;
}

const CLIENT_ID = 's4e_cl_7f3a9c…';
const KEY_ID = 'k1';
const TOKEN_ENDPOINT = 'https://<s4e-host>/api/integration/oauth2/token';
const API = 'https://<s4e-host>/api/integration/v1';

async function getToken(): Promise<TokenResponse> {
  const privateKey = await importPKCS8(readFileSync('s4e-private.pem', 'utf8'), 'ES256');

  const now = Math.floor(Date.now() / 1000);
  const assertion = await new SignJWT({})
    .setProtectedHeader({ alg: 'ES256', kid: KEY_ID })
    .setIssuer(CLIENT_ID)
    .setSubject(CLIENT_ID)
    .setAudience(TOKEN_ENDPOINT)
    .setIssuedAt(now)
    .setExpirationTime(now + 60)
    .setJti(randomUUID())
    .sign(privateKey);

  const response = await fetch(TOKEN_ENDPOINT, {
    method: 'POST',
    body: new URLSearchParams({ // sends a form, not JSON
      grant_type: 'client_credentials',
      client_assertion_type: 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
      client_assertion: assertion,
    }),
  });
  if (!response.ok) throw new Error(`${response.status} ${await response.text()}`);
  return (await response.json()) as TokenResponse;
}

const { access_token } = await getToken();
const me = await fetch(`${API}/me`, { headers: { Authorization: `Bearer ${access_token}` } });
console.log(await me.json());
```

Save it as `login.ts` (top-level `await` needs ES modules: set `"type": "module"` in `package.json`) and run `npx tsx login.ts`.

### Java (11+)

No extra libraries needed. The key must be in PKCS#8 format — the `openssl genpkey` command above creates it.

```java
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.KeyFactory;
import java.security.PrivateKey;
import java.security.Signature;
import java.security.spec.PKCS8EncodedKeySpec;
import java.util.Base64;
import java.util.UUID;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class SigningKeyLogin {
    static final String CLIENT_ID = "s4e_cl_7f3a9c…";
    static final String KEY_ID = "k1";
    static final String TOKEN_ENDPOINT = "https://<s4e-host>/api/integration/oauth2/token";
    static final String API = "https://<s4e-host>/api/integration/v1";

    public static void main(String[] args) throws Exception {
        PrivateKey key = readPrivateKey(Path.of("s4e-private.pem"));

        long now = System.currentTimeMillis() / 1000;
        String header = "{\"alg\":\"ES256\",\"kid\":\"" + KEY_ID + "\"}";
        String payload = "{\"iss\":\"" + CLIENT_ID + "\",\"sub\":\"" + CLIENT_ID + "\""
                + ",\"aud\":\"" + TOKEN_ENDPOINT + "\""
                + ",\"iat\":" + now + ",\"exp\":" + (now + 60)
                + ",\"jti\":\"" + UUID.randomUUID() + "\"}";
        String assertion = sign(header, payload, key);

        String form = "grant_type=client_credentials"
                + "&client_assertion_type=" + encode("urn:ietf:params:oauth:client-assertion-type:jwt-bearer")
                + "&client_assertion=" + encode(assertion);
        HttpRequest request = HttpRequest.newBuilder(URI.create(TOKEN_ENDPOINT))
                .header("Content-Type", "application/x-www-form-urlencoded")
                .POST(HttpRequest.BodyPublishers.ofString(form))
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

    /** header.payload.signature, each part Base64URL-encoded. */
    static String sign(String header, String payload, PrivateKey key) throws Exception {
        Base64.Encoder b64 = Base64.getUrlEncoder().withoutPadding();
        String unsigned = b64.encodeToString(header.getBytes(StandardCharsets.UTF_8)) + "."
                + b64.encodeToString(payload.getBytes(StandardCharsets.UTF_8));
        // JWT needs the raw R|S signature format (P1363), not the default DER format
        Signature signature = Signature.getInstance("SHA256withECDSAinP1363Format");
        signature.initSign(key);
        signature.update(unsigned.getBytes(StandardCharsets.US_ASCII));
        return unsigned + "." + b64.encodeToString(signature.sign());
    }

    static PrivateKey readPrivateKey(Path file) throws Exception {
        String pem = Files.readString(file)
                .replace("-----BEGIN PRIVATE KEY-----", "")
                .replace("-----END PRIVATE KEY-----", "")
                .replaceAll("\\s", "");
        return KeyFactory.getInstance("EC")
                .generatePrivate(new PKCS8EncodedKeySpec(Base64.getDecoder().decode(pem)));
    }

    static String encode(String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8);
    }
}
```

In a real project, a JWT library such as [Nimbus JOSE + JWT](https://connect2id.com/products/nimbus-jose-jwt)
does the signing for you.

### Testing tools

Postman and Insomnia can't sign the JWT themselves. Get a token with the [script](#quick-test-with-the-script)
and paste it as a **Bearer token**.

## Common mistakes

If you get `401 invalid_client`, check:

- `aud` is **exactly** the token endpoint (`http` vs `https`, no trailing `/`).
- `kid` matches the Key ID the administrator gave you.
- You signed with the private key that belongs to the registered public key.
- Your server clock is correct (use NTP). `iat` and `exp` must match the real time.
- `jti` is new for every request.
