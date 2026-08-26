import { describe, expect, it } from 'vitest'

import { flowStatus } from './flow-status'

describe('flowStatus', () => {
  it('luồng tắt thì luôn là "Ngừng", kể cả khi bộ máy của loại đang bật', () => {
    expect(flowStatus({ is_active: false }, true).label).toBe('Ngừng')
    expect(flowStatus({ is_active: false }, false).label).toBe('Ngừng')
  })

  it('luồng bật + bộ máy của loại đang bật mới là "Đang chạy"', () => {
    const status = flowStatus({ is_active: true }, true)

    expect(status.label).toBe('Đang chạy')
    expect(status.tone).toBe('running')
  })

  it('luồng bật nhưng công tắc loại đang TẮT thì báo chờ, không báo đang chạy', () => {
    //  Đây là cái bẫy của cả màn: hai cờ độc lập nhau, bảng cũ chỉ đọc
    //  `is_active` nên dán nhãn "Đang dùng" cho luồng chưa chạy phút nào.
    const status = flowStatus({ is_active: true }, false)

    expect(status.label).toBe('Chờ bật bộ máy')
    expect(status.tone).toBe('waiting')
    expect(status.hint).toMatch(/đường duyệt cũ/)
  })

  it('mỗi trạng thái kèm một câu giải thích, không để rỗng', () => {
    const cases = [
      flowStatus({ is_active: false }, false),
      flowStatus({ is_active: true }, false),
      flowStatus({ is_active: true }, true),
    ]

    for (const status of cases) {
      expect(status.hint.length).toBeGreaterThan(0)
    }
  })
})
