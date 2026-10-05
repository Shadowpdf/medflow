import os

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker 

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:Jucaro1737@localhost:5432/medflow")

engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)