# 生成项目核心记忆计划

## 目标
根据当前 `d:\Fish` 项目（鱼价管理平台）的全貌，生成一组稳定、有价值的项目级核心记忆，以便未来 AI 会话能快速理解项目上下文。

---

## 步骤

### 步骤 1：分析已有记忆，识别知识空白
- **已有项目记忆 (7条)**：服务重启规范、按钮极简样式、双栏展示策略、品种图片上传交互、UI组件最佳实践、品种与开单核心逻辑、品种页面无操作列
- **已有用户记忆 (1条)**：界面文案偏好（中文自然语言优先）
- **空白领域**：项目全景技术栈、启动命令、设计系统、数据模型、认证体系、前后端通信约定、业务规则等

### 步骤 2：逐条生成核心记忆

按以下优先级生成 7 条项目级核心记忆：

| # | 记忆标题 | 记忆类别 | 核心内容 |
|---|---------|---------|---------|
| 1 | **项目全景与技术栈** | Knowledge | 鱼价管理平台 (Fish Price Platform)，Vue 3 + TypeScript + Vite 5 + Tailwind CSS 3 前端，FastAPI + SQLAlchemy + SQLite 后端，JWT 认证，全栈分离架构 |
| 2 | **开发服务器启动命令** | Knowledge | 前端：`npm run dev` (端口 5175, `0.0.0.0`)，后端：`uvicorn main:app --reload --host 0.0.0.0 --port 8000`，构建：`npm run build`，类型检查：`npm run check`，lint：`npm run lint` |
| 3 | **敦煌主题设计系统** | Knowledge | 敦煌佛教美学主题，主色调：石青(#3b6a87)、石绿(#357266)、土黄(#d4b37f)、朱砂红(#c34a36)，背景(#f5eedc)，卡片(#faf5ea)，文字(#3d3935)。字体：Noto Sans SC / Noto Serif SC。祥云暗纹背景图。 |
| 4 | **核心数据模型与关系** | Knowledge | users(id, username, password_hash, role) → admin/operator 角色；species(id, name_zh, default_unit, default_price, image_url) → 品种库；bills(id, user_id FK, species_id FK, weight, unit_price, currency, subtotal, fee_type, fee_value, total_amount, status) → DRAFT/COMPLETED；audit_logs(id, bill_id FK, species_id FK, entity_type, user_id FK, action, old_data, new_data, created_at) |
| 5 | **认证与权限体系** | Knowledge | JWT Bearer Token 认证，`/api/token` 登录获取 token。角色：admin(管理员) 和 operator(操作员)。前端 Pinia store 存储 token，Axios 拦截器自动附加 Authorization header，401 自动跳转 /login。路由守卫确保未登录重定向。 |
| 6 | **前后端通信约定** | Knowledge | 前端 dev server 端口 5175，后端 8000。Vite proxy 转发 `/api/*` 和 `/uploads/*` 到 `http://127.0.0.1:8000`。后端所有 API 均带 `/api` 前缀，无需 rewrite。CORS 全源开放。 |
| 7 | **双语国际化架构** | Knowledge | 使用 vue-i18n 11，locale: 'zh'，fallbackLocale: 'zh'。前端 UI 支持 国语/粤语 双语切换。 |

### 步骤 3：执行记忆写入
使用 `manage_core_memory` 工具逐条（或批量）添加以上 7 条核心记忆，scope 均设为 `project`，category 为 `Knowledge`，via 为 `discovery`。

### 步骤 4：验证
- 确认生成的记忆条目完整覆盖项目的关键信息
- 确保与已有记忆不冲突、不冗余

---

## 执行说明
1. 本计划仅涉及**读取**操作和**写入核心记忆**操作，不修改任何项目代码文件
2. 每条记忆控制在 400 字符以内，使用中文描述
