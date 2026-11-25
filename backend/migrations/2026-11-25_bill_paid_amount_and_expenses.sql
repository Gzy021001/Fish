-- 2026-11-25: 实付 / 车费船费
-- 1) bills.paid_amount：模板「实付」列记的实际付款（一般只写在该批首行，其余行为空）
-- 2) week_expenses：车费/船费等非物命支出（模板表尾的行）
ALTER TABLE bills ADD COLUMN IF NOT EXISTS paid_amount NUMERIC(12,2);

CREATE TABLE IF NOT EXISTS week_expenses (
    id SERIAL PRIMARY KEY,
    release_date DATE,
    name VARCHAR(20),
    amount NUMERIC(12,2),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS ix_week_expenses_release_date ON week_expenses (release_date);
CREATE INDEX IF NOT EXISTS ix_week_expenses_is_deleted ON week_expenses (is_deleted);
CREATE INDEX IF NOT EXISTS ix_week_expenses_created_at ON week_expenses (created_at);
