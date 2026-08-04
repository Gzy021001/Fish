import { spawn } from "child_process";
import http from "http";
import net from "net";

const BACKEND_PORT = 8000;
const HEALTH_ENDPOINT = `http://127.0.0.1:${BACKEND_PORT}/api/health`;
const MAX_RETRIES = 120; // 120 retries (approx 2 minutes)
const RETRY_INTERVAL = 1000; // 1 second

let backendProcess = null;
let frontendProcess = null;

// Function to check if the port is in use
function checkPortInUse(port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once("error", (err) => {
      if (err.code === "EADDRINUSE") {
        resolve(true);
      } else {
        resolve(false);
      }
    });
    server.once("listening", () => {
      server.close();
      resolve(false);
    });
    server.listen(port, "127.0.0.1");
  });
}

// Function to perform a health check on the backend
function checkBackendHealth() {
  return new Promise((resolve) => {
    const req = http.get(HEALTH_ENDPOINT, { timeout: 2000 }, (res) => {
      if (res.statusCode === 200 || res.statusCode === 503) {
        // We consider it "responsive" if it returns 200.
        // Wait, if it returns 503, it means it's initializing.
        // We should wait until it returns 200.
        let data = "";
        res.on("data", (chunk) => {
          data += chunk;
        });
        res.on("end", () => {
          try {
            const json = JSON.parse(data);
            if (json.status === "ok") {
              resolve({ ok: true });
            } else if (json.status === "error") {
              resolve({ ok: false, error: json.error });
            } else {
              resolve({ ok: false });
            }
          } catch (e) {
            resolve({ ok: false });
          }
        });
      } else {
        resolve({ ok: false });
      }
    });

    req.on("timeout", () => {
      req.destroy();
      resolve({ ok: false });
    });

    req.on("error", () => {
      resolve({ ok: false });
    });

    req.end();
  });
}

// Wait for the backend to be healthy
async function waitForBackend() {
  console.log("⏳ [Dev] Waiting for backend service to be ready...");
  for (let i = 0; i < MAX_RETRIES; i++) {
    const result = await checkBackendHealth();
    if (result.ok) {
      console.log("✅ [Dev] Backend service is fully initialized and ready!");
      return true;
    } else if (result.error) {
      console.error(`❌ [Dev] Backend initialization failed: ${result.error}`);
      return false;
    }
    await new Promise((res) => setTimeout(res, RETRY_INTERVAL));
  }
  return false;
}

// Start the backend process
function startBackend() {
  console.log("🚀 [Dev] Starting backend service...");
  const isWindows = process.platform === "win32";
  const npmCmd = isWindows ? "npm.cmd" : "npm";

  backendProcess = spawn(npmCmd, ["run", "dev:backend"], {
    stdio: "inherit",
    shell: true,
  });

  backendProcess.on("error", (err) => {
    console.error("❌ [Dev] Failed to start backend:", err);
    process.exit(1);
  });

  backendProcess.on("exit", (code) => {
    if (code !== 0 && code !== null) {
      console.error(`❌ [Dev] Backend process exited with code ${code}`);
      process.exit(code);
    }
  });
}

// Start the frontend process
function startFrontend() {
  console.log("🚀 [Dev] Starting frontend service...");
  const isWindows = process.platform === "win32";
  const npmCmd = isWindows ? "npm.cmd" : "npm";

  frontendProcess = spawn(npmCmd, ["run", "dev:frontend"], {
    stdio: "inherit",
    shell: true,
  });

  frontendProcess.on("error", (err) => {
    console.error("❌ [Dev] Failed to start frontend:", err);
    cleanupAndExit(1);
  });
}

// Clean up processes on exit
function cleanupAndExit(code = 0) {
  console.log("\n🛑 [Dev] Shutting down services...");
  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill();
  }
  if (frontendProcess && !frontendProcess.killed) {
    frontendProcess.kill();
  }
  process.exit(code);
}

// Handle termination signals
process.on("SIGINT", () => cleanupAndExit(0));
process.on("SIGTERM", () => cleanupAndExit(0));
process.on("exit", () => cleanupAndExit(0));

// Main execution
async function main() {
  try {
    const isPortInUse = await checkPortInUse(BACKEND_PORT);

    if (isPortInUse) {
      console.log(
        `⚠️  [Dev] Port ${BACKEND_PORT} is already in use. Checking if it's our healthy backend...`,
      );
      const result = await checkBackendHealth();
      if (result.ok) {
        console.log("✅ [Dev] Existing backend is healthy. Reusing it.");
      } else {
        console.error(
          `❌ [Dev] Port ${BACKEND_PORT} is occupied by an unknown/unhealthy process. Please free the port and try again.`,
        );
        process.exit(1);
      }
    } else {
      startBackend();
      const isReady = await waitForBackend();
      if (!isReady) {
        console.error(
          "❌ [Dev] Backend failed to initialize within the timeout period. Please check backend logs.",
        );
        cleanupAndExit(1);
      }
    }

    startFrontend();
  } catch (err) {
    console.error("❌ [Dev] Unexpected error:", err);
    cleanupAndExit(1);
  }
}

main();
