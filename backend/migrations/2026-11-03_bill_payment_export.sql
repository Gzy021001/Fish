-- 手工迁移脚本（PostgreSQL / Neon）
-- 本次改动：单据增加支付方式（支付宝/微信/随喜放生）与本周现场随喜金额，支持按模板导出
-- 执行顺序：先在生产库执行本脚本，再部署新代码。
-- 本地 SQLite 无需执行本脚本：依赖 bootstrap.py 的 ADD COLUMN 检查。
ALTER TABLE bills ADD COLUMN IF NOT EXISTS payment_method VARCHAR(20);
ALTER TABLE bills ADD COLUMN IF NOT EXISTS weekly_donation NUMERIC(12,2);
