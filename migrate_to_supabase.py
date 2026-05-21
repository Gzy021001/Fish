import os
import sqlite3
from sqlalchemy import create_engine, MetaData, Table, select, insert
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# 配置路径
SQLITE_DB_PATH = Path("backend/fish_price.db")
DATABASE_URL = os.getenv("DATABASE_URL")

def migrate():
    if not DATABASE_URL:
        print("错误: 请先设置环境变量 DATABASE_URL。")
        print("用法: $env:DATABASE_URL='your_url'; python migrate_to_supabase.py")
        return

    if not SQLITE_DB_PATH.exists():
        print(f"错误: 未找到本地数据库文件 {SQLITE_DB_PATH}")
        return

    print(f"正在准备迁移...")

    # 连接 SQLite
    sqlite_engine = create_engine(f"sqlite:///{SQLITE_DB_PATH}")
    sqlite_meta = MetaData()
    sqlite_meta.reflect(bind=sqlite_engine)

    # 连接 PostgreSQL (Supabase)
    pg_url = DATABASE_URL
    if pg_url.startswith("postgres://"):
        pg_url = pg_url.replace("postgres://", "postgresql://", 1)
    
    pg_engine = create_engine(pg_url)
    
    # 获取目标数据库的会话
    Session = sessionmaker(bind=pg_engine)
    session = Session()

    # 按顺序迁移表 (处理外键依赖)
    # 1. users, 2. species, 3. bills, 4. audit_logs
    table_names = ["users", "species", "bills", "audit_logs"]

    try:
        for name in table_names:
            if name not in sqlite_meta.tables:
                print(f"警告: SQLite 中不存在表 {name}，跳过。")
                continue
                
            sqlite_table = sqlite_meta.tables[name]
            print(f"正在迁移表: {name} ...")
            
            # 读取所有数据
            with sqlite_engine.connect() as conn:
                result = conn.execute(select(sqlite_table))
                rows = [dict(row._mapping) for row in result]

            if not rows:
                print(f"表 {name} 为空，跳过。")
                continue

            # 插入到 PostgreSQL
            # 使用反射获取 PG 表结构 (假设已经由 app 运行创建好了)
            pg_meta = MetaData()
            pg_meta.reflect(bind=pg_engine, only=[name])
            pg_table = pg_meta.tables[name]

            # 批量插入
            session.execute(insert(pg_table), rows)
            print(f"表 {name} 迁移完成，共 {len(rows)} 条记录。")

        session.commit()
        print("\n🎉 所有数据迁移成功！")
    except Exception as e:
        session.rollback()
        print(f"\n❌ 迁移失败: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    migrate()
