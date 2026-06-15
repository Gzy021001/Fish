# Mobile API And Frontend Isolation Contract

## Frontend Boundary

- `src`、`index.html`、`vite.config.ts`、`src/router/index.ts`、`src/stores/auth.ts` 视为 PC 端冻结基线。
- 移动端只允许在 `src-mobile`、`mobile.html`、`vite.mobile.config.ts`、`tailwind.mobile.config.js`、`postcss.mobile.config.js` 中开发。
- 禁止为了兼容移动端而回写 PC 端组件、页面、样式和路由。

## Backend Boundary

- 后端现有接口默认行为不得改变。
- 移动端需要更轻 payload 时，只能新增可选参数或新增移动端接口。
- 列表接口默认字段集合必须保持兼容 PC。

## Storage Boundary

- PC 端继续使用 `token`、`username`、`user_avatar`。
- 移动端使用 `mobile_token`、`mobile_username`、`mobile_user_avatar`。

## Backend Enhancement Order

1. 先把头像和图片上传改成 URL 化，禁止继续新增 Base64 响应。
2. 为移动端增加更轻的列表返回字段集合，但默认接口行为不变。
3. 如果需要离线缓存，新增更新时间戳字段和增量同步参数。
4. 移动端专属接口只能新增，不能替换 PC 端默认接口。
