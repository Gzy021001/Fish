-- 单据记录原始计价单位：unit=件/个（NULL=按斤），unit_jin=1 件/个 合多少斤。
-- 用途：导出《慈悲组购生明细表》时按模板还原「蛏子（件） 2 件 × 120 元/件」「带子（个） 100 个 × 4.5 元/个」，
-- 而不是统一折成「20 斤 × 12 元/斤」。重量/单价仍按公斤、元/公斤入库，金额不变。
ALTER TABLE bills ADD COLUMN IF NOT EXISTS unit VARCHAR(10);
ALTER TABLE bills ADD COLUMN IF NOT EXISTS unit_jin NUMERIC(10,4);
