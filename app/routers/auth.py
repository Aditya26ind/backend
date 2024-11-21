from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from fastapi import Cookie, Depends, HTTPException, Response, status,APIRouter
from app import schemas
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
import os
from app.schemas import Token, TokenData,UserCreate


router = APIRouter(prefix="/auth", tags=["Authentication"])


SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # Set to 24 hours or adjust as needed

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if the username is already taken
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Hash the password
    hashed_password = pwd_context.hash(user.password)

    # Create and save the new user
    new_user = User(
        username=user.username,
        password=hashed_password,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully", "id": new_user.id}

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(access_token: str = Cookie(None), db: Session = Depends(get_db)):
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing"
        )
    
    # Remove 'Bearer ' prefix if present
    if access_token.startswith("Bearer "):
        access_token = access_token.split(" ")[1]

    try:
        # Decode the token
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload invalid"
            )
        token_data = TokenData(username=username)
    except JWTError as e:
        print(f"JWT decoding error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not verify credentials"
        )
    
    # Query the database to verify the user exists
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

@router.post("/login", response_model=Token)
def login(response: Response, user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not pwd_context.verify(user.password, db_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": db_user.username})
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True, 
        max_age=60 * 60 * 24,
        secure=False,
        samesite="none"
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
def get_user_details(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "id": current_user.id}


@router.get("/check-auth")
def check_auth(access_token: str = Cookie(None), db: Session = Depends(get_db)):
    print(f"Received access_token: {access_token}")  # Log the cookie

    if not access_token:
        print("No access token provided")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = access_token.split(" ")[1]  # Remove "Bearer" prefix
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"Decoded payload: {payload}")  # Log payload

        username = payload.get("sub")
        if not username:
            print("Invalid token payload")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        user = db.query(User).filter(User.username == username).first()
        if not user:
            print("User not found in database")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    except JWTError as e:
        print(f"JWT decoding error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return {"username": user.username, "id": user.id, "authenticated": True}


@router.post("/logout")
def logout(response: Response):
    # Clear the access token cookie
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}