# 🔐 Cryptokeep v2 (botpass)

A local-first password vault I built for myself because I don't trust the cloud.
I got tired of forgetting my Netflix password and I don't trust LastPass after their breaches. 
Also, my Information Security professor said password managers are cool.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    INTERFACES (3 clients)                   │
│  ┌──────────┐  ┌──────────────┐  ┌─────────────────────┐  │
│  │   CLI    │  │  Web (local) │  │   Desktop (PyQt/    │  │
│  │ (Python) │  │  (Flask/JS)  │  │    Tauri wrapper)   │  │
│  └────┬─────┘  └──────┬───────┘  └──────────┬──────────┘  │
│       │               │                     │             │
│       └───────────────┴─────────────────────┘             │
│                         │                                 │
│              ┌──────────▼──────────┐                      │
│              │   Vault Core API    │                      │
│              │   (Python module)   │                      │
│              │  - Crypto engine    │                      │
│              │  - DB abstraction   │                      │
│              │  - Session mgmt     │                      │
│              └──────────┬──────────┘                      │
│                         │                                 │
│              ┌──────────▼──────────┐                      │
│              │   vault.db (SQLite) │                      │
│              │   + salt.bin        │                      │
│              │   + config.json     │                      │
│              └─────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

## Threat Model

This is where I show I actually paid attention in class.

| Threat | Mitigation |
|--------|-----------|
| **Database theft** | AES-256-GCM encryption. Attacker gets gibberish. |
| **Brute force master pw** | Argon2id is memory-hard. Slows GPUs to a crawl. |
| **Swap attacks** (swap two encrypted entries) | Each entry encrypted with unique nonce + associated data |
| **Length leakage** | (TODO: Pad passwords to fixed length) |
| **Memory dump** | Key held in memory only when unlocked. Auto-lock after 5 min. Clear clipboard after 10s. |
| **Rollback attack** | Known limitation (would need an external secure append-only log) |

## Crypto Stack
- **Key Derivation**: Argon2id (64MB, 3 iterations, 4 threads)
- **Encryption**: AES-256-GCM
- **Domain Indexing**: HMAC-SHA256 (Hides which sites you have accounts on if DB is leaked)

## Installation

```bash
# Setup virtual environment
python -m venv venv
# Activate venv on Windows: .\venv\Scripts\activate
# Activate venv on Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
python -m botpass.cli.main  # for CLI
```

## Security Warnings
- If you forget your master password, your data is GONE. No recovery. I'm not magic.
- Back up your `vault.db` and `salt.bin` together. Lose one, lose everything.
- This is a student project. Don't store nuclear launch codes in it.

## TODO (maybe never)
- [ ] Browser extension (lol no)
- [ ] Mobile app (React Native? maybe in 2027)
- [ ] Cloud sync (I don't trust clouds)
- [ ] Web UI (Phase 3)
- [ ] Desktop Wrapper (Phase 4)
