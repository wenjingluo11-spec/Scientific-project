"""
数据迁移脚本：从 SQLite 迁移到 PostgreSQL (修复版)
"""

import sqlite3
import asyncio
import asyncpg
from datetime import datetime

# 配置
SQLITE_SOURCE = "./database/scientific.db"
PG_ADMIN = {
    "host": "182.92.74.187",
    "port": 9124,
    "database": "research",
    "user": "postgres",
    "password": "tphy@123"
}

# 需要迁移的表
PG_TABLES = [
    "topics",
    "papers",
    "agent_conversations",
    "competitors",
    "industry_news",
    "topic_recommendations"
]


def parse_datetime(value):
    """解析日期时间字符串"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        for fmt in [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%d',
        ]:
            try:
                return datetime.strptime(value.split('+')[0].split('Z')[0], fmt)
            except:
                continue
    return None


async def migrate_data():
    """迁移业务数据到 PostgreSQL"""
    print("=" * 60)
    print("   数据迁移脚本 (修复版)")
    print("=" * 60)
    
    # 连接 SQLite
    sqlite_conn = sqlite3.connect(SQLITE_SOURCE)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # 连接 PostgreSQL
    pg_conn = await asyncpg.connect(**PG_ADMIN)
    print("✅ Connected to PostgreSQL")
    
    # 迁移每张表
    for table in PG_TABLES:
        await migrate_table(sqlite_cursor, pg_conn, table)
    
    # 授权给 llm_dev
    await pg_conn.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO llm_dev")
    await pg_conn.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO llm_dev")
    
    sqlite_conn.close()
    await pg_conn.close()
    print("\n✅ Migration completed!")


async def migrate_table(sqlite_cursor, pg_conn, table_name):
    """迁移单张表"""
    # 检查表是否存在
    sqlite_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    if not sqlite_cursor.fetchone():
        print(f"⚠️ Table {table_name} not found. Skipping.")
        return
    
    # 获取 SQLite 数据
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"ℹ️ Table {table_name}: No data")
        return
    
    # 获取 PostgreSQL 表的列信息
    pg_columns = await pg_conn.fetch(f"""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = $1 AND table_schema = 'public'
    """, table_name)
    pg_column_names = {c['column_name'] for c in pg_columns}
    
    # 获取 SQLite 列名
    sqlite_columns = [desc[0] for desc in sqlite_cursor.description]
    
    # 找出两边都有的列 (排除 id)
    common_columns = [c for c in sqlite_columns if c in pg_column_names and c != 'id']
    
    if not common_columns:
        print(f"⚠️ Table {table_name}: No common columns")
        return
    
    migrated = 0
    errors = 0
    
    for row in rows:
        row_dict = dict(zip(sqlite_columns, row))
        values = []
        
        for col in common_columns:
            val = row_dict[col]
            # 处理日期
            if col.endswith('_at') or col.endswith('_date'):
                val = parse_datetime(val)
            values.append(val)
        
        try:
            placeholders = ", ".join([f"${i+1}" for i in range(len(common_columns))])
            columns_str = ", ".join(common_columns)
            
            await pg_conn.execute(
                f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                *values
            )
            migrated += 1
        except Exception as e:
            errors += 1
            if errors <= 3:  # 只显示前几个错误
                print(f"  ⚠️ {table_name} error: {e}")
    
    print(f"✅ Table {table_name}: {migrated}/{len(rows)} rows migrated" + (f" ({errors} errors)" if errors else ""))


if __name__ == "__main__":
    asyncio.run(migrate_data())
