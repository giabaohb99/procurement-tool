import { describe, expect, it } from 'vitest'

import { suggestedDayCount } from './suggested-day-count'

/**
 * ⚠️ Mấy mốc dưới đây phải khớp bản Python (`type_metadata.so_ngay_goi_y`), vì
 * backend mới là chốt ghi xuống CSDL. Lệch nhau thì ô «Tổng số ngày» hiện một
 * con số rồi lưu xong ra con số khác — người dùng không hiểu vì sao.
 */
describe('soNgayGoiY', () => {
  it('ba ngày trọn vẹn tính ra ba công', () => {
    expect(suggestedDayCount('2026-09-01', '2026-09-03', 'full', 'full')).toBe(3)
  })

  it('nửa ngày phép tính ra nửa công', () => {
    expect(suggestedDayCount('2026-09-01', '2026-09-01', 'morning', 'morning')).toBe(0.5)
  })

  it('cùng một ngày, cùng một buổi thì ra nửa công', () => {
    expect(suggestedDayCount('2026-09-01', '2026-09-01', 'afternoon', 'afternoon')).toBe(0.5)
  })

  it('đi từ chiều, về buổi sáng: hai đầu nửa ngày cộng phần giữa', () => {
    // 01 chiều (0.5) + 02 trọn (1) + 03 sáng (0.5) = 2
    expect(suggestedDayCount('2026-09-01', '2026-09-03', 'afternoon', 'morning')).toBe(2)
  })

  /**
   * ⚠️ Ô buổi nói MỐC bắt đầu / kết thúc, không nói *"buổi nào được nghỉ"*.
   * Bản cũ tra chung một bảng cho cả hai đầu nên ba nhóm ca dưới đây ra sai —
   * và sai im lặng, vì con số vẫn là một số hợp lý (vá 07/09/2026).
   */
  describe('ô buổi là MỐC, không phải buổi', () => {
    it('bắt đầu buổi SÁNG là nghỉ trọn ngày đó, không phải nửa', () => {
      //  Bản cũ ra 2.5.
      expect(suggestedDayCount('2026-09-01', '2026-09-03', 'morning', 'full')).toBe(3)
    })

    it('kết thúc buổi CHIỀU là nghỉ trọn ngày đó, không phải nửa', () => {
      //  Bản cũ ra 2.5.
      expect(suggestedDayCount('2026-09-01', '2026-09-03', 'full', 'afternoon')).toBe(3)
    })

    it('sáng → chiều là trọn cả khoảng', () => {
      //  Bản cũ ra 2.0.
      expect(suggestedDayCount('2026-09-01', '2026-09-03', 'morning', 'afternoon')).toBe(3)
    })

    it('CÙNG ngày «cả ngày → sáng» chỉ là NỬA ngày', () => {
      //  Bản cũ ra 1.0 — người lao động mất oan nửa ngày phép.
      expect(suggestedDayCount('2026-09-01', '2026-09-01', 'full', 'morning')).toBe(0.5)
    })

    it('CÙNG ngày «sáng → chiều» là trọn một ngày', () => {
      //  Bản cũ ra 0.5.
      expect(suggestedDayCount('2026-09-01', '2026-09-01', 'morning', 'afternoon')).toBe(1)
    })

    it('CÙNG ngày «chiều → sáng» là khoảng trống, trả 0 chứ không ra số âm', () => {
      //  Backend chặn hẳn ca này; ở đây chỉ cần không sinh ra số âm.
      expect(suggestedDayCount('2026-09-01', '2026-09-01', 'afternoon', 'morning')).toBe(0)
    })

    it('khai THEO GIỜ thì không gợi ý con số bịa', () => {
      expect(suggestedDayCount('2026-09-01', '2026-09-01', 'hourly', 'hourly')).toBe(0)
    })
  })

  it('đếm CẢ cuối tuần — hệ chưa có lịch làm việc nên không tự trừ', () => {
    // 2026-09-05 là thứ Bảy, 06 Chủ nhật.
    expect(suggestedDayCount('2026-09-04', '2026-09-07', 'full', 'full')).toBe(4)
  })

  it('chưa nhập đủ ngày thì trả 0, không đoán', () => {
    expect(suggestedDayCount('', '2026-09-03', 'full', 'full')).toBe(0)
    expect(suggestedDayCount('2026-09-01', '', 'full', 'full')).toBe(0)
    expect(suggestedDayCount(undefined, undefined, undefined, undefined)).toBe(0)
  })

  it('ngày về TRƯỚC ngày đi là lỗi nhập, trả 0 chứ không ra số âm', () => {
    expect(suggestedDayCount('2026-09-05', '2026-09-01', 'full', 'full')).toBe(0)
  })

  it('buổi lạ thì coi như cả ngày, đừng ra NaN', () => {
    expect(suggestedDayCount('2026-09-01', '2026-09-01', 'linh-tinh', 'full')).toBe(1)
  })
})
