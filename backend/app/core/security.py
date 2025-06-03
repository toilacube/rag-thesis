import bcrypt

from app.config.config import getConfig

from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer # Keep for login endpoint if still used there, or remove if not
from sqlalchemy.orm import Session

from db.database import get_db_session
from app.models.models import User

def create_hashed_password(password: str):
    """
    Hash a password using bcrypt
    """
    '''
 Postgres as my DDBB and his driver, or the DDBB system, encode always an already encoded string
 '''
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') # decode the hash to prevent is encoded twice


def createAccessToken(data: dict, expires_delta: int = None):
    """
    Create a JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + timedelta(days=expires_delta)
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

# Set up OAuth2 with Bearer token for JWT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False) # auto_error=False to allow fallback

ACCESS_TOKEN_COOKIE_NAME = "access_token"

def get_current_user(
    token_from_header: str = Depends(oauth2_scheme),
    access_token_cookie: str = Cookie(None, alias=ACCESS_TOKEN_COOKIE_NAME),
    db: Session = Depends(get_db_session)
):
    """
    Verify JWT token and return the current user.
    Checks Authorization header first, then falls back to HTTP cookie.
    
    Args:
        token_from_header: JWT token from Authorization header (optional)
        access_token_cookie: JWT token from HTTP cookie (optional)
        db: Database session
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: If token is invalid or user doesn't exist from either source
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}, # Keep Bearer for header-based auth
    )

    token = None
    if token_from_header:
        token = token_from_header
    elif access_token_cookie:
        token = access_token_cookie
    else:
        # No token provided in header or cookie
        raise credentials_exception

    try:
        # Decode JWT token
        payload = jwt.decode(token, getConfig().SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        
        if email is None:
            raise credentials_exception # Missing 'sub' claim
            
    except JWTError: # Covers expired tokens, invalid signature, etc.
        raise credentials_exception
        
    # Get user from database
    user = db.query(User).filter(User.email == email).first()
    
    if user is None:
        # User from token not found in DB
        raise credentials_exception
        
    return user

