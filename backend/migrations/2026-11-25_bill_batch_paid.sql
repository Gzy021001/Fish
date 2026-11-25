-- 2026-11-25: 本批实付（模板里该批的原始实付总额，同批每行相同）
ALTER TABLE bills ADD COLUMN IF NOT EXISTS batch_paid NUMERIC(12,2);
