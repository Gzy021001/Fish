import sqlite3
import os

conn = sqlite3.connect('fish_price.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

with open('migration_data.sql', 'w', encoding='utf-8') as f:
    f.write("-- 禁用外键检查\n")
    f.write("SET session_replication_role = 'replica';\n\n")

    tables = ['users', 'species', 'bills', 'audit_logs']
    
    for table in tables:
        rows = cursor.execute(f"SELECT * FROM {table}").fetchall()
        if not rows:
            continue
        
        f.write(f"-- 导出表 {table} 的数据 ({len(rows)} 条)\n")
        
        for row in rows:
            cols = []
            vals = []
            for key in row.keys():
                cols.append(key)
                val = row[key]
                if val is None:
                    vals.append('NULL')
                elif isinstance(val, (int, float)):
                    vals.append(str(val))
                else:
                    # 替换单引号为两个单引号
                    safe_val = str(val).replace("'", "''")
                    vals.append(f"'{safe_val}'")
            
            col_str = ", ".join(cols)
            val_str = ", ".join(vals)
            f.write(f"INSERT INTO {table} ({col_str}) VALUES ({val_str}) ON CONFLICT (id) DO UPDATE SET ")
            
            # Add ON CONFLICT update logic just in case
            update_clauses = []
            for col in cols:
                if col != 'id':
                    update_clauses.append(f"{col} = EXCLUDED.{col}")
            
            if update_clauses:
                f.write(", ".join(update_clauses) + ";\n")
            else:
                f.write("id = EXCLUDED.id;\n")
            
        f.write("\n")
        # 更新自增主键序列
        f.write(f"SELECT setval('{table}_id_seq', (SELECT MAX(id) FROM {table}));\n\n")
        
    f.write("SET session_replication_role = 'origin';\n")
print("SQL exported successfully to migration_data.sql")
