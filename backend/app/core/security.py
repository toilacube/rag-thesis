import bcrypt

from app.config.config import getConfig

from datetime import datetime, timedelta
from jose import jwt

def create_hashed_password(password: str):
    """
    Hash a password using bcrypt
    """

    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def createAccessToken(data: dict, expires_delta: int = None):
    """
    Create a JWT token
    """
    

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + timedelta(minutes=expires_delta)
    else:
        expire = datetime.now() + timedelta(days=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, getConfig().SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verifyPassword(plain_password: str, hashed_password: str):
    """
    Verify a password against a hashed password
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

