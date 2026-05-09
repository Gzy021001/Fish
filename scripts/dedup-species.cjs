const http = require("http")
const https = require("https")

const HOST = "127.0.0.1"
const PORT = 8000
const TOKEN = process.argv[2]

if (!TOKEN) {
  console.error("用法: node scripts/dedup-species.cjs <token>")
  console.error("Token 可从浏览器 localStorage 中获取")
  process.exit(1)
}

function api(method, path) {
  return new Promise((resolve, reject) => {
    const opts = {
      hostname: HOST,
      port: PORT,
      path: "/api" + path,
      method,
      headers: { Authorization: "Bearer " + TOKEN },
    }
    const req = http.request(opts, (res) => {
      let body = ""
      res.on("data", (chunk) => (body += chunk))
      res.on("end", () => {
        try { resolve(JSON.parse(body)) }
        catch { resolve(body) }
      })
    })
    req.on("error", reject)
    req.end()
  })
}

async function main() {
  console.log("正在获取品种列表...")
  const species = await api("GET", "/species")
  if (!Array.isArray(species)) {
    console.error("获取失败:", JSON.stringify(species))
    process.exit(1)
  }

  console.log(`共 ${species.length} 个品种`)

  const seen = new Map()
  const dupes = []

  for (const sp of species) {
    if (seen.has(sp.name_zh)) {
      dupes.push(sp)
    } else {
      seen.set(sp.name_zh, sp)
    }
  }

  if (dupes.length === 0) {
    console.log("没有重复数据，无需清理")
    process.exit(0)
  }

  console.log(`发现 ${dupes.length} 个重复品种：`)
  for (const d of dupes) {
    console.log(`  - [${d.id}] ${d.name_zh}`)
  }

  console.log(`\n开始删除...`)
  for (const d of dupes) {
    try {
      await api("DELETE", `/species/${d.id}`)
      console.log(`  ✅ 已删除 [${d.id}] ${d.name_zh}`)
    } catch (e) {
      console.error(`  ❌ 删除失败 [${d.id}] ${d.name_zh}:`, e.message)
    }
  }

  console.log("\n去重完成")
}

main()
