-- 2026-11-25: 品种默认单位由「公斤」统一为「斤」（界面与导入模板一致按斤展示）
-- 说明：重量/单价在库里仍按公斤、元/公斤存储，这里只统一单位文案，不改数值口径。
UPDATE species
SET default_unit = '斤'
WHERE default_unit = '公斤';
