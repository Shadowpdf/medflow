import asyncio

from app.database import AsyncSessionLocal
from app.models import User, UserRole
from app.security import hash_password


async def seed_users():
    async with AsyncSessionLocal() as session:
        users = [
            User(
                username="admin",
                hashed_password=hash_password("admin123"),
                role=UserRole.CLINICAL_ADMIN,
            ),
            User(
                username="technician",
                hashed_password=hash_password("tech123"),
                role=UserRole.FIELD_TECHNICIAN,
            ),
            User(
                username="auditor",
                hashed_password=hash_password("audit123"),
                role=UserRole.AUDITOR,
            ),
        ]

        session.add_all(users)
        await session.commit()

        print("Users seeded successfully.")
        


if __name__ == "__main__":
    asyncio.run(seed_users())