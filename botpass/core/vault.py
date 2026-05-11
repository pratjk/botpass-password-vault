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

    def add(self, domain: str, username: str, password: str):
        if not self.key:
            raise Exception("Vault is locked")

        self._reset_timer()
        domain_h = hmac_domain(domain, self.key)
        ad = b"botpass_entry"
        
        payload = json.dumps({"domain": domain, "username": username, "password": password})
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
