import { describe, expect, it } from 'vitest'

import { SEAL_STATUS, SEAL_STATUS_BADGE, SEAL_STATUS_CHART_COLOR, SEAL_STATUS_LABELS } from './seal-request'

const ALL_STATUSES = Object.values(SEAL_STATUS)

describe('bộ mã trạng thái phiếu đóng dấu', () => {
  it('mọi trạng thái đều có nhãn và tông huy hiệu', () => {
    for (const status of ALL_STATUSES) {
      expect(SEAL_STATUS_LABELS[status], `thiếu nhãn cho mã ${status}`).toBeTruthy()
      expect(SEAL_STATUS_BADGE[status], `thiếu tông huy hiệu cho mã ${status}`).toBeTruthy()
    }
  })

  //  Lỗi thật đã xảy ra: trang Tổng quan tô bánh bằng một mảng NĂM màu đánh
  //  theo thứ hạng (`STATUS_COLORS[i % 5]`) trong khi bộ mã có BẢY trạng thái,
  //  nên «Yêu cầu chỉnh sửa» tô lại đúng màu của «Nháp» — hai ô chú giải xanh
  //  y hệt nhau. Hai bài kiểm dưới canh đúng chỗ đó: đủ màu, và không trùng.
  it('mọi trạng thái đều có màu biểu đồ riêng', () => {
    for (const status of ALL_STATUSES) {
      expect(SEAL_STATUS_CHART_COLOR[status], `thiếu màu biểu đồ cho mã ${status}`).toBeTruthy()
    }
  })

  it('không có hai trạng thái nào dùng chung một màu trên bánh', () => {
    const colors = ALL_STATUSES.map((s) => SEAL_STATUS_CHART_COLOR[s])
    expect(new Set(colors).size).toBe(ALL_STATUSES.length)
  })

  it('màu lấy từ biến CSS của chủ đề, không gõ mã màu cứng', () => {
    //  Gõ thẳng `#2a78d6` thì nền tối giữ nguyên màu nền sáng và lát bánh
    //  chìm vào nền — mọi token đều có bậc riêng cho hai nền.
    for (const status of ALL_STATUSES) {
      expect(SEAL_STATUS_CHART_COLOR[status]).toMatch(/^var\(--[a-z0-9-]+\)$/)
    }
  })
})
