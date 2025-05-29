import bcrypt

from app.config.config import getConfig

from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
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
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db_session)):
    """
    Verify JWT token and return the current user
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: If token is invalid or user doesn't exist
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, getConfig().SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        
        if email is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
        
    # Get user from database
    user = db.query(User).filter(User.email == email).first()
    
    if user is None:
        raise credentials_exception
        
    return user

