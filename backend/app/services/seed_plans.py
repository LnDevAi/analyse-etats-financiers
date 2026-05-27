"""
Initialise les plans d'abonnement par défaut en base.
À exécuter une fois après la migration 005.

    python -m app.services.seed_plans
"""
import asyncio
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.billing import SubscriptionPlan

PLANS = [
    {
        "name": "STARTER",
        "display_name": "Starter",
        "price_monthly": Decimal("25000"),
        "price_yearly": Decimal("255000"),   # 15% remise
        "max_analyses": 10,
        "max_users": 3,
        "max_documents": 50,
        "trial_days": 14,
        "sort_order": 1,
        "features": [
            "Analyses FEC complètes",
            "Loi de Benford",
            "Cohérence SYSCOHADA",
            "Export PDF & Excel",
        ],
    },
    {
        "name": "PRO",
        "display_name": "Pro",
        "price_monthly": Decimal("75000"),
        "price_yearly": Decimal("765000"),
        "max_analyses": 50,
        "max_users": 10,
        "max_documents": 500,
        "trial_days": 14,
        "sort_order": 2,
        "features": [
            "Tout Starter",
            "Revue analytique N vs N-1",
            "Cross-checking multi-entités",
            "Analyse AG (budget, marchés, bilan social)",
            "Balance générale — réconciliation",
            "Support prioritaire",
        ],
    },
    {
        "name": "ENTERPRISE",
        "display_name": "Enterprise",
        "price_monthly": Decimal("0"),       # sur devis
        "price_yearly": Decimal("0"),
        "max_analyses": None,                 # illimité
        "max_users": None,
        "max_documents": None,
        "trial_days": 30,
        "sort_order": 3,
        "features": [
            "Tout Pro",
            "Analyses illimitées",
            "Utilisateurs illimités",
            "Déploiement on-premise disponible",
            "Intégration API personnalisée",
            "Account manager dédié",
            "SLA 99,9%",
        ],
    },
]


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        for plan_data in PLANS:
            existing = await db.execute(
                select(SubscriptionPlan).where(SubscriptionPlan.name == plan_data["name"])
            )
            if existing.scalar_one_or_none():
                print(f"  Plan {plan_data['name']} déjà présent — ignoré.")
                continue

            plan = SubscriptionPlan(**plan_data)
            db.add(plan)
            print(f"  Plan {plan_data['name']} créé.")

        await db.commit()
    print("Seed terminé.")


if __name__ == "__main__":
    asyncio.run(seed())
