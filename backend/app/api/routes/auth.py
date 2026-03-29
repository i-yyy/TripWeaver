"""Authentication API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ...db.models import User
from ...models.auth_schemas import (
    AuthUserResponse,
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UpdateProfileRequest,
)
from ...services.auth_service import get_auth_service
from ...services.security_service import get_current_user, get_security_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthUserResponse, summary="Register")
async def register(payload: RegisterRequest) -> AuthUserResponse:
    try:
        password_hash = get_security_service().hash_password(payload.password)
        user = get_auth_service().register_user(
            nickname=payload.nickname,
            email=payload.email,
            password_hash=password_hash,
        )
        return AuthUserResponse(success=True, message="Registration succeeded", data=get_auth_service().to_user_data(user))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/login", response_model=LoginResponse, summary="Login")
async def login(payload: LoginRequest) -> LoginResponse:
    user = get_auth_service().get_user_by_email(payload.email)
    if user is None or not get_security_service().verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    refreshed_user = get_auth_service().update_login_time(user.id) or user
    token = get_security_service().create_access_token(
        subject=refreshed_user.id,
        extra_claims={"email": refreshed_user.email or ""},
    )
    return LoginResponse(
        success=True,
        message="Login succeeded",
        access_token=token,
        token_type="bearer",
        data=get_auth_service().to_user_data(refreshed_user),
    )


@router.get("/me", response_model=AuthUserResponse, summary="Current user")
async def get_me(current_user: User = Depends(get_current_user)) -> AuthUserResponse:
    return AuthUserResponse(success=True, message="Current user fetched", data=get_auth_service().to_user_data(current_user))


@router.put("/profile", response_model=AuthUserResponse, summary="Update profile")
async def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
) -> AuthUserResponse:
    try:
        updated_user = get_auth_service().update_profile(current_user.id, payload)
        return AuthUserResponse(success=True, message="Profile updated", data=get_auth_service().to_user_data(updated_user))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/password", response_model=AuthUserResponse, summary="Change password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
) -> AuthUserResponse:
    if not get_security_service().verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be different")

    updated_user = get_auth_service().update_password(
        current_user.id,
        get_security_service().hash_password(payload.new_password),
    )
    return AuthUserResponse(success=True, message="Password updated", data=get_auth_service().to_user_data(updated_user))


@router.delete("/me", response_model=AuthUserResponse, summary="Delete current account")
async def delete_me(current_user: User = Depends(get_current_user)) -> AuthUserResponse:
    get_auth_service().delete_account(current_user.id)
    return AuthUserResponse(success=True, message="Account deleted successfully", data=None)
