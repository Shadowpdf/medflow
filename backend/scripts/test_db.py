import asyncio

from sqlalchemy import text, select

from app.database import AsyncSessionLocal



async def test_database():
    async with AsyncSessionLocal() as session:
       test_stmt = select(text("1"))
       
       result = await session.execute(test_stmt)

       for result in result.scalars():
            print(f"Test-Output: {result!r}")


if __name__ == "__main__":
    asyncio.run(test_database())
