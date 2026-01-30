"""
数据迁移脚本：从 SQLite 迁移到混合数据库架构

此脚本将：
1. 将 llm_configs 表复制到新的本地 SQLite 数据库 (local_config.db)
2. 将其他业务表迁移到远程 PostgreSQL 数据库

使用方法：
    cd backend
    python migrate_to_postgres.py
"""

import sqlite3
import asyncio
import asyncpg
from datetime import datetime

# 配置
SQLITE_SOURCE = "./database/scientific.db"
SQLITE_LOCAL = "./database/local_config.db"

# PostgreSQL 配置 - 使用管理员账号创建表
PG_ADMIN = {
    "host": "182.92.74.187",
    "port": 9124,
    "database": "research",
    "user": "postgres",
    "password": "tphy@123"
}

# PostgreSQL 配置 - 应用使用的账号
PG_APP = {
    "host": "182.92.74.187",
    "port": 9124,
    "database": "research",
    "user": "llm_dev",
    "password": "tphy@123"
}

# 需要迁移到 PostgreSQL 的表
PG_TABLES = [
    "topics",
    "papers",
    "agent_conversations",
    "competitors",
    "industry_news",
    "topic_recommendations"
]


def get_table_columns(cursor, table_name):
    """获取表的列信息"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [(row[1], row[2]) for row in cursor.fetchall()]  # (name, type)


def migrate_llm_configs_to_local():
    """将 llm_configs 迁移到本地 SQLite"""
    print("\n📦 Step 1: Migrating llm_configs to local SQLite...")
    
    # 连接源数据库
    source_conn = sqlite3.connect(SQLITE_SOURCE)
    source_cursor = source_conn.cursor()
    
    # 检查 llm_configs 表是否存在
    source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='llm_configs'")
    if not source_cursor.fetchone():
        print("   ⚠️ llm_configs table not found in source database. Skipping.")
        source_conn.close()
        return
    
    # 连接/创建目标本地数据库
    local_conn = sqlite3.connect(SQLITE_LOCAL)
    local_cursor = local_conn.cursor()
    
    # 创建表
    local_cursor.execute("""
        CREATE TABLE IF NOT EXISTS llm_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) UNIQUE NOT NULL,
            provider VARCHAR(50) DEFAULT 'anthropic',
            base_url VARCHAR(500) NOT NULL,
            api_key VARCHAR(500) NOT NULL,
            default_model VARCHAR(100) NOT NULL,
            max_tokens INTEGER DEFAULT 4096,
            timeout INTEGER DEFAULT 120,
            is_primary BOOLEAN DEFAULT 0,
            created_at DATETIME,
            updated_at DATETIME
        )
    """)
    
    # 复制数据
    source_cursor.execute("SELECT * FROM llm_configs")
    rows = source_cursor.fetchall()
    
    if rows:
        # 获取列名
        columns = [desc[0] for desc in source_cursor.description]
        placeholders = ", ".join(["?" for _ in columns])
        columns_str = ", ".join(columns)
        
        for row in rows:
            try:
                local_cursor.execute(
                    f"INSERT OR REPLACE INTO llm_configs ({columns_str}) VALUES ({placeholders})",
                    row
                )
            except Exception as e:
                print(f"   ⚠️ Error inserting row: {e}")
        
        local_conn.commit()
        print(f"   ✅ Migrated {len(rows)} llm_configs to local database")
    else:
        print("   ℹ️ No llm_configs found to migrate")
    
    source_conn.close()
    local_conn.close()


async def migrate_to_postgres():
    """将业务数据迁移到 PostgreSQL"""
    print("\n📦 Step 2: Migrating business data to PostgreSQL...")
    
    # 连接 SQLite
    sqlite_conn = sqlite3.connect(SQLITE_SOURCE)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # 使用管理员账号连接 PostgreSQL 创建表
    try:
        print("   Connecting with admin account (postgres)...")
        pg_conn = await asyncpg.connect(**PG_ADMIN)
        print("   ✅ Connected to PostgreSQL as admin")
    except Exception as e:
        print(f"   ❌ Failed to connect to PostgreSQL: {e}")
        return
    
    # 创建表 (PostgreSQL 语法)
    await create_pg_tables(pg_conn)
    
    # 授权给 llm_dev
    print("   Granting permissions to llm_dev...")
    await pg_conn.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO llm_dev")
    await pg_conn.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO llm_dev")
    print("   ✅ Permissions granted")
    
    # 迁移每张表
    for table in PG_TABLES:
        await migrate_table(sqlite_cursor, pg_conn, table)
    
    sqlite_conn.close()
    await pg_conn.close()
    print("\n✅ Migration completed!")


async def create_pg_tables(pg_conn):
    """在 PostgreSQL 中创建表"""
    print("   Creating PostgreSQL tables...")
    
    # Topics 表
    await pg_conn.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            field VARCHAR(100),
            keywords TEXT,
            status VARCHAR(50) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    # Papers 表
    await pg_conn.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id SERIAL PRIMARY KEY,
            topic_id INTEGER REFERENCES topics(id),
            topic_ids TEXT,
            title VARCHAR(512),
            abstract TEXT,
            content TEXT,
            status VARCHAR(50) DEFAULT 'draft',
            quality_score FLOAT,
            detailed_scores TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    # AgentConversations 表
    await pg_conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_conversations (
            id SERIAL PRIMARY KEY,
            paper_id INTEGER REFERENCES papers(id),
            agent_role VARCHAR(100),
            message TEXT,
            iteration INTEGER DEFAULT 1,
            step_name VARCHAR(100),
            input_context TEXT,
            model_signature VARCHAR(200),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    # Competitors 表
    await pg_conn.execute("""
        CREATE TABLE IF NOT EXISTS competitors (
            id SERIAL PRIMARY KEY,
            topic_id INTEGER REFERENCES topics(id),
            title VARCHAR(500),
            authors TEXT,
            source VARCHAR(100),
            url VARCHAR(1000),
            abstract TEXT,
            citations INTEGER DEFAULT 0,
            published_date DATE,
            analysis TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    # IndustryNews 表
    await pg_conn.execute("""
        CREATE TABLE IF NOT EXISTS industry_news (
            id SERIAL PRIMARY KEY,
            topic_id INTEGER REFERENCES topics(id),
            title VARCHAR(500),
            source VARCHAR(200),
            url VARCHAR(1000),
            content TEXT,
            keywords TEXT,
            relevance_score FLOAT,
            published_date DATE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    # TopicRecommendations 表
    await pg_conn.execute("""
        CREATE TABLE IF NOT EXISTS topic_recommendations (
            id SERIAL PRIMARY KEY,
            research_field VARCHAR(200),
            specific_topic VARCHAR(500),
            keywords TEXT,
            description TEXT,
            suggestions TEXT,
            model_signature VARCHAR(200),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    print("   ✅ PostgreSQL tables created")


async def migrate_table(sqlite_cursor, pg_conn, table_name):
    """迁移单张表"""
    # 检查表是否存在
    sqlite_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    if not sqlite_cursor.fetchone():
        print(f"   ⚠️ Table {table_name} not found in source. Skipping.")
        return
    
    # 获取数据
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"   ℹ️ Table {table_name}: No data to migrate")
        return
    
    # 获取列名
    columns = [desc[0] for desc in sqlite_cursor.description]
    
    # 插入到 PostgreSQL (跳过 id 列，让 PostgreSQL 自动生成)
    columns_without_id = [c for c in columns if c != 'id']
    
    migrated = 0
    for row in rows:
        row_dict = dict(zip(columns, row))
        values = [row_dict[c] for c in columns_without_id]
        
        # 处理日期格式
        processed_values = []
        for v in values:
            if isinstance(v, str) and v and ('T' in v or '-' in v):
                try:
                    # 尝试解析日期
                    if 'T' in v:
                        processed_values.append(datetime.fromisoformat(v.replace('Z', '+00:00')))
                    else:
                        processed_values.append(v)
                except:
                    processed_values.append(v)
            else:
                processed_values.append(v)
        
        try:
            placeholders = ", ".join([f"${i+1}" for i in range(len(columns_without_id))])
            columns_str = ", ".join(columns_without_id)
            
            await pg_conn.execute(
                f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                *processed_values
            )
            migrated += 1
        except Exception as e:
            print(f"   ⚠️ Error migrating row in {table_name}: {e}")
    
    print(f"   ✅ Table {table_name}: Migrated {migrated}/{len(rows)} rows")


async def main():
    print("=" * 60)
    print("   数据迁移脚本：SQLite → 混合数据库架构")
    print("=" * 60)
    print(f"\n源数据库: {SQLITE_SOURCE}")
    print(f"本地目标 (LLM 配置): {SQLITE_LOCAL}")
    print(f"远程目标 (业务数据): PostgreSQL @ {PG_ADMIN['host']}:{PG_ADMIN['port']}/{PG_ADMIN['database']}")
    
    # Step 1: 迁移 LLM 配置到本地 SQLite
    migrate_llm_configs_to_local()
    
    # Step 2: 迁移业务数据到 PostgreSQL
    await migrate_to_postgres()
    
    print("\n" + "=" * 60)
    print("   迁移完成！")
    print("=" * 60)
    print("\n后续步骤:")
    print("1. 启动后端: python main.py")
    print("2. 验证 Settings 页面和业务功能")


if __name__ == "__main__":
    asyncio.run(main())
