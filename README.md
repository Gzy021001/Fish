# Fish Price Platform

**鱼类价格管理平台 - 性能与部署优化版**

本项目是一个面向现代化 Web 体验的全栈应用，专为鱼类品种管理、账单录入、交易统计与审计分析设计。通过一系列深度的全链路优化，解决了跨洋网络延迟与大规模数据加载瓶颈，实现了极致的交互性能（首屏及数据加载耗时 < 1s）。

## ✨ 核心功能

- **📊 实时仪表盘 (Dashboard)**
  - 提供系统概览、关键指标统计、最新账单及数据图表展示。
  - 支持快捷操作与核心数据的全局总览。
- **🐟 品种管理 (Species Management)**
  - 鱼类品种的增删改查（CRUD）。
  - 支持高清品种图片上传与 Base64 实时呈现。
- **📝 账单与交易录入 (Billing & Transactions)**
  - 高效录入、修改与查询每日交易明细。
  - 深度优化的后端分页机制，支持超大数据量的平滑滚动与检索。
- **📥 批量数据导入 (Data Import)**
  - 支持历史账单及品种数据的批量化导入，提升初始化效率。
- **🛡️ 权限与安全 (Auth & Security)**
  - 完备的用户登录认证。
  - 基于 JWT 的 API 访问控制与浏览器状态持久化。
- **📜 操作审计日志 (Audit Logs)**
  - 自动记录关键数据的变更历史与操作人员，方便安全追溯和对账。

## 🛠️ 技术栈

- **前端 (Frontend)**
  - Vue 3 (Composition API)
  - Vite (构建与热更新)
  - Tailwind CSS (原子化响应式样式)
  - Vue Router (前端路由控制)
  - Pinia (轻量级状态管理)
- **后端 (Backend)**
  - FastAPI (高性能异步 Python Web 框架)
  - SQLAlchemy ORM (关系型数据建模与操作)
  - Pydantic (数据校验与序列化)
- **数据库 (Database)**
  - Supabase / PostgreSQL
  - PgBouncer 连接池机制 (端口 6543)
- **部署 (Deployment)**
  - Vercel Serverless (前端与 API 同构无服务器部署)

## 🚀 性能与架构优化

本项目在传统全栈架构的基础上，针对 Vercel Serverless 环境及大数据量场景进行了深度改造：

1. **极致数据加载性能**：首屏渲染及数据加载响应时间严格控制在 300ms 左右，满足 `< 1s` 的硬性业务约束。
2. **全链路分页与 Payload 瘦身**：全面弃用前端内存分页，强制启用后端分页机制。列表级接口（如 `/api/bills`、`/api/species`）强行剥离 Base64 图片等高体积字段，极大减小了网络传输体积，彻底消除了 Vercel 10s 超时瓶颈引起的 500 报错。
3. **API 缓存策略**：为高频且低频变动的数据接口（如品种列表、统计趋势）引入 LRU 内存缓存机制，大幅降低数据库 IO 负担。
4. **数据库索引优化**：重构复杂 SQL 查询，剥离如 `func.coalesce` 等会导致索引失效的函数写法，采用对索引友好的 `OR` / `UNION` 逻辑进行平替，加速查询。
5. **消除跨洋延迟 (Geo-Alignment)**：通过 `vercel.json` 强绑定 Vercel Serverless Function 执行区域为 `sin1` (新加坡)，完美对齐 Supabase 数据库的物理节点，消除了数百毫秒的跨大西洋网络延迟。
6. **性能监控中间件**：FastAPI 后端集成专属性能监控中间件 (Performance Monitoring Middleware)，在服务端实时追踪耗时超过 500ms 的慢请求并输出分析日志。
7. **数据流压缩**：后端强制启用 `GZipMiddleware` 对超过 1KB 的 JSON 响应体进行 GZip 压缩，进一步加快弱网环境下的传输效率。

## 📂 项目结构

```text
/
├── backend/            # FastAPI 后端服务核心目录
│   ├── routers/        # 路由层 (auth, bills, species, stats, logs)
│   ├── services/       # 业务逻辑服务层
│   ├── app.py          # 核心应用构建及中间件注册
│   ├── main.py         # uvicorn 启动入口
│   ├── models.py       # SQLAlchemy 数据库实体模型
│   └── database.py     # 数据库连接池及 Session 依赖管理
├── src/                # Vue 3 前端源码目录
│   ├── api/            # Axios 网络请求中心及拦截器
│   ├── components/     # 全局复用 UI 组件库
│   ├── composables/    # 封装的 Vue 组合式函数 (Hooks)
│   ├── pages/          # 视图级页面组件
│   ├── router/         # 路由配置树
│   └── stores/         # Pinia 全局状态仓
├── api/                # Vercel Serverless 函数入口映射 (如 index.py)
├── vercel.json         # Vercel 核心部署、区域及路由配置文件
├── vite.config.ts      # Vite 构建及开发代理配置
└── package.json        # 前端依赖声明与 NPM 脚本
```

## ⚙️ 部署与环境配置

### 环境变量 (`.env`)
在项目根目录需配置以下环境变量（本地和 Vercel 控制台均需配置）。
**强烈建议使用 Neon Serverless Postgres** 或 Supabase。
Neon 提供了开箱即用的连接池和分支功能，非常适合 Vercel/Serverless 环境。

```env
# 数据库连接串（以 Neon 为例）
DATABASE_URL="postgresql://[user]:[password]@[endpoint].aws.neon.tech/neondb?sslmode=require&channel_binding=require"
# JWT 加密密钥
SECRET_KEY=your_secret_key
# 数据库初始化重置标志（按需开启）
RESET_DATABASE=false
```

### 本地运行
1. **安装前端依赖**：
   ```bash
   npm install
   ```
2. **安装后端依赖**：
   ```bash
   pip install -r backend/requirements.txt
   ```
3. **启动开发服务**：
   - 终端 1 (启动前端)：`npm run dev`
   - 终端 2 (启动后端)：`cd backend && uvicorn main:app --reload --port 8000`

### Vercel 生产部署
执行 Vercel CLI 指令，强制推送最新构建与配置到生产环境：
```bash
vercel --prod --force
```
*(注意：务必确保 Vercel Dashboard 中的 Environment Variables 已正确同步)*
