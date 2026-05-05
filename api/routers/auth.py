from fastapi import APIRouter, status

from ..schemas import AuthResponse, LoginRequest, RegisterRequest
from ..services import login_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest) -> AuthResponse:
    user = register_user(payload)
    return AuthResponse(message="User registered successfully.", user=user)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    user = login_user(payload)
    return AuthResponse(message="Login successful.", user=user)
