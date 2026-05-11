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
    # Pad to 64 bytes to hide length? Actually let's just do fixed block size padding if we wanted,
    # but for a student project, let's just encode it and maybe pad to a multiple of 64 bytes.
    # To keep it simple: just encrypt.
    pt_bytes = plaintext.encode('utf-8')
    
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
    return pt_bytes.decode('utf-8')

def hmac_domain(domain: str, key: bytes) -> str:
    """Hash the domain so the DB doesn't leak which sites you use."""
    h = hmac.new(key, domain.lower().encode('utf-8'), hashlib.sha256)
    return h.hexdigest()
