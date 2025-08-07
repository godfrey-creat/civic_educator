from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.database import DatabaseManager, Base
from app.models import User
from pydantic import BaseModel, EmailStr
from app.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix="/auth", tags=["auth"])

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""

class UserLogin(BaseModel):
    email: EmailStr
    password: str

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"msg": "User registered successfully", "user_id": str(db_user.id)}

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # For demo: return user info. In production, return a JWT token.
    return {"msg": "Login successful", "user_id": str(db_user.id)}

class AuthManager:
    @staticmethod
    def authenticate(email: str, password: str, db: Session):
        user = db.query(User).filter(User.email == email).first()
        if user and verify_password(password, user.hashed_password):
            return user
        return None

    @staticmethod
    def get_user_by_email(email: str, db: Session):
        return db.query(User).filter(User.email == email).first()
