-- 手动迁移脚本（PostgreSQL / Neon）
-- 执行顺序：先在生产库执行本脚本，再部署新代码。
-- 本地 SQLite 无需执行本脚本：直接删除 fish_price.db 后重启，create_all 会按新模型重建。

-- 1) created_at: DATE -> TIMESTAMP（精确到时分秒，解决同一天审计日志无法排序）
ALTER TABLE bills      ALTER COLUMN created_at TYPE TIMESTAMP USING created_at::timestamp;
ALTER TABLE audit_logs ALTER COLUMN created_at TYPE TIMESTAMP USING created_at::timestamp;

-- 2) 趋势查询复合索引 (species_id, release_date)
CREATE INDEX IF NOT EXISTS ix_bills_species_release ON bills (species_id, release_date);
