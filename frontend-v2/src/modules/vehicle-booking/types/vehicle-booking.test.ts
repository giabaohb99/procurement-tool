import { describe, expect, it } from 'vitest'

import {
  BOOKING_STATUS,
  BOOKING_STATUS_BADGE,
  BOOKING_STATUS_CHART_COLOR,
  BOOKING_STATUS_LABELS,
} from './vehicle-booking'

const ALL_STATUSES = Object.values(BOOKING_STATUS)

describe('bộ mã trạng thái phiếu đặt xe', () => {
  it('mọi trạng thái đều có nhãn và tông huy hiệu', () => {
    for (const status of ALL_STATUSES) {
      expect(BOOKING_STATUS_LABELS[status], `thiếu nhãn cho mã ${status}`).toBeTruthy()
      expect(BOOKING_STATUS_BADGE[status], `thiếu tông huy hiệu cho mã ${status}`).toBeTruthy()
    }
  })

  //  Lỗi cùng họ với duoc-CR-428 bên Duyệt dấu: trang Tổng quan tô bánh bằng
  //  một mảng NĂM màu đánh theo thứ hạng (`STATUS_COLORS[i % 5]`) trong khi bộ
  //  mã có TÁM trạng thái — hai trạng thái cuối tô lại màu của hai trạng thái
  //  đầu, và kỳ nào thiếu một trạng thái là toàn bộ màu dịch một bậc.
  it('mọi trạng thái đều có màu biểu đồ riêng', () => {
    for (const status of ALL_STATUSES) {
      expect(BOOKING_STATUS_CHART_COLOR[status], `thiếu màu biểu đồ cho mã ${status}`).toBeTruthy()
    }
  })

  it('không có hai trạng thái nào dùng chung một màu trên bánh', () => {
    const colors = ALL_STATUSES.map((s) => BOOKING_STATUS_CHART_COLOR[s])
    expect(new Set(colors).size).toBe(ALL_STATUSES.length)
  })

  it('màu lấy từ biến CSS của chủ đề, không gõ mã màu cứng', () => {
    //  Gõ thẳng `#2a78d6` thì nền tối giữ nguyên màu nền sáng và lát bánh chìm
    //  vào nền — mọi token đều có bậc riêng cho hai nền.
    for (const status of ALL_STATUSES) {
      expect(BOOKING_STATUS_CHART_COLOR[status]).toMatch(/^var\(--[a-z0-9-]+\)$/)
    }
  })
})
