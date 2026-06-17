---
title: GCP Setup Guide for Hermes on Zo
description: Step-by-step guide to configure GCP OAuth 2.0 credentials for Hermes agent workspace integration (Gmail, Drive, Sheets) on Zo Computer.
created: 2026-05-03
updated: 2026-05-03
---
# GCP Setup for Hermes on Zo

Hermes uses **OAuth 2.0** — not service accounts — to access Gmail, Google Sheets, and Google Drive on behalf of the user. This is the only supported authentication method.

## Overview

Hermes needs programmatic read/write access to:

| Service | Purpose |
| --- | --- |
| **Gmail** | Send completed HHE-200 packages to site evaluators |
| **Google Sheets** | Read new form submission rows as intake data |
| **Google Drive** | Retrieve uploaded sketches and save generated PDFs |

---

## Required GCP APIs

Before creating credentials, enable these APIs in your GCP project:

- **Gmail API**
- **Google Sheets API**
- **Google Drive API**

---

## Step 1: Enable APIs in GCP Console

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and select your project.
2. Navigate to **APIs & Services → Library**.
3. Search for and enable each API above.

**Console path:** `APIs & Services > Library`

---

## Step 2: Create OAuth 2.0 Client ID

1. Navigate to **APIs & Services → Credentials**.
2. Click **+ Create Credentials → OAuth client ID**.

**Console path:** `APIs & Services > Credentials > Create Credentials > OAuth client ID`

### First-Time Setup: Consent Screen

If this is your first OAuth client in this GCP project, Google will prompt you to configure an **OAuth consent screen** before you can create credentials:

1. On the **OAuth consent screen** page, select **External** and click **Create**.
2. Fill in the required fields:
   - **App name** — e.g., `Hermes on Zo`
   - **User support email** — your Gmail address
   - **Developer contact email** — your Gmail address
3. Click **Save and Continue**. You can skip Scopes for now — Hermes will request only the scopes it needs.
4. Add any test users if prompted (optional for internal use).

### Complete Credential Creation

1. Back at **Create OAuth client ID**, select **Desktop app** (or **Other** if Desktop is not available as an option).
2. Give it a name — e.g., `Hermes Workspace Client`.
3. Click **Create**.
4. A dialog will appear showing your **Client ID** and **Client Secret**.
5. Click **Download JSON** to download the credentials file.

---

## Step 3: Save the Credentials File

After downloading, **rename the file** to:

```markdown
google_oauth_credentials.json
```

> Important: The default filename from GCP (e.g., `file client_secret_xxxx.json`) will not work — Hermes expects the specific filename above.

Store it at:

```markdown
~/.config/google_oauth_credentials.json
```

If the `~/.config/` directory does not exist, create it:

```bash
mkdir -p ~/.config
```

Then move or copy the credentials file:

```bash
mv ~/Downloads/client_secret_xxxx.json ~/.config/google_oauth_credentials.json
```

---

## Step 4: Run Initial Auth Flow

Hermes will generate an authorization URL. You visit it in your browser, grant permissions, receive a code, and paste it back.

```bash
hermes auth init --google-workspace
```

**What happens during the flow:**

1. Hermes prints a URL to the terminal.
2. Open the URL in your browser.
3. Sign in to the Google account you want Hermes to use.
4. Review and grant the requested permissions.
5. The browser will show a code (e.g., `4/0AdeuB...`). Copy it.
6. Paste the code back into the terminal prompt.
7. Tokens are automatically saved to `file ~/.config/google_token_store.json`.

> **Note:** The tokens are long-lived but may expire after account changes, password resets, or extended inactivity. If Hermes reports access errors later, re-run the auth init step.

---

## Step 5: Verify Access

Confirm Hermes can reach each service:

```bash
hermes auth verify
```

Expected output confirms:

- Gmail send access
- Sheets read access
- Drive read access

---

## OAuth Scopes

Hermes uses exactly these three scopes:

| Service | Scope |
| --- | --- |
| Gmail | `https://www.googleapis.com/auth/gmail.send` |
| Sheets | `https://www.googleapis.com/auth/spreadsheets.readonly` |
| Drive | `https://www.googleapis.com/auth/drive.readonly` |

---

## Token and Credential Paths

| File | Path | Purpose |
| --- | --- | --- |
| Credentials |  | OAuth 2.0 client ID and secret |
| Token store |  | Access and refresh tokens |

Both files must be present for Hermes to authenticate. Do not share these files — they grant access to your Google account.

---

## Troubleshooting

### "Invalid client credentials" error

- Verify `file google_oauth_credentials.json` is at the exact path `file ~/.config/google_oauth_credentials.json`
- Verify the file is valid JSON (no extra whitespace or characters)
- Ensure the file was downloaded from GCP, not copy-pasted manually

### "Token expired" errors

- Re-run `hermes auth init --google-workspace` to refresh tokens without re-downloading credentials
- If the account password was changed, you may need to delete `file google_token_store.json` and re-authenticate from scratch

### "Access denied" or missing Drive/Sheets data

- Ensure the Google account used during auth has access to the relevant Drive files and Sheets
- For shared Drive files, verify the account has at least "Viewer" access

### First-time consent screen rejected

- If you accidentally clicked "deny," delete `file google_token_store.json` and re-run `hermes auth init`
- If you are part of an organization with Google Workspace restrictions, you may need an admin to approve the app

### Consent screen says "App not verified"

- This is expected for personal/development OAuth flows
- Click "Advanced" → "Go to \[App Name\] (unsafe)" to proceed
- This only affects the initial setup; verified status is not required for personal use