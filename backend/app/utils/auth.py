from datetime import datetime, timedelta
import hashlib
from typing import Optional
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models import User
from backend.app.utils.logger import logger

# OAuth2 Password Bearer (retrieves the token from Authorization header)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

def _pre_hash_password(password: str) -> str:
    """
    Pre-hashes a password using SHA-256 to circumvent bcrypt's 72-byte limitation
    and mitigate potential Denial of Service (DoS) attacks on bcrypt calculations.
    Returns the hexadecimal string digest of the hash.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if a plain-text password (after SHA-256 pre-hashing) matches the stored bcrypt hash.
    """
    try:
        pre_hashed = _pre_hash_password(plain_password)
        # Verify using standard bcrypt checkpw
        return bcrypt.checkpw(
            pre_hashed.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False

def get_password_hash(password: str) -> str:
    """
    Generates a secure bcrypt hash of a pre-hashed password.
    """
    pre_hashed = _pre_hash_password(password)
    # Generate salt and hash using standard bcrypt
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pre_hashed.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generates a signed JWT access token containing the provided data payload.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.secret_key, 
            algorithm=settings.algorithm
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Failed to generate JWT token: {e}")
        raise RuntimeError("Token generation failed.")

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency that extracts the JWT token from headers,
    decodes it, and retrieves the authenticated User from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the token payload
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError as e:
        logger.warning(f"JWT Decode error: {e}")
        raise credentials_exception
        
    # Query database for user
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        logger.warning(f"User not found for token email: {email}")
        raise credentials_exception
        
    return user
