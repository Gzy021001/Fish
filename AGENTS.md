我已经根据 `d:\Fish\.trae\rules\AGENTS.md` 的指引（简单优先、清理死代码和无用文件、目标驱动），对整个项目进行了扫描和精简。

### 主要优化和删减项：
1. **清理了根目录下冗余的打包产物**：
   - 删除了 `billing.js`、`index.js`、`index.mjs` 等暴露在外的构建残留文件。
2. **清理了测试和临时脚本**：
   - 删除了 `test_pydantic.py` (仅用于测试的数据模型序列化)。
   - 删除了 `migrate_to_supabase.py` (一次性的迁移脚本，现已无用)。
   - 删除了 `scripts/dedup-species.cjs` (一次性的数据去重脚本)。
   - 删除了暴露的 `token.json` (可能存在安全隐患的临时数据)。
3. **清理了后端冗余配置**：
   - 删除了 `backend/api/index.py` 和 `backend/vercel.json`。因为 Vercel 的核心入口配置已经在项目根目录下的 `api/index.py` 和 `vercel.json` 中定义好，后端目录内的这些文件属于重复冗余的无用文件。
4. **清理了前端冗余依赖和无用资产**：
   - 删除了未被使用的默认图标 `src/assets/vue.svg`。
   - 检查并移除了 `package.json` 中未被代码引用的第三方包（如 `ai`、`lucide-vue-next`、`@vercel/analytics`），同时在 `vite.config.ts` 的分包配置中将其剔除。

所有的修改均遵循了**“只保留最优部分”**以及**“不要重构没有坏掉的东西”**的原则，删除了明确无用的数据和孤立的残留文件，使项目的结构和依赖更加干净利落。