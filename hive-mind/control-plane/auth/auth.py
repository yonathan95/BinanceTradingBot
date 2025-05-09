from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db.database import get_db
from models.database import User, Agent

# Secret key for JWT token generation
# In production, this should be a secure secret key stored in environment variables
SECRET_KEY = "REPLACE_WITH_SECURE_SECRET_KEY_FROM_ENV_VARIABLE"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    """Authenticate a user with username and password"""
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    user = result.scalars().first()
    
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    
    return user


async def authenticate_agent(db: AsyncSession, agent_id: str, api_key: str) -> Optional[Agent]:
    """Authenticate an agent with agent_id and API key"""
    query = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(query)
    agent = result.scalars().first()
    
    if not agent:
        return None
    # In a real implementation, you would verify the API key securely
    # This is a placeholder for demonstration
    # if not secure_compare(api_key, agent.api_key_hash):
    #     return None
    
    return agent


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        # Check if token is for a user or agent
        user_type = payload.get("user_type", "human")
        
        if user_type == "human":
            query = select(User).where(User.username == username)
            result = await db.execute(query)
            user = result.scalars().first()
            if user is None:
                raise credentials_exception
            
            # Update last login time
            user.last_login = datetime.utcnow()
            await db.commit()
            
            return user
        else:
            # For agent authentication
            query = select(Agent).where(Agent.id == username)
            result = await db.execute(query)
            agent = result.scalars().first()
            if agent is None:
                raise credentials_exception
            
            # Return the agent as authenticated entity
            return agent
            
    except JWTError:
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Check if the current user is active"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user 