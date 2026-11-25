import { beforeEach, describe, expect, it, vi } from "vitest"

const { getMock, postMock } = vi.hoisted(() => ({ getMock: vi.fn(), postMock: vi.fn() }))

vi.mock("../src/api", () => ({
  default: { get: getMock, post: postMock },
}))

import { saveImportedRowsChunked, waitForBackendReady } from "../src/services/billingEntryService"
import type { ImportRow } from "../src/services/billingEntryService"

const row = (date: string, i: number): ImportRow => ({
  name_zh: "草鱼",
  weight: 1,
  unit_price: 10,
  fee_value: 0,
  release_date: date,
})

describe("waitForBackendReady", () => {
  beforeEach(() => {
    getMock.mockReset()
    postMock.mockReset()
  })

  it("已经初始化完成时立即返回，只探一次", async () => {
    getMock.mockResolvedValue({ data: { status: "ok", initialized: true } })
    await expect(waitForBackendReady(5000)).resolves.toBeUndefined()
    expect(getMock).toHaveBeenCalledTimes(1)
  })

  it("还在启动时继续轮询，直到 initialized 才返回", async () => {
    vi.useFakeTimers()
    getMock
      .mockResolvedValueOnce({ data: { status: "warming_up", initialized: false } })
      .mockResolvedValueOnce({ data: { status: "ok", initialized: true } })
    const p = waitForBackendReady(10_000)
    await vi.advanceTimersByTimeAsync(1600)
    await expect(p).resolves.toBeUndefined()
    expect(getMock).toHaveBeenCalledTimes(2)
    vi.useRealTimers()
  })

  it("一直没就绪时超时并给出可读错误", async () => {
    vi.useFakeTimers()
    getMock.mockResolvedValue({ data: { status: "warming_up", initialized: false } })
    const assertion = expect(waitForBackendReady(100)).rejects.toThrow(/服务器正在启动.*请稍后重试/)
    await vi.advanceTimersByTimeAsync(3000)
    await assertion
    vi.useRealTimers()
  })
})

describe("saveImportedRowsChunked", () => {
  beforeEach(() => {
    getMock.mockReset()
    postMock.mockReset()
    getMock.mockResolvedValue({ data: { status: "ok", initialized: true } })
  })

  it("首片失败就整体停止，不再继续追加（否则会和旧数据重复）", async () => {
    postMock.mockRejectedValueOnce({
      response: { status: 503, data: { detail: "服务器正在启动，请稍后重试" } },
    })
    const rows = [...Array.from({ length: 20 }, (_, i) => row("2026-03-01", i)), ...Array.from({ length: 10 }, (_, i) => row("2026-03-02", i))]
    await expect(saveImportedRowsChunked(rows)).rejects.toThrow(
      /导入已停止：第 1\/2 片失败（服务器正在启动，请稍后重试）。未写入任何数据/,
    )
    expect(postMock).toHaveBeenCalledTimes(1)
  })

  it("正常时按片提交并汇总结果", async () => {
    postMock.mockResolvedValue({ data: { success_count: 20, skip_count: 0, errors: [] } })
    const rows = [...Array.from({ length: 20 }, (_, i) => row("2026-03-01", i)), ...Array.from({ length: 10 }, (_, i) => row("2026-03-02", i))]
    const res = await saveImportedRowsChunked(rows)
    expect(postMock).toHaveBeenCalledTimes(2)
    expect(res.success_count).toBe(40)
    expect(res.errors).toEqual([])
  })
})
