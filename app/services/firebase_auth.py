import firebase_admin
from firebase_admin import credentials, auth
from app.core.config import settings
from fastapi import HTTPException

# Initialize Firebase Admin SDK
cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
firebase_admin.initialize_app(cred)


def verify_firebase_token(id_token: str) -> dict:
    """Verify Firebase ID token and return decoded claims."""
    try:
        decoded = auth.verify_id_token(id_token)
        return {
            "uid": decoded["uid"],
            "email": decoded.get("email", ""),
            "name": decoded.get("name", ""),
            "email_verified": decoded.get("email_verified", False)
        }
    except auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Token expired. Please login again.")
    except auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


def create_firebase_user(email: str, password: str, display_name: str = "") -> dict:
    """Create a new Firebase user."""
    try:
        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name
        )
        return {"uid": user.uid, "email": user.email}
    except auth.EmailAlreadyExistsError:
        raise HTTPException(status_code=400, detail="Email already registered.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"User creation failed: {str(e)}")


def get_firebase_user(uid: str) -> dict:
    """Get Firebase user by UID."""
    try:
        user = auth.get_user(uid)
        return {"uid": user.uid, "email": user.email, "name": user.display_name}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"User not found: {str(e)}")