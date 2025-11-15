"""Check database indexes."""
import asyncio
from sqlalchemy import text
from app.infrastructure.database.session import engine


async def check_indexes():
    """Check composite indexes on designs table."""
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'designs' 
            AND indexname LIKE 'ix_designs_%'
            ORDER BY indexname
        """))
        
        print('\n📊 COMPOSITE INDEXES ON designs:')
        indexes = result.fetchall()
        
        if not indexes:
            print('  ❌ No composite indexes found!')
        else:
            for row in indexes:
                print(f'  ✅ {row[0]}')
        
        print(f'\nTotal: {len(indexes)} indexes')


if __name__ == '__main__':
    asyncio.run(check_indexes())
