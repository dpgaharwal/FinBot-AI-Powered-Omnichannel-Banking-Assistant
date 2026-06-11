import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.firebase_auth import verify_firebase_token, create_firebase_user
from app.middleware.auth import create_access_token
from app.core.config import settings

router = APIRouter()


class SignUpRequest(BaseModel):
    email: str
    password: str
    display_name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class FirebaseTokenRequest(BaseModel):
    firebase_token: str


@router.post("/auth/signup")
async def signup(request: SignUpRequest):
    """Create Firebase user + return FinBot JWT."""
    user = create_firebase_user(
        email=request.email,
        password=request.password,
        display_name=request.display_name
    )
    token = create_access_token(data={
        "sub": user["email"],
        "uid": user["uid"],
        "customer_id": None
    })
    return {"access_token": token, "token_type": "bearer", "uid": user["uid"]}


@router.post("/auth/login")
async def login(request: LoginRequest):
    """Sign in with Firebase REST API → return FinBot JWT."""
    firebase_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={settings.FIREBASE_WEB_API_KEY}"

    async with httpx.AsyncClient() as client:
        response = await client.post(firebase_url, json={
            "email": request.email,
            "password": request.password,
            "returnSecureToken": True
        })

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    data = response.json()
    firebase_token = data["idToken"]
    user_claims = verify_firebase_token(firebase_token)

    token = create_access_token(data={
        "sub": user_claims["email"],
        "uid": user_claims["uid"],
        "customer_id": None
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "uid": user_claims["uid"],
        "email": user_claims["email"],
        "name": user_claims.get("name", "")
    }


@router.post("/auth/verify")
async def verify_token_endpoint(request: FirebaseTokenRequest):
    """Verify a Firebase ID token directly."""
    user_claims = verify_firebase_token(request.firebase_token)
    token = create_access_token(data={
        "sub": user_claims["email"],
        "uid": user_claims["uid"],
        "customer_id": None
    })
    return {"access_token": token, "token_type": "bearer"}