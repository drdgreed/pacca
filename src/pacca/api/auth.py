import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError 

# 1. The Keys for the Bouncer
SECRET_KEY = "your-super-secret-development-key" 
ALGORITHM = "HS256"

# This tells FastAPI where our login route is
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login/")

# 2. Pure bcrypt hashing (No passlib bug!)
def get_password_hash(password: str) -> str:
    # bcrypt requires text to be converted to bytes first
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8') # Convert back to string for the database

def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')
    try:
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except ValueError:
        return False

# 3. The Original Bouncer
def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    except Exception: 
        raise HTTPException(status_code=401, detail="Could not validate credentials")