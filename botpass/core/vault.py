import sqlite3
import os
import json
import ctypes
from datetime import datetime
from threading import Timer

from .crypto import derive_key, encrypt_entry, decrypt_entry, hmac_domain

_vault_instance = None  # yeah yeah, singleton pattern. sue me.

class Vault:
    def __init__(self, db_path: str, salt_path: str, config_path: str):
        self.db_path = db_path
        self.salt_path = salt_path
        self.config_path = config_path
        
        self.conn = None
        self.key = None
        self.pepper = os.environ.get("BOTPASS_PEPPER", "default_student_pepper").encode('utf-8')
        self._lock_timer = None

    def _init_db(self):
        # I know global variables are bad, but it's fine for a CLI tool
        db = sqlite3.connect(self.db_path, check_same_thread=False)
        db.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain_hmac TEXT NOT NULL UNIQUE,
                data_enc BLOB,
                nonce BLOB,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        db.commit()
        return db

    def setup(self, master_pw: str):
        """First time setup."""
        if os.path.exists(self.db_path) or os.path.exists(self.salt_path):
            raise Exception("Vault already exists!")
            
        # Password complexity validation
        if len(master_pw) < 8:
            raise Exception("Master password must be at least 8 characters long.")
        if not any(char.isdigit() for char in master_pw):
            raise Exception("Master password must contain at least one number.")
        if not any(not char.isalnum() for char in master_pw):
            raise Exception("Master password must contain at least one special character.")

        salt = os.urandom(32)
        with open(self.salt_path, 'wb') as f:
            f.write(salt)

        with open(self.config_path, 'w') as f:
            json.dump({"warning": "Do not lose salt.bin or vault.db"}, f)

        self.key = derive_key(master_pw, salt, self.pepper)
        self.conn = self._init_db()

        # Create verification canary
        self._create_canary()

    def _create_canary(self):
        """Create a verification entry to check passwords without storing hashes."""
        # This is a bit hacky but it works
        payload = json.dumps({"verify": "correct_horse_battery_staple"})
        cipher_data, nonce = encrypt_entry(payload, self.key, b"__verify__")
        
        now = datetime.now().isoformat()
        domain_hmac = hmac_domain("__verify__", self.key)

        self.conn.execute(
            'INSERT INTO entries (domain_hmac, data_enc, nonce, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
            (domain_hmac, cipher_data, nonce, now, now)
        )
        self.conn.commit()

    def unlock(self, master_pw: str) -> bool:
        """Attempt to unlock the vault."""
        if not os.path.exists(self.salt_path) or not os.path.exists(self.db_path):
            raise Exception("Vault not found. Run setup first.")

        with open(self.salt_path, 'rb') as f:
            salt = f.read()

        candidate_key = derive_key(master_pw, salt, self.pepper)
        
        if self.conn is None:
            self.conn = self._init_db()

        # Check canary
        verify_hmac = hmac_domain("__verify__", candidate_key)
        cursor = self.conn.cursor()
        cursor.execute('SELECT data_enc, nonce FROM entries WHERE domain_hmac = ?', (verify_hmac,))
        row = cursor.fetchone()

        if not row:
            return False

        try:
            # Try to decrypt the canary
            decrypted = decrypt_entry(row[0], row[1], candidate_key, b"__verify__")
            data = json.loads(decrypted)
            if data.get("verify") == "correct_horse_battery_staple":
                self.key = candidate_key
                self._reset_timer()
                return True
        except Exception:
            pass

        return False

    def lock(self):
        """Lock the vault and clear memory."""
        # Try to zero out the key buffer
        if self.key:
            # Python's GC makes this imperfect, but it shows we understand memory dumps
            buffer_size = len(self.key)
            offset = id(self.key) + 33 # Approximate offset for bytes object data
            try:
                ctypes.memset(offset, 0, buffer_size)
            except Exception:
                pass
            self.key = None
        
        if self.conn:
            self.conn.close()
            self.conn = None
            
        if self._lock_timer:
            self._lock_timer.cancel()

    def _reset_timer(self):
        """Auto-lock after 5 minutes."""
        if self._lock_timer:
            self._lock_timer.cancel()
        
        # This timer is janky but it works. Don't @ me.
        self._lock_timer = Timer(300.0, self.lock)
        self._lock_timer.daemon = True
        self._lock_timer.start()

    def add(self, domain: str, username: str, password: str, notes: str = ""):
        if not self.key:
            raise Exception("Vault is locked")

        self._reset_timer()
        domain_h = hmac_domain(domain, self.key)
        ad = b"botpass_entry"
        
        payload = json.dumps({"domain": domain, "username": username, "password": password, "notes": notes})
        cipher_data, nonce = encrypt_entry(payload, self.key, ad)
        
        now = datetime.now().isoformat()

        try:
            self.conn.execute(
                'INSERT INTO entries (domain_hmac, data_enc, nonce, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
                (domain_h, cipher_data, nonce, now, now)
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            raise Exception("Domain already exists!")

    def get(self, domain: str) -> dict:
        """Returns the dictionary data for a domain."""
        if not self.key:
            raise Exception("Vault is locked")

        self._reset_timer()
        domain_h = hmac_domain(domain, self.key)
        
        cursor = self.conn.cursor()
        cursor.execute('SELECT data_enc, nonce FROM entries WHERE domain_hmac = ?', (domain_h,))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        ad = b"botpass_entry"
        try:
            decrypted = decrypt_entry(row[0], row[1], self.key, ad)
            return json.loads(decrypted)
        except Exception:
            return None

    def list_entries(self) -> list[dict]:
        """List all entries in the vault."""
        if not self.key:
            raise Exception("Vault is locked")

        self._reset_timer()
        cursor = self.conn.cursor()
        cursor.execute('SELECT domain_hmac, data_enc, nonce FROM entries')
        
        results = []
        for row in cursor.fetchall():
            domain_hmac, data_enc, nonce = row
            if domain_hmac == hmac_domain("__verify__", self.key):
                continue
            
            ad = b"botpass_entry"
            try:
                decrypted = decrypt_entry(data_enc, nonce, self.key, ad)
                results.append(json.loads(decrypted))
            except Exception:
                pass
                
        return results

    def delete(self, domain: str) -> bool:
        """Delete an entry."""
        if not self.key:
            raise Exception("Vault is locked")

        self._reset_timer()
        domain_h = hmac_domain(domain, self.key)
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM entries WHERE domain_hmac = ?', (domain_h,))
        self.conn.commit()
        return cursor.rowcount > 0

    def change_master_password(self, new_pw: str):
        """Re-encrypt the entire vault with a new master password."""
        if not self.key:
            raise Exception("Vault must be unlocked to change password.")

        # Password complexity validation
        if len(new_pw) < 8:
            raise Exception("Master password must be at least 8 characters long.")
        if not any(char.isdigit() for char in new_pw):
            raise Exception("Master password must contain at least one number.")
        if not any(not char.isalnum() for char in new_pw):
            raise Exception("Master password must contain at least one special character.")

        new_salt = os.urandom(32)
        new_key = derive_key(new_pw, new_salt, self.pepper)

        cursor = self.conn.cursor()
        cursor.execute('SELECT domain_hmac, data_enc, nonce FROM entries')
        rows = cursor.fetchall()

        new_entries = []
        old_verify_hmac = hmac_domain("__verify__", self.key)

        for row in rows:
            domain_hmac, data_enc, nonce = row
            if domain_hmac == old_verify_hmac:
                try:
                    decrypted = decrypt_entry(data_enc, nonce, self.key, b"__verify__")
                    new_domain_hmac = hmac_domain("__verify__", new_key)
                    new_cipher, new_nonce = encrypt_entry(decrypted, new_key, b"__verify__")
                    new_entries.append((new_domain_hmac, new_cipher, new_nonce, domain_hmac))
                except Exception:
                    raise Exception("Failed to decrypt canary during re-keying.")
            else:
                try:
                    decrypted = decrypt_entry(data_enc, nonce, self.key, b"botpass_entry")
                    payload = json.loads(decrypted)
                    domain = payload.get("domain")
                    
                    new_domain_hmac = hmac_domain(domain, new_key)
                    new_cipher, new_nonce = encrypt_entry(decrypted, new_key, b"botpass_entry")
                    new_entries.append((new_domain_hmac, new_cipher, new_nonce, domain_hmac))
                except Exception:
                    pass

        try:
            for new_h, new_c, new_n, old_h in new_entries:
                self.conn.execute('''
                    UPDATE entries 
                    SET domain_hmac = ?, data_enc = ?, nonce = ?, updated_at = ?
                    WHERE domain_hmac = ?
                ''', (new_h, new_c, new_n, datetime.now().isoformat(), old_h))
            
            with open(self.salt_path, 'wb') as f:
                f.write(new_salt)
                
            self.conn.commit()
            self.key = new_key
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Failed to change password: {e}")

    def update_entry(self, domain: str, new_username: str = None, new_password: str = None, new_notes: str = None):
        """Update an existing entry's username, password, and/or notes."""
        if not self.key:
            raise Exception("Vault is locked")

        self._reset_timer()
        data = self.get(domain)
        if not data:
            raise Exception("Entry not found.")

        # Update whatever was provided
        if new_username is not None:
            data["username"] = new_username
        if new_password is not None:
            data["password"] = new_password
        if new_notes is not None:
            data["notes"] = new_notes

        domain_h = hmac_domain(domain, self.key)
        ad = b"botpass_entry"
        payload = json.dumps(data)
        cipher_data, nonce = encrypt_entry(payload, self.key, ad)
        now = datetime.now().isoformat()

        self.conn.execute('''
            UPDATE entries SET data_enc = ?, nonce = ?, updated_at = ?
            WHERE domain_hmac = ?
        ''', (cipher_data, nonce, now, domain_h))
        self.conn.commit()

    def export_backup(self, filepath: str):
        """Export the vault to an encrypted JSON backup file."""
        if not self.key:
            raise Exception("Vault is locked")

        self._reset_timer()
        entries = self.list_entries()
        
        # We'll encrypt the entire JSON blob with our current key
        backup_data = json.dumps({
            "version": "botpass-backup-v1",
            "exported_at": datetime.now().isoformat(),
            "entries": entries
        })
        
        ad = b"botpass_backup"
        cipher_data, nonce = encrypt_entry(backup_data, self.key, ad)
        
        # Write as a simple binary format: nonce_len(1 byte) + nonce + ciphertext
        with open(filepath, 'wb') as f:
            f.write(bytes([len(nonce)]))
            f.write(nonce)
            f.write(cipher_data)

    def import_backup(self, filepath: str):
        """Import entries from an encrypted backup file."""
        if not self.key:
            raise Exception("Vault is locked")

        self._reset_timer()
        
        with open(filepath, 'rb') as f:
            nonce_len = f.read(1)[0]
            nonce = f.read(nonce_len)
            cipher_data = f.read()
        
        ad = b"botpass_backup"
        try:
            decrypted = decrypt_entry(cipher_data, nonce, self.key, ad)
            backup = json.loads(decrypted)
        except Exception:
            raise Exception("Failed to decrypt backup. Wrong master password or corrupted file.")
        
        if backup.get("version") != "botpass-backup-v1":
            raise Exception("Unknown backup format.")
        
        imported = 0
        skipped = 0
        for entry in backup.get("entries", []):
            domain = entry.get("domain")
            username = entry.get("username", "")
            password = entry.get("password", "")
            notes = entry.get("notes", "")
            
            try:
                self.add(domain, username, password, notes)
                imported += 1
            except Exception:
                # Domain probably already exists, skip
                skipped += 1
        
        return {"imported": imported, "skipped": skipped}

