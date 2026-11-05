# CLAUDE.md

本文件是 Claude Code / AI 助手在本仓库工作时的**硬性约束**。任何改动前先读本文件，违反以下条款的改动不得提交。

## 项目定位

鱼类价格/放生记账后台（鱼价管理平台）。

- 前端：Vue 3 + TypeScript + Vite + Tailwind + Pinia + ECharts（`src/`）
- 后端：FastAPI + SQLAlchemy（`backend/`），生产 PostgreSQL/Neon + Vercel Serverless，本地 SQLite
- 部署：Vercel（`api/index.py` 入口，`vercel.json`）
- 业务核心：品种库（species）、单据（bills，DRAFT/COMPLETED 两态）、审计日志（audit_logs）、Excel 导入导出、统计看板

## 改动原则（最重要）

1. **最小改动**：只改任务要求的部分，不顺手重构、不重命名、不动无关代码、不引入新依赖。
2. **不新增功能**：除非任务明确要求，禁止添加需求外的新页面/新接口/新字段/新表。
3. **不引入新库**：新增第三方依赖（npm/pip）必须先征得同意；优先用现有依赖实现。
4. **保持 API 兼容**：改后端接口不得破坏前端现有调用（字段名、响应结构、默认行为），除非前端同步修改并在汇报中说明。
5. **前端改动同样受控**：只动与任务直接相关的文件。

## 领域硬约束（交易后台标准，不得破坏）

1. **金额精度**：金额相关列一律 `Numeric(12,2)`（SQLAlchemy），计算一律 `Decimal` 并 quantize 到分（`0.01`），禁止在 Python 里用 float 做金额运算。加金额列时必须用 Numeric。
2. **审计不可变**：`audit_logs` 是 append-only。任何删除操作只能**软删除**（置 `is_deleted=True`），禁止把 `audit_logs.bill_id / species_id` 置 NULL、禁止物理删除审计行、禁止删除含单据引用的数据。写审计前必须保证 old/new 数据取**同一字段集**，无实际变更不得写 UPDATE 日志。
3. **幂等**：写接口（POST/PUT/DELETE）不得在客户端自动重试（仅 GET 可重试）。创建单据保留"重复提交窗口"检测（同用户+同物种+同日期+同重量+同单价+同费用+近 10 秒 → 409）。批量导入的幂等依赖 `replace=true` 首片的先删后插语义。
4. **权限在后端**：任何权限判断必须由后端执行（`get_current_user` / `require_admin`），前端的 `v-if` 隐藏按钮只是 UI 辅助，不能作为安全边界。
5. **登录安全**：`/api/token` 有限流——同 IP+用户名累计 5 次失败首次锁定 **30 秒**，解锁后再失败锁定时长**翻倍递增**（60s/120s/240s/480s），封顶 15 分钟，登录成功清零；初始用户 `must_change_password=True`，未改密只能访问改密页；前端不得预填任何账号密码。
6. **列表接口必须分页**：任何 `.all()` 返回列表的接口都要有分页或上限；**单页 page_size 硬上限 200 条**（服务端 clamp）；禁止把全量数据交给前端聚合（统计聚合放后端 `GROUP BY`）。
7. **图片不进列表**：Vercel base64 模式下，品种列表接口不得返回 `data:` 开头的 image_url（单查 `/species/{id}` 除外）。新增图片字段遵循同一规则。

## 数据库 / 迁移

- 模型定义在 `backend/models.py`；schema 变更必须同时提供：
  1. `backend/migrations/` 下手写 SQL（PostgreSQL，用 `IF NOT EXISTS` / `USING` 安全写法）；
  2. `backend/bootstrap.py::ensure_db_schema_updates` 里补 SQLite 兼容的 ADD COLUMN 检查（Vercel 跳过 bootstrap，生产靠迁移 SQL）。
- 禁止随意 `drop_all`；`RESET_DATABASE=true` 仅限本地开发。
- 本地 SQLite 与生产 PostgreSQL 的 SQL 方言不同，写语句前先确认目标库。

## 编码规范

- 后端：路由（`routers/`）只做参数/权限/缓存失效，业务放 `services/`；HTTPException 用中文 detail；新接口默认挂 `Depends(auth.get_current_user)`，管理操作挂 `require_admin`。
- 前端：页面逻辑抽到 `src/composables/`；金额显示用 `formatMoney`；API 调用统一走 `src/api`（axios 实例），错误提示走 `apiErrorMessage`；新增请求错误处理必须 `isAuthError` 短路。
- 已定领域约定不得绕过：单据状态仅 `DRAFT`/`COMPLETED`；打包耗材（冰/打包/袋）由 `isPackagingItem` 判定；币种 `CNY`；`fee_type` 仅 `FIXED`。

## 测试 / 验证

- 改动后必须验证：前端 `npm run check`（vue-tsc）+ `npm run test`（vitest）；后端跑 `tests/` 下相关脚本或 pytest。
- 涉及金额/状态流转/权限/审计的改动，先想清楚对应验证用例再改代码。

## 沟通

- 与用户对话用中文；改动汇报列出"改了哪些文件、为什么、前端是否有可见变化"。
