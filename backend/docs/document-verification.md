# Supplier document verification

Supplier declarations and issuer verification are separate. Selecting **Present** never creates a verified badge or passes a certificate readiness check by itself. Verification receipts are stored in PostgreSQL and scoped to the authenticated user and workspace; the browser never persists them in localStorage.

## Supported checks

| Profile evidence | Sandbox flow | Conditions for a live badge |
| --- | --- | --- |
| GST registration | EntityLocker, `gstn_details` | Explicit consent, trusted XML signature, exact GSTIN and business-name match, and an active GST registry record |
| Contact person's PAN | DigiLocker, `pan` | Explicit consent, trusted XML signature, exact PAN and contact-name match |
| ISO 9001 or manufacturer authorization | No supported issuer integration yet | Remains unverified; requires an authoritative issuer check |

The PAN badge reads **PAN verified by DigiLocker**. It does not verify the supplier's GST, ISO, or manufacturer certificate. GST reads **GST verified by EntityLocker**. Test-environment results use `test_passed` and cannot create live badges. A name change, failed check, or expired receipt prevents a matching badge; only live, unexpired GST receipts can pass a GST readiness requirement.

## Runtime configuration

Set these on the backend:

- `SANDBOX_ENVIRONMENT`: `test` (default) or `live`. Test and production use separate Sandbox credentials.
- `SANDBOX_API_KEY` and `SANDBOX_API_SECRET`: distinct server credentials, never `NEXT_PUBLIC_*` values. An identical key/secret pair is rejected before a provider request.
- `SANDBOX_RETURN_URL`: the HTTPS URL of the supplier profile, with no existing query or fragment, for example `https://your-domain.example/dashboard/profile`. Enable this callback with Sandbox as required by your account.
- `DIGILOCKER_SIGNING_CERTIFICATE_PATH`: the trusted Digital India Corporation PEM **public signing certificate** for DigiLocker PAN documents, obtained from an authenticated issuer/Sandbox channel.
- `ENTITYLOCKER_SIGNING_CERTIFICATE_PATH`: the trusted NeGD public signing certificate for EntityLocker GST documents. Configure the appropriate certificate for each enabled flow. The signer must be within its current validity period. Never trust a certificate merely because it is embedded in a user-supplied document. No private signing key is needed.
- `CERTIFICATE_VERIFICATION_TTL_HOURS`: defaults to 24; accepted receipt duration is bounded to 1–168 hours and any document expiry, whichever is earlier.

OAuth consent requires valid Sandbox credentials and the HTTPS return URL. A signing certificate is required when checking the returned document, rather than when opening consent. Without that certificate a completed consent stays in `review` and cannot award a verified badge.

### Local demo callback

Sandbox requires an HTTPS callback even when the frontend is at `http://localhost:3000`. Run the dedicated callback relay and expose only its port through a temporary HTTPS tunnel:

```sh
uv run python -m app.cli.digilocker_callback
cloudflared tunnel --url http://127.0.0.1:8766 --no-autoupdate --protocol http2
```

Set `SANDBOX_RETURN_URL=https://<the-generated-host>.trycloudflare.com/callback` in the backend `.env`, then restart the backend (or trigger its development reloader). Keep both processes running throughout the demo; restarting the tunnel changes its hostname. The relay accepts only a verification UUID and redirects to the local profile. It does not forward provider tokens or codes, expose the application, or grant verification. For a deployed app, set the return URL directly to its public HTTPS profile page instead. See [Cloudflare Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).

The project's secret-safety rules require runtime injection through `asm-exec`, using references such as `{{resolve:secretsmanager:your-secret-id:SecretString:api_key}}` and `{{resolve:secretsmanager:your-secret-id:SecretString:api_secret}}`. Resolve these into the backend process environment. Do not put the reference itself in a credential field without the resolver, read raw Secrets Manager values into an agent session, commit credentials, or return them to the browser. The `aws-secrets-manager` skill and `asm-exec` must be available before using that live setup workflow. This change does not install live credentials or provision AWS infrastructure.

Enable EntityLocker and GST Public/Search GSTIN access for the GST flow, and DigiLocker for PAN. Actual issuer consent must be completed by the document holder or authorized business representative. No Aadhaar numbers, OTPs, DigiLocker passwords, or scans are collected by TenderLens.

Set `TENDERLENS_API_URL` on the Next.js server to the backend origin (default `http://127.0.0.1:8000`). Firebase ID tokens are forwarded through the same-origin `/api/certificates` routes; Sandbox credentials stay on the backend. Real Firebase sign-in is required in live mode; development mock tokens cannot initiate live verification.

Apply the migration and start the backend using its configured runtime environment:

```sh
uv run alembic upgrade head
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Protocol and retained evidence

1. Reserve a verification record before submitting the consent session. Idempotency keys and a workspace lock prevent duplicate submissions. A workspace is limited to ten session starts in 24 hours.
2. Initiate the documented Sandbox REST consent flow, then redirect the holder to the returned official DigiLocker/EntityLocker destination. There is no client-side API key or SDK completion event that can award a badge.
3. After the holder returns, check the provider session from the server. Its ID, entity type, successful status, and `documents_consented` must match the reserved check.
4. Retrieve the provider's XML over HTTPS, enforce size and host restrictions, and validate its enveloped signature against the configured trusted certificate. Read only the signed certificate payload. Unsigned PDFs and self-uploaded documents cannot be verified.
5. Match the holder and document number exactly after conservative name normalization. GST additionally requires the registry's matching legal name, GSTIN, and `Active` status.
6. Persist the receipt, issuer, document hash, timestamps, and verification outcome. Downloaded XML, document URLs, OAuth authorization URLs, and provider access tokens are not stored in the receipt or exposed by its public API. Provider access tokens are cached only in process memory. Identifiers in API receipts are masked; expected identifiers remain in the workspace-scoped database record to bind the check.

Unknown submission outcomes require operator reconciliation; the application does not blindly resubmit them. Failed, unsupported, missing-consent, or signature-mismatched documents stay unverified. Automatic status polling is bounded to ten minutes and pauses in hidden tabs.

## Sources

- [DigiLocker REST consent flow](https://developer.sandbox.co.in/api-reference/kyc/digilocker/endpoints/initiate_session)
- [EntityLocker REST consent flow](https://developer.sandbox.co.in/api-reference/kyc/entitylocker/endpoints/initiate_session)
- [EntityLocker signed document format](https://developer.sandbox.co.in/api-reference/kyc/entitylocker/sample-responses)
- [GST Search API](https://developer.sandbox.co.in/api-reference/gst/compliance/endpoints/public/search_gstin)
- [SignXML verification and trust configuration](https://xml-security.github.io/signxml/)
