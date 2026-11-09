import { describe, expect, it } from "vitest"
import {
  detectColumns,
  evalSimpleFormula,
  extractRowPayments,
  normalizeSpeciesName,
  parseImportRows,
} from "../src/lib/importUtils"

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

  it("斤制表格：重量×0.5 转公斤、单价×2 转元/公斤，总计不变", () => {
    const rows = [
      { 品种: "大头（鳙鱼）", "重量(斤)": 200, "单价(元)": 8, 服务费: 0, 放生日期: "2026-01-03" },
      { 品种: "小油锥", "重量(斤)": 10.5, "单价(元)": 50, 服务费: 0, 放生日期: "2026-01-03" },
    ]
    const result = parseImportRows(rows, COLUMNS, "2026-01-03")
    expect(result.validRows).toHaveLength(2)
    // 200斤×8元/斤 = 1600元；换算后 100公斤×16元/公斤 = 1600元（总计不变）
    expect(result.validRows[0]).toMatchObject({ name_zh: "鳙鱼", weight: 100, unit_price: 16 })
    expect(result.validRows[1]).toMatchObject({ name_zh: "油锥", weight: 5.25, unit_price: 100 })
  })

  it("以件计价的行（蛏子（件））先按 1 件=10 斤 折成斤，再换算公斤，金额不变", () => {
    const rows = [
      { 品种: "蛏子（件）", "重量(斤)": 2, "单价(元)": 120, 服务费: 0, 放生日期: "2026-08-08" },
    ]
    const result = parseImportRows(rows, COLUMNS, "2026-08-08")
    expect(result.validRows).toHaveLength(1)
    // 2 件 × 120 元/件 = 240 元；折成 20 斤 × 12 元/斤 → 10 公斤 × 24 元/公斤
    expect(result.validRows[0]).toMatchObject({ name_zh: "蛏子", weight: 10, unit_price: 24, unit: "件", unit_jin: 10 })
    expect(result.validRows[0].weight * result.validRows[0].unit_price).toBeCloseTo(240, 6)
  })

  it("普通「蛏子」按斤报价时不做件换算，也不记单位", () => {
    const rows = [
      { 品种: "蛏子", "重量(斤)": 47, "单价(元)": 12, 服务费: 0, 放生日期: "2026-10-24" },
    ]
    const result = parseImportRows(rows, COLUMNS, "2026-10-24")
    expect(result.validRows[0]).toMatchObject({ name_zh: "蛏子", weight: 23.5, unit_price: 24, unit: null, unit_jin: null })
  })

  it("按个卖的带子（无论有没有写「（个）」）按 1 个=1 斤 折成斤，金额不变并记下单位", () => {
    const rows = [
      { 品种: "带子", "重量(斤)": 300, "单价(元)": 2.8, 服务费: 0, 放生日期: "2026-01-10" },
      { 品种: "带子（个）", "重量(斤)": 100, "单价(元)": 4.5, 服务费: 0, 放生日期: "2026-08-08" },
    ]
    const result = parseImportRows(rows, COLUMNS, "2026-01-10")
    expect(result.validRows).toHaveLength(2)
    // 300 个 × 2.8 元/个 = 840 元；折成 300 斤 × 2.8 元/斤 → 150 公斤 × 5.6 元/公斤
    expect(result.validRows[0]).toMatchObject({ name_zh: "带子", weight: 150, unit_price: 5.6, unit: "个", unit_jin: 1 })
    expect(result.validRows[0].weight * result.validRows[0].unit_price).toBeCloseTo(840, 6)
    // 100 个 × 4.5 元/个 = 450 元；折成 100 斤 × 4.5 元/斤 → 50 公斤 × 9 元/公斤
    expect(result.validRows[1]).toMatchObject({ name_zh: "带子", weight: 50, unit_price: 9, unit: "个", unit_jin: 1 })
    expect(result.validRows[1].weight * result.validRows[1].unit_price).toBeCloseTo(450, 6)
  })

  it("小草龟（个）按市场价反推的 1 个=0.22 斤 折成斤，金额不变", () => {
    const rows = [
      { 品种: "小草龟（个）", "重量(斤)": 30, "单价(元)": 5.5, 服务费: 0, 放生日期: "2026-05-23" },
    ]
    const result = parseImportRows(rows, COLUMNS, "2026-05-23")
    // 30 个 × 5.5 元/个 = 165 元；6.6 斤 × 25 元/斤（市场 50 元/千克）→ 3.3 公斤 × 50 元/公斤
    expect(result.validRows[0]).toMatchObject({ name_zh: "草龟", weight: 3.3, unit_price: 50, unit: "个", unit_jin: 0.22 })
    expect(result.validRows[0].weight * result.validRows[0].unit_price).toBeCloseTo(165, 6)
  })

  it("品种写了别的单位（带子（件））时不猜，保持按表头斤处理", () => {
    const rows = [
      { 品种: "带子（件）", "重量(斤)": 2, "单价(元)": 120, 服务费: 0, 放生日期: "2026-08-08" },
    ]
    const result = parseImportRows(rows, COLUMNS, "2026-08-08")
    expect(result.validRows[0]).toMatchObject({ name_zh: "带子", weight: 1, unit_price: 240 })
  })

  it("公斤制表格（重量/单价都按公斤）不做换算", () => {
    const cols = { species: "品种", weight: "重量(公斤)", unit_price: "单价(元/公斤)", fee_value: "服务费", release_date: "放生日期" }
    const rows = [
      { 品种: "草鱼", "重量(公斤)": 100, "单价(元/公斤)": 6, 服务费: 0, 放生日期: "2026-01-03" },
    ]
    const result = parseImportRows(rows, cols, "2026-01-03")
    expect(result.validRows).toHaveLength(1)
    expect(result.validRows[0]).toMatchObject({ weight: 100, unit_price: 6 })
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

describe("evalSimpleFormula", () => {
  it("多次称重相加的重量公式能求值", () => {
    expect(evalSimpleFormula("79+77")).toBe(156)
    expect(evalSimpleFormula("=61.3+60.8+63.6")).toBe(185.7)
    expect(evalSimpleFormula("40+40+40+40+40+40+40+40+40+33.5")).toBe(393.5)
  })

  it("支持括号与四则运算，消除浮点尾差", () => {
    expect(evalSimpleFormula("(2+3)*4")).toBe(20)
    expect(evalSimpleFormula("10/4")).toBe(2.5)
    expect(evalSimpleFormula("1.1+2.2")).toBe(3.3)
  })

  it("SUM 等函数、单元格引用、非法字符返回 null（回退为空）", () => {
    expect(evalSimpleFormula("SUM(D4:D27)")).toBeNull()
    expect(evalSimpleFormula("D10+1")).toBeNull()
    expect(evalSimpleFormula("1+abc")).toBeNull()
    expect(evalSimpleFormula("")).toBeNull()
    expect(evalSimpleFormula(null)).toBeNull()
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
