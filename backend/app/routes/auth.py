from fastapi import APIRouter, HTTPException, status, Depends

from app.core.security import create_access_token, get_current_user_id
from app.models.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    LoginResponse,
    SignupResponse,
)
from app.services.user_service import (
    get_user_by_email,
    get_user_by_username,
    get_user_by_id,
    create_user,
    authenticate_user,
    user_doc_to_response,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate):
    """
    Register a new user.
    
    **How it works:**
    1. Check if email already exists
    2. Check if username already exists
    3. Hash the password (using bcrypt)
    4. Store user in MongoDB
    5. Return success message
    
    **Password Storage:**
    - We NEVER store the plain password
    - We hash it using bcrypt (one-way encryption)
    - Even if database is hacked, passwords are safe
    """
    # Check if email already registered
    existing_email = await get_user_by_email(user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already taken
    existing_username = await get_user_by_username(user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create the user (password gets hashed in create_user)
    user_doc = await create_user(user_data)
    user_response = user_doc_to_response(user_doc)
    
    return SignupResponse(
        message="Account created successfully! You can now log in.",
        user=user_response
    )


@router.post("/login", response_model=LoginResponse)
async def login(credentials: UserLogin):
    """
    Authenticate user and return JWT token.
    
    **How password verification works:**
    1. User sends email + plain password
    2. We find the user by email
    3. We get their hashed password from database
    4. We hash the input password with the same salt
    5. We compare the two hashes
    6. If they match -> password is correct!
    
    **Why this is secure:**
    - Plain password is never stored
    - Even we don't know user's password
    - bcrypt is slow by design (prevents brute force)
    - Each password has unique salt (prevents rainbow tables)
    """
    # Authenticate user (check password)
    user = await authenticate_user(credentials.email, credentials.password)
    
    if not user:
        # Don't reveal if email exists or password is wrong
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create JWT token
    # The token contains user ID, signed with our secret key
    access_token = create_access_token(data={"sub": str(user["_id"])})
    
    # Return token and user info
    user_response = user_doc_to_response(user)
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(user_id: str = Depends(get_current_user_id)):
    """
    Get current authenticated user's profile.
    
    **How authentication works:**
    1. Client sends JWT token in Authorization header
    2. We decode and verify the token
    3. Extract user ID from token
    4. Fetch user from database
    5. Return user info
    
    The token is signed with our SECRET_KEY, so:
    - Nobody can forge a token without the key
    - We can trust the user ID in the token
    """
    user = await get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user_doc_to_response(user)


@router.post("/verify-token")
async def verify_token(user_id: str = Depends(get_current_user_id)):
    """
    Verify if a JWT token is valid.
    
    Returns user ID if valid, 401 if invalid/expired.
    """
    return {"valid": True, "user_id": user_id}
