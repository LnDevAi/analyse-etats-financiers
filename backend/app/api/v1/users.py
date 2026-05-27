from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_db
from app.core.security import hash_password, ROLES
from app.middleware.auth import get_current_user
from app.middleware.audit_logger import log_action
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["Utilisateurs"])


@router.post("/", response_model=UserOut)
async def create_user(
    body: UserCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if ROLES.get(current_user.role.value, 0) < ROLES.get(UserRole.CHEF_MISSION.value, 0):
        raise HTTPException(status_code=403, detail="Rôle Chef de mission requis pour créer un utilisateur")

    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    user = User(
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        role=body.role,
        tenant_id=current_user.tenant_id,
    )
    db.add(user)
    await log_action(db, "USER_CREATE", user=current_user, resource_type="User", resource_id=body.email)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/", response_model=list[UserOut])
async def list_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if ROLES.get(current_user.role.value, 0) < ROLES.get(UserRole.CHEF_MISSION.value, 0):
        raise HTTPException(status_code=403, detail="Accès réservé au Chef de mission et Associé")

    result = await db.execute(
        select(User).where(User.tenant_id == current_user.tenant_id)
    )
    return result.scalars().all()


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if ROLES.get(current_user.role.value, 0) < ROLES.get(UserRole.ASSOCIE.value, 0):
        raise HTTPException(status_code=403, detail="Rôle Associé requis")

    result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == current_user.tenant_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    if body.full_name is not None:
        user.full_name = body.full_name
    if body.role is not None:
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active

    await log_action(db, "USER_UPDATE", user=current_user, resource_type="User", resource_id=str(user_id))
    await db.commit()
    await db.refresh(user)
    return user
