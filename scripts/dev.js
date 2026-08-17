import { spawn } from "child_process";
import http from "http";

const BACKEND_PORT = 8000;
const FRONTEND_PORT = 5175;
const HEALTH_ENDPOINT = `http://127.0.0.1:${BACKEND_PORT}/api/health`;
const MAX_RETRIES = 30;
const RETRY_INTERVAL = 1000;

let backendProcess = null;
let frontendProcess = null;

// Health check
function checkBackendHealth() {
  return new Promise((resolve) => {
    const req = http.get(HEALTH_ENDPOINT, { timeout: 2000 }, (res) => {
      if (res.statusCode === 200) {
        let data = "";
        res.on("data", (chunk) => {
          data += chunk;
        });
        res.on("end", () => {
          try {
            const json = JSON.parse(data);
            resolve(
              json.status === "ok"
                ? { ok: true }
                : json.status === "error"
                  ? { ok: false, error: json.error }
                  : { ok: false },
            );
          } catch {
            resolve({ ok: false });
          }
        });
      } else {
        res.resume();
        resolve({ ok: false });
      }
    });
    req.on("timeout", () => {
      req.destroy();
      resolve({ ok: false });
    });
    req.on("error", () => resolve({ ok: false }));
    req.end();
  });
}

// Wait for backend with spinner
async function waitForBackend() {
  const frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
  for (let i = 0; i < MAX_RETRIES; i++) {
    const result = await checkBackendHealth();
    if (result.ok) {
      process.stdout.write("\r\x1b[K");
      console.log("✅ [Dev] Backend ready.");
      return true;
    }
    if (result.error) {
      process.stdout.write("\r\x1b[K");
      console.error(`❌ [Dev] Backend init failed: ${result.error}`);
      return false;
    }
    process.stdout.write(
      `\r${frames[i % frames.length]} [Dev] Waiting for backend... (${i + 1}s)`,
    );
    await new Promise((res) => setTimeout(res, RETRY_INTERVAL));
  }
  process.stdout.write("\r\x1b[K");
  return false;
}

// Start a process
function startProcess(label, npmScript, port) {
  console.log(`🚀 [Dev] Starting ${label}...`);
  const isWindows = process.platform === "win32";
  const proc = spawn(isWindows ? "npm.cmd" : "npm", ["run", npmScript], {
    stdio: "inherit",
    shell: true,
  });
  proc.on("error", (err) => {
    console.error(`❌ [Dev] ${label} start failed:`, err);
    cleanup(1);
  });
  return proc;
}

function cleanup(code = 0) {
  console.log("\n🛑 [Dev] Shutting down...");
  if (backendProcess && !backendProcess.killed) backendProcess.kill();
  if (frontendProcess && !frontendProcess.killed) frontendProcess.kill();
  process.exit(code);
}

process.on("SIGINT", () => cleanup(0));
process.on("SIGTERM", () => cleanup(0));

// Main: 前后端并行启动，总耗时 ≈ max(后端初始化, 前端编译) 而非两者之和
async function main() {
  backendProcess = startProcess("backend", "dev:backend", BACKEND_PORT);
  frontendProcess = startProcess("frontend", "dev:frontend", FRONTEND_PORT);

  const isReady = await waitForBackend();
  if (!isReady) {
    console.error("❌ [Dev] Backend did not become ready in time.");
    cleanup(1);
    return;
  }

  console.log(`🌐 [Dev] Frontend: http://localhost:${FRONTEND_PORT}`);
  console.log(`🔗 [Dev] Backend:  http://localhost:${BACKEND_PORT}`);
}

main();
