-- 本次改动：单据增加三种随喜类型金额（支付宝/微信/随喜放生），供导出收款区按模板逐笔输出
ALTER TABLE bills ADD COLUMN IF NOT EXISTS alipay_amount NUMERIC(12,2);
ALTER TABLE bills ADD COLUMN IF NOT EXISTS wechat_amount NUMERIC(12,2);
ALTER TABLE bills ADD COLUMN IF NOT EXISTS suixi_amount NUMERIC(12,2);
