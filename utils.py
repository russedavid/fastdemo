import hashlib
import uuid
from datetime import datetime

# Helper functions
def generate_uuid():
    return str(uuid.uuid4())

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash

def get_current_timestamp():
    return datetime.now().isoformat()