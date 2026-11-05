import { describe, expect, it } from "vitest"
import { detectColumns, extractRowPayments, normalizeSpeciesName, parseImportRows } from "../src/lib/importUtils"

const COLUMNS = {
  species: "品种",
  weight: "重量(斤)",
  unit_price: "单价(元)",
  fee_value: "服务费",
  release_date: "放生日期",
}

describe("parseImportRows", () => {
  it("完全空白的行不计入跳过（空白行不是校验失败）", () => {
    const rows = [
      { 品种: "草鱼", "重量(斤)": 100, "单价(元)": 6, 服务费: 0, 放生日期: "2026-01-03" },
      { 品种: "", "重量(斤)": "", "单价(元)": "", 服务费: "", 放生日期: "" },
      { 品种: "", "重量(斤)": "", "单价(元)": "", 服务费: "", 放生日期: "" },
      { 品种: "  ", "重量(斤)": 10, "单价(元)": 5, 服务费: "", 放生日期: "2026-01-03" },
    ]
    const result = parseImportRows(rows, COLUMNS, "2026-01-03")
    expect(result.validRows).toHaveLength(1)
    expect(result.skippedRows).toHaveLength(1)
    expect(result.skippedRows[0].reason).toContain("品种名称为空")
  })

  it("汇总行（本周现场随喜等）直接忽略，不进入跳过列表", () => {
    const rows = [
      { 品种: "本周现场随喜", "重量(斤)": "", "单价(元)": "", 服务费: "", 放生日期: "2026-01-03" },
      { 品种: "本周随喜累计", "重量(斤)": "", "单价(元)": "", 服务费: "", 放生日期: "2026-01-03" },
      { 品种: "草鱼", "重量(斤)": 100, "单价(元)": 6, 服务费: 0, 放生日期: "2026-01-03" },
    ]
    const result = parseImportRows(rows, COLUMNS, "2026-01-03")
    expect(result.validRows).toHaveLength(1)
    expect(result.skippedRows).toHaveLength(0)
  })

  it("打包耗材行（冰块/打包袋等）直接忽略，不导入也不进跳过列表", () => {
    const rows = [
      { 品种: "冰块", "重量(斤)": 100, "单价(元)": 2, 服务费: 0, 放生日期: "2026-01-03" },
      { 品种: "大冰块（块）", "重量(斤)": 50, "单价(元)": 3, 服务费: 0, 放生日期: "2026-01-03" },
      { 品种: "打包袋", "重量(斤)": 10, "单价(元)": 1, 服务费: 0, 放生日期: "2026-01-03" },
      { 品种: "草鱼", "重量(斤)": 100, "单价(元)": 6, 服务费: 0, 放生日期: "2026-01-03" },
    ]
    const result = parseImportRows(rows, COLUMNS, "2026-01-03")
    expect(result.validRows).toHaveLength(1)
    expect(result.validRows[0].name_zh).toBe("草鱼")
    expect(result.skippedRows).toHaveLength(0)
  })

  it("斤自动换算为公斤，名称别名归一化", () => {
    const rows = [
      { 品种: "大头（鳙鱼）", "重量(斤)": 200, "单价(元)": 8, 服务费: 0, 放生日期: "2026-01-03" },
      { 品种: "小油锥", "重量(斤)": 10.5, "单价(元)": 50, 服务费: 0, 放生日期: "2026-01-03" },
    ]
    const result = parseImportRows(rows, COLUMNS, "2026-01-03")
    expect(result.validRows).toHaveLength(2)
    expect(result.validRows[0]).toMatchObject({ name_zh: "鳙鱼", weight: 100 })
    expect(result.validRows[1]).toMatchObject({ name_zh: "油锥", weight: 5.25 })
  })

  it("列名自动识别（含括号/空格差异）", () => {
    const cols = detectColumns(["序号", "品种", "重量(斤)", "单价（元）", "总计", "服务费"])
    expect(cols.species).toBe("品种")
    expect(cols.weight).toBe("重量(斤)")
    expect(cols.unit_price).toBe("单价（元）")
    expect(cols.fee_value).toBe("服务费")
  })

  it("名称清洗：去掉大小/台小等前缀括号，括号内单位不当品种名", () => {
    expect(normalizeSpeciesName("（台小）泥鳅")).toBe("泥鳅")
    expect(normalizeSpeciesName("小草鱼")).toBe("草鱼")
    expect(normalizeSpeciesName("大头（鳙鱼）")).toBe("鳙鱼")
    // 括号内是单位时，保留括号外的品种名，而不是把单位当品种
    expect(normalizeSpeciesName("蛏子（件）")).toBe("蛏子")
    expect(normalizeSpeciesName("大冰块（块）")).toBe("冰块")
    expect(normalizeSpeciesName("带子（个）")).toBe("带子")
    expect(normalizeSpeciesName("带子(件)")).toBe("带子")
  })
})

describe("extractRowPayments", () => {
  it("按出现顺序抓取收款行（支付宝/微信/微信/随喜放生）", () => {
    const matrix = [
      ["序号", "品种", "重量", "单价", "总计", "服务费", "实付", "", "支付宝", 364],
      [1, "草鱼", 3.5, 8, 28, 5, 33, "", "微信", 387],
      [2, "鲫鱼", 2.8, 12, 33.6, 3, 36.6, "", "微信", 19278.03],
      [3, "甲鱼", 8, 45, 360, 10, 370, "", "随喜放生", 1300],
      ["", "", "", "", "", "", "", "", "本周随喜", "=SUM(J4:J7)"],
    ]
    expect(extractRowPayments(matrix)).toEqual([
      { kind: "alipay", amount: 364 },
      { kind: "wechat", amount: 387 },
      { kind: "wechat", amount: 19278.03 },
      { kind: "suixi", amount: 1300 },
    ])
  })

  it("收款区从表头行开始（与数据行错开）也能抓到", () => {
    const matrix = [
      ["序号", "品种", "重量", "单价", "支付宝", 364],
      [1, "草鱼", 3.5, 8, "微信", 387],
      [2, "鲫鱼", 2.8, 12, "随喜放生", 1300],
    ]
    expect(extractRowPayments(matrix)).toEqual([
      { kind: "alipay", amount: 364 },
      { kind: "wechat", amount: 387 },
      { kind: "suixi", amount: 1300 },
    ])
  })

  it("没有收款区的模板返回空数组", () => {
    const rows = extractRowPayments([
      ["序号", "品种", "重量", "单价", "总计", "服务费", "实付"],
      [1, "草鱼", 3.5, 8, 28, 5, 33],
    ])
    expect(rows).toEqual([])
  })

  it("解析出的行带 matrixRow（0 起），便于排查对齐问题", () => {
    const rows = [
      { 品种: "", "重量(斤)": "", "单价(元)": "", 服务费: "", 放生日期: "" },
      { 品种: "草鱼", "重量(斤)": 100, "单价(元)": 6, 服务费: 0, 放生日期: "2026-01-03" },
      { 品种: "", "重量(斤)": "", "单价(元)": "", 服务费: "", 放生日期: "" },
      { 品种: "甲鱼", "重量(斤)": 10, "单价(元)": 45, 服务费: 0, 放生日期: "2026-01-03" },
    ]
    const result = parseImportRows(rows, COLUMNS, "2026-01-03")
    expect(result.validRows.map((r) => r.matrixRow)).toEqual([1, 3])
  })
})
