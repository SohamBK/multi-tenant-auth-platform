from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher(
    time_cost=3,      # Number of iterations
    memory_cost=65536, # 64MiB of RAM
    parallelism=4,    # Number of parallel threads
    hash_len=32,      # Length of the resulting hash
    salt_len=16       # Length of the random salt
)

def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using Argon2id.
    Includes an automatic random salt.
    """
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a password against its Argon2id hash.
    Protects against timing attacks.
    """
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False