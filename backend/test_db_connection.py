import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import urllib.parse

# Config
HOST = "182.92.74.187"
PORT = 9124
DB = "research"
USER = "llm_dev"
PASS_RAW = "tphy@123"
PASS_ENCODED = urllib.parse.quote_plus(PASS_RAW)

print(f"Raw pass: {PASS_RAW}")
print(f"Encoded pass: {PASS_ENCODED}")

# URL with encoded password
URL_ENCODED = f"postgresql+asyncpg://{USER}:{PASS_ENCODED}@{HOST}:{PORT}/{DB}"
# URL with raw password (for comparison)
URL_RAW = f"postgresql+asyncpg://{USER}:{PASS_RAW}@{HOST}:{PORT}/{DB}"

async def test_encoded():
    print(f"\nTesting Encoded URL: {URL_ENCODED}...")
    try:
        engine = create_async_engine(URL_ENCODED, echo=False)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"✅ Success! Result: {result.scalar()}")
        await engine.dispose()
    except Exception as e:
        print(f"❌ Failed: {e}")

async def main():
    await test_encoded()

if __name__ == "__main__":
    asyncio.run(main())
