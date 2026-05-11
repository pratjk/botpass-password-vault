import os
import hmac
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from argon2.low_level import hash_secret_raw, Type

# Argon2id is memory-hard which means it eats RAM on purpose. Sorry, Chrome.
# We're using 64MB, 3 iterations, 4 parallelism.
def derive_key(master_pw: str, salt: bytes, pepper: bytes) -> bytes:
    """Derive a 32-byte key from the master password."""
    # Combine password and pepper
    secret = master_pw.encode('utf-8')
    
    # Argon2id derivation
    key = hash_secret_raw(
        secret=secret,
        salt=salt,
        time_cost=3,
        memory_cost=65536,  # 64MB
        parallelism=4,
        hash_len=32,
        type=Type.ID
    )
    return key

def encrypt_entry(plaintext: str, key: bytes, associated_data: bytes = b"") -> tuple[bytes, bytes]:
    """Encrypt a string with AES-256-GCM. Returns (ciphertext, nonce)."""
    pt_bytes = plaintext.encode('utf-8')
    
    # Pad plaintext to nearest 128-byte block to prevent length leakage
    # This is important! Ciphertext length == plaintext length in GCM,
    # so without padding an attacker can guess what's stored.
    block_size = 128
    pad_len = block_size - (len(pt_bytes) % block_size)
    # Store the pad length in the last byte so we can strip it later
    pt_bytes = pt_bytes + bytes([pad_len] * pad_len)
    
    # 12 bytes nonce for GCM
    nonce = os.urandom(12)
    
    # Fernet was cute but GCM is where the big kids play
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, pt_bytes, associated_data)
    
    return ciphertext, nonce

def decrypt_entry(ciphertext: bytes, nonce: bytes, key: bytes, associated_data: bytes = b"") -> str:
    """Decrypt AES-256-GCM ciphertext."""
    aesgcm = AESGCM(key)
    # This will raise an exception if authentication fails or it's tampered
    pt_bytes = aesgcm.decrypt(nonce, ciphertext, associated_data)
    
    # Strip the padding we added during encryption
    pad_len = pt_bytes[-1]
    if pad_len > 0 and pad_len <= 128:
        # Verify all padding bytes are the same (like PKCS7)
        if all(b == pad_len for b in pt_bytes[-pad_len:]):
            pt_bytes = pt_bytes[:-pad_len]
    
    return pt_bytes.decode('utf-8')

def hmac_domain(domain: str, key: bytes) -> str:
    """Hash the domain so the DB doesn't leak which sites you use."""
    h = hmac.new(key, domain.lower().encode('utf-8'), hashlib.sha256)
    return h.hexdigest()
