from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class MFAVerifyRequest(BaseModel):
    email: EmailStr
    totp_code: str
    temp_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    requires_mfa: bool = False
    temp_token: Optional[str] = None


class MFASetupResponse(BaseModel):
    secret: str
    qr_code_base64: str
    totp_uri: str


class MFAEnableRequest(BaseModel):
    totp_code: str


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
