# BOTPASS // VAULT

A highly secure, local-first password vault and 2FA authenticator designed for privacy, strong cryptography, and a stark, brutalist HUD interface. 

Botpass was built to completely replace cloud-based password managers and secondary authenticator apps. It stores everything locally, uses state-of-the-art encryption, and features a high-tech "Overwatch" dashboard aesthetic.

## KEY FEATURES

- **Local-First**: Your data never leaves your machine. No cloud, no subscriptions, no data breaches.
- **Integrated 2FA (TOTP)**: Completely replaces Google Authenticator/Authy. Store your Setup Keys and generate live 6-digit codes directly in the app.
- **Breach Detection**: Checks your passwords against *Have I Been Pwned* using **k-anonymity** (sending only the first 5 characters of a SHA-1 hash), ensuring complete privacy.
- **Password Generation**: Generate strong random passwords or memorable Diceware passphrases, complete with zxcvbn strength analysis.
- **Organization**: Categorize your entries with custom Tags and use live filtering to instantly find what you need.
- **Encrypted Backups**: Export and import your entire vault into a single encrypted `.botpass` file.
- **Multiple Interfaces**: Use the Web Dashboard, the standalone Desktop app, or the blazing-fast Terminal CLI.

## OVERWATCH HUD UI

The interface abandons generic, rounded design trends in favor of a brutalist, tactical Heads-Up Display (HUD) aesthetic. It features pure black backgrounds, sharp modular grid lines, high-contrast monospace typography, and neon green system accents. It is designed to look like a secure terminal, extending seamlessly from the Web UI down to the raw CLI.

## ARCHITECTURE & CRYPTO STACK

```text
+-------------------------------------------------------------+
|                     INTERFACES (3 clients)                  |
|                                                             |
|   [ CLI ]          [ Web (local) ]      [ Desktop (PyQt/ ]  |
|   (Python)           (Flask/JS)          Tauri wrapper)  ]  |
|      |                    |                     |           |
+------|--------------------|---------------------|-----------+
       |                    |                     |
       +--------------------+---------------------+
                            |
                            v
                 +----------------------+
                 |    Vault Core API    |
                 |   (Python module)    |
                 |  - Crypto engine     |
                 |  - DB abstraction    |
                 |  - Session mgmt      |
                 +----------+-----------+
                            |
                            v
                 +----------------------+
                 |   vault.db (SQLite)  |
                 |   + salt.bin         |
                 |   + config.json      |
                 +----------------------+
```

### Threat Model & Mitigations

| Threat | Mitigation |
|--------|-----------|
| **Database theft** | **AES-256-GCM** encryption. An attacker just gets gibberish. |
| **Brute force master pw** | **Argon2id** (64MB, 3 iterations, 4 threads) is memory-hard, rendering GPU brute-forcing ineffective. |
| **Domain tracking** | Domains are hashed via **HMAC-SHA256**. An attacker looking at the DB cannot even see which websites you use. |
| **Length leakage** | All payloads are padded to **128-byte blocks** (PKCS7-style) before encryption. An attacker cannot guess password length by analyzing ciphertext size. |
| **Swap attacks** | Each entry is encrypted with a unique nonce and Associated Data (AD). |
| **Memory dump** | The master key is held in memory only when unlocked. The vault auto-locks after 5 minutes of inactivity, attempting to zero out memory buffers. Clipboards clear automatically after 10 seconds. |

## HOW TO USE

### 1. Initialization
When you launch Botpass for the first time, you will be prompted to set a Master Password. **Do not lose this password.** It is the only key to decrypt your data.

### 2. Adding Entries & 2FA
Click `[ ADD NEW ]` or use the `add` command in the CLI. 
- Enter the domain, username, and password.
- **To setup 2FA**: Go to the website you are saving (e.g., GitHub), enable 2FA, and click "setup manually" to get a text code (e.g., `JBSWY3DPEHPK3PXP`). Paste this text into the **2FA Setup Key** field in Botpass.

### 3. Retrieving Passwords & Codes
- Find your entry in the list and click `[ REVEAL ]`.
- Your password will automatically be copied to your clipboard (and will wipe after 10 seconds).
- A system modal will appear showing your live 6-digit 2FA code. Click the code to copy it, then paste it into the website.

### 4. Backups
- Use the `[ EXPORT ]` button to generate an encrypted `.botpass` file containing your entire vault.
- Keep this file safe. If you ever lose your database, you can use `[ IMPORT ]` to restore everything, provided you still know the master password that was used when the backup was created.

## INSTALLATION & USAGE

Botpass requires Python 3.8+.

```bash
# 1. Clone the repository
git clone https://github.com/pratjk/botpass-password-vault.git
cd botpass

# 2. Setup virtual environment
python -m venv venv

# Activate venv on Windows:
.\venv\Scripts\activate
# Activate venv on Mac/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Running Botpass

**Terminal CLI:**
```bash
python -m botpass.cli.main
```

**Web Dashboard (runs on http://127.0.0.1:5000):**
```bash
python -m botpass.web.main
```

**Desktop App:**
```bash
python -m botpass.desktop.main
```

## SECURITY WARNINGS
- **If you forget your master password, your data is mathematically GONE. There is no "forgot password" mechanism.**
- Always back up your `vault.db` and `salt.bin` together, or use the built-in encrypted Export feature.
- This is a locally-hosted tool. The security of your vault relies on the security of your operating system.
