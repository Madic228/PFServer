from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from routers.schemas import UserCreate, Token
from services.auth_service import get_user_by_email, verify_password, get_password_hash, create_user_in_db
from db.database import get_db_connection
from datetime import datetime, timedelta
from jose import jwt, JWTError

router = APIRouter()

# Замените на ваш секретный ключ
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Создает токен доступа с истечением."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db=Depends(get_db_connection)
):
    """Получает текущего пользователя по токену."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_email(email)
    if user is None:
        raise credentials_exception
    return user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db_connection)):
    """Маршрут для входа пользователя."""
    user = get_user_by_email(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user["email"]}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserCreate)
def register(user: UserCreate, db=Depends(get_db_connection)):
    """Регистрация нового пользователя."""
    existing_user = get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already in use",
        )
    if create_user_in_db(user.email, user.password, user.username):  # Добавлен user.username
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

