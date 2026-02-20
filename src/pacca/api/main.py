# 1. Standard Python tools
from datetime import datetime, timedelta

# 2. Third-party libraries
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from jose import jwt # We use 'jose' here to perfectly match what we used in auth.py

# 3. Your local project files
from .database import SessionLocal, engine, Base
from .models import User
from .routes import authorizations, admin
from .auth import verify_password, get_password_hash, verify_token, SECRET_KEY, ALGORITHM

app = FastAPI(title="PACCA Level 5")

# This line looks at models.py and actually creates the pacca.db file and the users table!
Base.metadata.create_all(bind=engine)

# This is a "Dependency". It opens a database session for a request, and closes it when done.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ALLOW THE FRONTEND TO TALK TO THE BACKEND
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (good for local demo)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserCreate(BaseModel):
    username: str
    password: str

@app.post("/api/v1/register/")
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # 1. Check if the username already exists in the database
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # 2. Scramble the password
    hashed_password = get_password_hash(user.password)
    
    # 3. Create the new User object
    new_user = User(username=user.username, hashed_password=hashed_password)
    
    # 4. Save it to the database!
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User created successfully! You can now log in."}

app.include_router(
    authorizations.router, 
    prefix="/api/v1/authorizations",
    dependencies=[Depends(verify_token)] # <-- This locks the door
)
app.include_router(admin.router, prefix="/api/v1/admin")

# 1. Define the format we expect from the React frontend
class LoginRequest(BaseModel):
    username: str
    password: str

# 2. Create the endpoint to generate the token
@app.post("/api/v1/login/")
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    # 1. Look up the user in the database by their username
    user = db.query(User).filter(User.username == credentials.username).first()
    
    # 2. If the user doesn't exist, OR the password doesn't match the scrambled one, kick them out
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect username or password"
        )
    
    # 3. If they passed the check, build the token just like before!
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode = {"sub": user.username, "exp": expire}
    access_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return {"access_token": access_token, "token_type": "bearer"}

    
@app.get("/health")
async def health(): return {"status": "ok"}
