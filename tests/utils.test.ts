import { describe, it, expect } from 'vitest'
import { dateStr, formatMoney, isPackagingItem, getSpeciesCategory, dayLabel, diffFields } from '../src/lib/utils'

describe('dateStr', () => {
  it('returns empty string for null/undefined/empty', () => {
    expect(dateStr(null)).toBe('')
    expect(dateStr(undefined)).toBe('')
    expect(dateStr('')).toBe('')
  })

  it('converts YYYY-MM-DD to YYYY/M/D format', () => {
    expect(dateStr('2026-08-12')).toBe('2026/8/12')
    expect(dateStr('2025-01-01')).toBe('2025/1/1')
  })

  it('returns original string for non-date format', () => {
    expect(dateStr('hello')).toBe('hello')
  })
})

describe('formatMoney', () => {
  it('returns "0.00" for null/undefined/non-finite', () => {
    expect(formatMoney(null)).toBe('0.00')
    expect(formatMoney(undefined)).toBe('0.00')
    expect(formatMoney(NaN)).toBe('0.00')
  })

  it('formats numbers with 2 decimal places', () => {
    expect(formatMoney(123.456)).toBe('123.46')
    expect(formatMoney(1000)).toBe('1,000.00')
  })
})

describe('isPackagingItem', () => {
  it('detects packaging items', () => {
    expect(isPackagingItem('冰块')).toBe(true)
    expect(isPackagingItem('打包袋')).toBe(true)
    expect(isPackagingItem('打包')).toBe(true)
  })

  it('returns false for normal species', () => {
    expect(isPackagingItem('草鱼')).toBe(false)
    expect(isPackagingItem('桂花鱼')).toBe(false)
  })
})

describe('getSpeciesCategory', () => {
  it('categorizes shellfish', () => {
    expect(getSpeciesCategory('花甲')).toBe('贝类')
    expect(getSpeciesCategory('带子')).toBe('贝类')
    expect(getSpeciesCategory('蛤')).toBe('贝类')
  })

  it('categorizes turtles', () => {
    expect(getSpeciesCategory('乌龟')).toBe('龟鳖类')
    expect(getSpeciesCategory('甲鱼')).toBe('龟鳖类')
  })

  it('categorizes shrimp/crabs', () => {
    expect(getSpeciesCategory('基围虾')).toBe('虾蟹类')
  })

  it('categorizes default as fish', () => {
    expect(getSpeciesCategory('草鱼')).toBe('鱼类')
  })

  it('categorizes snails', () => {
    expect(getSpeciesCategory('田螺')).toBe('螺类')
  })
})

describe('dayLabel', () => {
  it('converts YYYY-MM-DD to MM/DD', () => {
    expect(dayLabel('2026-08-12')).toBe('8/12')
    expect(dayLabel('2025-01-01')).toBe('1/1')
  })
})

describe('diffFields', () => {
  it('returns empty for null input', () => {
    expect(diffFields(null, null, [{ key: 'a', label: 'A' }])).toEqual([])
    expect(diffFields('{}', null, [{ key: 'a', label: 'A' }])).toEqual([])
  })

  it('detects changed fields', () => {
    const result = diffFields(
      JSON.stringify({ name: 'old', price: 10 }),
      JSON.stringify({ name: 'new', price: 10 }),
      [{ key: 'name', label: '名称' }, { key: 'price', label: '价格' }],
    )
    expect(result).toHaveLength(1)
    expect(result[0]).toEqual({ label: '名称', old: 'old', new: 'new' })
  })

  it('returns empty for identical data', () => {
    const result = diffFields(
      JSON.stringify({ name: 'same' }),
      JSON.stringify({ name: 'same' }),
      [{ key: 'name', label: '名称' }],
    )
    expect(result).toHaveLength(0)
  })
})
