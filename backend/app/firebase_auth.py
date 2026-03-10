import json
import logging
import os

import firebase_admin

from firebase_admin import credentials, auth
from fastapi import HTTPException

logger = logging.getLogger(__name__)


_firebase_initialized = False 

def initialize_firebase() -> None:
    """
    Initializes the Firebase Admin SDK ONCE using credentials from a JSON file.
    """
    global _firebase_initialized

    if _firebase_initialized:
        return  # Already initialized
    
    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

    # Validate the presence and correctness of the service account JSON
    if service_account_json:
        try:
            credential_data = json.loads(service_account_json)
            cred = credentials.Certificate(credential_data)
        except Exception as e:
            raise ValueError(f"Invalid FIREBASE_SERVICE_ACCOUNT_JSON: {e}")
    else:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON environment variable is not set")
    
    # Initialize the Firebase Admin SDK with the provided credentials
    firebase_admin.initialize_app(cred)
    _firebase_initialized = True


def verify_firebase_token(token: str) -> dict:
    """
    Verifies the provided Firebase ID token and returns the decoded token claims.
    Raises an HTTPException if the token is invalid or verification fails.
    """
    if not token:
        raise HTTPException(status_code=400, detail="Firebase token is required")
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        logger.warning("Firebase token verification failed: %s", e)
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token")