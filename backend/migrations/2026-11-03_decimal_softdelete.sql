-- 手动迁移脚本（PostgreSQL / Neon）
-- 第一期改动：金额精度 Numeric + 软删除 + 强制改密标记
-- 执行顺序：先在生产库执行本脚本，再部署新代码。
-- 本地 SQLite 无需执行本脚本：直接删除 fish_price.db 后重启，create_all 会按新模型重建；
-- 或依赖 bootstrap.py 的 ADD COLUMN 检查（SQLite 中 NUMERIC 与 FLOAT 同为动态类型，无需改列）。

-- 1) 金额列 Float -> NUMERIC(12,2)，保留两位小数（四舍五入到分）
ALTER TABLE species ALTER COLUMN default_price TYPE NUMERIC(12,2) USING ROUND(default_price::numeric, 2);
ALTER TABLE bills   ALTER COLUMN weight       TYPE NUMERIC(12,2) USING ROUND(weight::numeric, 2);
ALTER TABLE bills   ALTER COLUMN unit_price   TYPE NUMERIC(12,2) USING ROUND(unit_price::numeric, 2);
ALTER TABLE bills   ALTER COLUMN subtotal     TYPE NUMERIC(12,2) USING ROUND(subtotal::numeric, 2);
ALTER TABLE bills   ALTER COLUMN fee_value    TYPE NUMERIC(12,2) USING ROUND(fee_value::numeric, 2);
ALTER TABLE bills   ALTER COLUMN total_amount TYPE NUMERIC(12,2) USING ROUND(total_amount::numeric, 2);

-- 2) 软删除标记（审计日志保留外键引用，删除改置位）
ALTER TABLE bills   ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE;
ALTER TABLE species ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS ix_bills_is_deleted   ON bills   (is_deleted);
CREATE INDEX IF NOT EXISTS ix_species_is_deleted ON species (is_deleted);

-- 3) 用户强制改密标记（初始账号首次登录必须改密）
ALTER TABLE users ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT FALSE;

-- 4) 现有初始账号补标记（首次登录强制改密；如已正常使用可跳过此步）
UPDATE users SET must_change_password = TRUE WHERE username IN ('admin', 'operator1', 'operator2', 'operator3');
