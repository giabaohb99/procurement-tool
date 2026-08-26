import { describe, expect, it } from 'vitest'

import {
  IMPORT_MODE_LABELS,
  IMPORT_MODULE_COMPANY,
  IMPORT_MODULE_EMPLOYEE,
  IMPORT_MODULE_LABELS,
  IMPORT_MODULE_OPTIONS,
  IMPORT_STATUS_DONE,
  IMPORT_STATUS_FAILED,
  IMPORT_STATUS_LABELS,
  IMPORT_STATUS_QUEUED,
  IMPORT_STATUS_REVERTED,
  IMPORT_STATUS_RUNNING,
  isImportRunning,
} from './import-meta'

describe('import-meta', () => {
  it('mọi đối tượng chọn được đều có nhãn — không để lọt số trần ra dropdown', () => {
    for (const opt of IMPORT_MODULE_OPTIONS) {
      expect(IMPORT_MODULE_LABELS[opt.value], `thiếu nhãn cho module ${opt.value}`).toBeTruthy()
      expect(opt.label).toBe(IMPORT_MODULE_LABELS[opt.value])
    }
  })

  it('từ CR-176 MỌI đối tượng import đều có file mẫu (Khảo sát/ĐMH chuyển sang mẫu chuẩn)', () => {
    const noTemplate = IMPORT_MODULE_OPTIONS.filter((o) => !o.hasTemplate)
    expect(noTemplate).toEqual([])
    expect(IMPORT_MODULE_OPTIONS.map((o) => o.value)).toContain(IMPORT_MODULE_COMPANY)
    expect(IMPORT_MODULE_OPTIONS.map((o) => o.value)).toContain(IMPORT_MODULE_EMPLOYEE)
  })

  it('mỗi đối tượng import đều gắn một phân hệ (moduleId) để gom nhóm', () => {
    for (const opt of IMPORT_MODULE_OPTIONS) {
      expect(opt.moduleId, `thiếu moduleId cho ${opt.label}`).toBeTruthy()
    }
  })

  it('danh mục nền xếp trước — mặc định dialog rơi vào Công ty, không phải Khảo sát', () => {
    expect(IMPORT_MODULE_OPTIONS[0]?.value).toBe(IMPORT_MODULE_COMPANY)
  })

  it('chỉ Chờ và Đang chạy mới coi là còn chạy (để auto-poll)', () => {
    expect(isImportRunning(IMPORT_STATUS_QUEUED)).toBe(true)
    expect(isImportRunning(IMPORT_STATUS_RUNNING)).toBe(true)
    expect(isImportRunning(IMPORT_STATUS_DONE)).toBe(false)
    expect(isImportRunning(IMPORT_STATUS_FAILED)).toBe(false)
    expect(isImportRunning(IMPORT_STATUS_REVERTED)).toBe(false)
  })

  it('mọi trạng thái và chế độ đều có nhãn hiển thị', () => {
    for (const s of [
      IMPORT_STATUS_QUEUED,
      IMPORT_STATUS_RUNNING,
      IMPORT_STATUS_DONE,
      IMPORT_STATUS_FAILED,
      IMPORT_STATUS_REVERTED,
    ]) {
      expect(IMPORT_STATUS_LABELS[s]).toBeTruthy()
    }
    expect(IMPORT_MODE_LABELS[0]).toBeTruthy()
    expect(IMPORT_MODE_LABELS[1]).toBeTruthy()
  })
})
