from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    verify_password, hash_password, create_access_token, create_refresh_token, decode_token,
    generate_totp_secret, get_totp_uri, generate_qr_code_base64, verify_totp,
)
from app.core.redis_client import blacklist_token, cache_set, cache_get
from app.core.config import settings
from app.middleware.audit_logger import log_action
from app.models.user import User
from app.schemas.auth import (
    LoginRequest, MFAVerifyRequest, TokenResponse, MFASetupResponse,
    MFAEnableRequest, RefreshRequest, PasswordChangeRequest,
    ForgotPasswordRequest, ResetPasswordRequest,
)
from app.middleware.auth import get_current_user
from app.services.email_service import send_password_reset_email
import uuid

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        await log_action(db, "LOGIN_FAILED", ip_address=request.client.host, extra_data={"email": body.email}, result="FAILURE")
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants incorrects")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte désactivé")

    if user.mfa_enabled:
        temp_token = str(uuid.uuid4())
        await cache_set(f"mfa_temp:{temp_token}", str(user.id), ttl=300)
        await log_action(db, "LOGIN_MFA_REQUIRED", user=user, ip_address=request.client.host)
        await db.commit()
        return TokenResponse(requires_mfa=True, temp_token=temp_token)

    access_token = create_access_token({"sub": str(user.id), "tenant": str(user.tenant_id), "role": user.role.value})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    await log_action(db, "LOGIN_SUCCESS", user=user, ip_address=request.client.host)
    await db.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/mfa/verify", response_model=TokenResponse)
async def verify_mfa(
    body: MFAVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_id = await cache_get(f"mfa_temp:{body.temp_token}")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token temporaire invalide ou expiré")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or user.email != body.email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur non trouvé")

    if not verify_totp(user.mfa_secret, body.totp_code):
        await log_action(db, "MFA_FAILED", user=user, ip_address=request.client.host, result="FAILURE")
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Code MFA incorrect")

    access_token = create_access_token({"sub": str(user.id), "tenant": str(user.tenant_id), "role": user.role.value})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    await log_action(db, "MFA_SUCCESS", user=user, ip_address=request.client.host)
    await db.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(current_user: User = Depends(get_current_user)):
    secret = generate_totp_secret()
    uri = get_totp_uri(secret, current_user.email)
    qr = generate_qr_code_base64(uri)
    return MFASetupResponse(secret=secret, qr_code_base64=qr, totp_uri=uri)


@router.post("/mfa/enable")
async def enable_mfa(
    body: MFAEnableRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Le secret doit avoir été communiqué via /mfa/setup — vérifier le code
    setup = await cache_get(f"mfa_setup:{current_user.id}")
    if not setup:
        raise HTTPException(status_code=400, detail="Lancez d'abord GET /auth/mfa/setup")

    if not verify_totp(setup, body.totp_code):
        raise HTTPException(status_code=400, detail="Code TOTP invalide")

    current_user.mfa_secret = setup
    current_user.mfa_enabled = True
    await log_action(db, "MFA_ENABLED", user=current_user)
    await db.commit()
    return {"message": "MFA activé avec succès"}


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await log_action(db, "LOGOUT", user=current_user)
    await db.commit()
    return {"message": "Déconnexion réussie"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalide")

    result = await db.execute(select(User).where(User.id == uuid.UUID(payload["sub"])))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur inactif")

    access_token = create_access_token({"sub": str(user.id), "tenant": str(user.tenant_id), "role": user.role.value})
    return TokenResponse(access_token=access_token, refresh_token=body.refresh_token)


@router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Initie la réinitialisation de mot de passe.
    Toujours renvoyer 200 pour ne pas divulguer si l'email existe.
    """
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user and user.is_active:
        reset_token = str(uuid.uuid4())
        ttl = settings.RESET_TOKEN_EXPIRE_MINUTES * 60
        await cache_set(f"reset_pwd:{reset_token}", str(user.id), ttl=ttl)
        await send_password_reset_email(user.email, user.full_name, reset_token)
        await log_action(
            db, "PASSWORD_RESET_REQUESTED",
            user=user,
            ip_address=request.client.host,
        )
        await db.commit()

    return {"message": "Si votre adresse email est connue, vous recevrez un lien de réinitialisation."}


@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_id = await cache_get(f"reset_pwd:{body.token}")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lien invalide ou expiré")

    if len(body.new_password) < 8:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Le mot de passe doit contenir au moins 8 caractères")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Utilisateur introuvable")

    user.hashed_password = hash_password(body.new_password)
    await log_action(db, "PASSWORD_RESET_COMPLETED", user=user, ip_address=request.client.host)
    await db.commit()

    # Invalider le token après usage
    await cache_set(f"reset_pwd:{body.token}", "", ttl=1)

    return {"message": "Mot de passe réinitialisé avec succès. Vous pouvez maintenant vous connecter."}
