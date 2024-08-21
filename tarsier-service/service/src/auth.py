import os
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from propelauth_fastapi import init_auth, User
from dotenv import load_dotenv


load_dotenv() 
auth = init_auth("https://6966894145.propelauthtest.com", os.environ["PROPEL_AUTH_API_KEY"])
security = HTTPBearer()

def validate_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        user: User = auth.validate_api_key(credentials.credentials)
        return user
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
