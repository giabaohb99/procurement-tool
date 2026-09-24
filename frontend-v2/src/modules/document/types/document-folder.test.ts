import { describe, expect, it } from 'vitest'

import { FOLDER_ACCESS_LEVEL, folderAccessLevelLabel } from './document-folder'

describe('folderAccessLevelLabel', () => {
  it('maps each of the four known levels to its Vietnamese label', () => {
    expect(folderAccessLevelLabel(FOLDER_ACCESS_LEVEL.private)).toBe('Riêng tư')
    expect(folderAccessLevelLabel(FOLDER_ACCESS_LEVEL.view)).toBe('Xem')
    expect(folderAccessLevelLabel(FOLDER_ACCESS_LEVEL.contribute)).toBe('Đóng góp')
    expect(folderAccessLevelLabel(FOLDER_ACCESS_LEVEL.manage)).toBe('Quản lý')
  })

  // Lỗi từng gặp ở chỗ khác (duoc-CR-475 nhắc lại): `0` là RIÊNG TƯ thật, không
  // phải "chưa có giá trị" — nhầm `0` với falsy là mất luôn nhãn "Riêng tư".
  it('does not treat level 0 (Riêng tư) as a missing value', () => {
    expect(folderAccessLevelLabel(0)).toBe('Riêng tư')
    expect(folderAccessLevelLabel(0)).not.toBe('')
  })

  it('returns empty string for null/undefined instead of throwing or printing "undefined"', () => {
    expect(folderAccessLevelLabel(null)).toBe('')
    expect(folderAccessLevelLabel(undefined)).toBe('')
  })

  it('returns empty string for out-of-range numbers (negative, too large, non-integer)', () => {
    expect(folderAccessLevelLabel(-1)).toBe('')
    expect(folderAccessLevelLabel(4)).toBe('')
    expect(folderAccessLevelLabel(99)).toBe('')
    expect(folderAccessLevelLabel(1.5)).toBe('')
  })
})
