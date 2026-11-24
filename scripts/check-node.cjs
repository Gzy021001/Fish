/**
 * 启动前 Node.js 版本自检（dev / test 前置钩子）。
 *
 * 背景：本项目前端工具链（Vite 5 / Vitest 4 / vue-tsc）要求 Node.js >= 20。
 * 本机用 nvm-windows 同时装了 v12 与 v24，一旦当前版本被切回 v12，现象是：
 *   - 终端里 vite 抛 ERR_UNSUPPORTED_ESM_URL_SCHEME（node: 协议不被旧版 ESM 支持）；
 *   - IDE 的 Vitest 扩展只显示 "Vitest process exited with code 1 / could not load any config"。
 * 这里提前给出明确的中文提示，避免再去猜配置。
 *
 * 用 CommonJS + ES5 语法书写，保证在 Node 12 上也能跑出这段提示。
 */
var MIN_MAJOR = 20;
var RECOMMENDED = '24.22.0';

var raw = process.versions.node || '0.0.0';
var major = parseInt(raw.split('.')[0], 10) || 0;

if (major < MIN_MAJOR) {
  console.error('');
  console.error(
    '❌ [env] 当前 Node.js 为 v' + raw + '，本项目要求 Node.js >= ' + MIN_MAJOR + '（推荐 ' + RECOMMENDED + '）。',
  );
  console.error('   Vite 5 / Vitest 4 在 Node 12 上会直接崩溃，Vitest 扩展只会报 "Vitest process exited with code 1"。');
  console.error('');
  console.error('   修复：nvm use ' + RECOMMENDED + '  之后重开终端；IDE 需 "Developer: Reload Window"。');
  console.error('');
  process.exit(1);
}
