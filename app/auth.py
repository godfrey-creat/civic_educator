from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt

from app.models import User
from app.database import get_db

# JWT config
SECRET_KEY = "change_this_to_a_strong_secret"  # Change in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix="/api/auth", tags=["auth"])

# ----------------------------
# Schemas
# ----------------------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""
    is_staff: bool = False

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    is_staff: bool

# ----------------------------
# Helpers
# ----------------------------
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# ----------------------------
# Endpoints
# ----------------------------
@router.post("/register", response_model=TokenResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
        is_staff=user.is_staff
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    token_data = {"sub": str(db_user.id), "is_staff": db_user.is_staff}
    access_token = create_access_token(token_data)
    return TokenResponse(access_token=access_token, token_type="bearer", is_staff=db_user.is_staff)

@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token_data = {"sub": str(db_user.id), "is_staff": db_user.is_staff}
    access_token = create_access_token(token_data)
    return TokenResponse(access_token=access_token, token_type="bearer", is_staff=db_user.is_staff)