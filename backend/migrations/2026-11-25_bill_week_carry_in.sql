-- 2026-11-25: 上周余款（模板里这一周开头的结转余额，导出时照抄）
ALTER TABLE bills ADD COLUMN IF NOT EXISTS week_carry_in NUMERIC(12,2);
