from exceptiongroup import catch
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session 

from app.dtos.authDTO import LoginResponse, LoginRequest
from app.services.permission import PermissionService, getPermissionService
from db.database import get_db_session
from app.core import security
from app.core.api_reponse import api_response
from app.dtos.userDTO import UserCreate, UserResponse
from app.models.models import User


router = APIRouter()

@router.post("/login", response_model=LoginResponse)
async def login(*, db: Session = Depends(get_db_session), permissionService: PermissionService = Depends(getPermissionService), login: LoginRequest):
    # Check if the user exists
    user = db.query(User).filter(User.email == login.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    # Verify the password
    if not security.verifyPassword(login.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    # Get user scopes
    scopes = permissionService.getUserScopes(user.id)

    # Generate a JWT token
    access_token = security.createAccessToken(data={"sub": user.email, "scopes": scopes})

    # Create response with token in body
    response_data = {
        "access_token": access_token
    }
    
    # Create JSON response and set HTTP cookie
    response = JSONResponse(content=response_data)
    response.set_cookie(
        key=security.ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        max_age=30 * 24 * 60 * 60,  # 30 days in seconds
        httponly=True,  # Security: prevent JavaScript access
        secure=False,  # Set to True in production with HTTPS
        samesite="lax"  # CSRF protection
    )
    
    return response

@router.get("/logout")
async def logout():
    # Clear the cookie on logout
    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie(key=security.ACCESS_TOKEN_COOKIE_NAME)
    return response

@router.post("/register", response_model=UserResponse)
async def register(*,  db: Session = Depends(get_db_session), userCreate: UserCreate):

    # Check if the user already exists
    existing_user = db.query(User).filter(User.email == userCreate.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    # Create a new user
    new_user = User(
        email=userCreate.email,
        username=userCreate.username,
        hashed_password=security.create_hashed_password(userCreate.password),  # Ensure to hash the password in a real application
        is_active=True,
        is_superuser=False,
    )

    # Add the new user to the database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user
    
@router.get("/me", response_model=UserResponse)
def get_current_user(
    current_user: User = Depends(security.get_current_user)
):
    if current_user.is_active:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
    )