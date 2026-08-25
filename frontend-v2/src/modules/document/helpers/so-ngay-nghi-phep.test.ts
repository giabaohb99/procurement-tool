import { describe, expect, it } from 'vitest'

import { soNgayGoiY } from './so-ngay-nghi-phep'

/**
 * ⚠️ Mấy mốc dưới đây phải khớp bản Python (`type_metadata.so_ngay_goi_y`), vì
 * backend mới là chốt ghi xuống CSDL. Lệch nhau thì ô «Tổng số ngày» hiện một
 * con số rồi lưu xong ra con số khác — người dùng không hiểu vì sao.
 */
describe('soNgayGoiY', () => {
  it('ba ngày trọn vẹn tính ra ba công', () => {
    expect(soNgayGoiY('2026-09-01', '2026-09-03', 'full', 'full')).toBe(3)
  })

  it('nửa ngày phép tính ra nửa công', () => {
    expect(soNgayGoiY('2026-09-01', '2026-09-01', 'morning', 'morning')).toBe(0.5)
  })

  it('cùng một ngày thì hai ô buổi nói về CÙNG một buổi, chỉ lấy một', () => {
    //  Lấy cả hai là ra 1 công cho một buổi sáng — sai gấp đôi.
    expect(soNgayGoiY('2026-09-01', '2026-09-01', 'afternoon', 'afternoon')).toBe(0.5)
  })

  it('đi từ chiều, về buổi sáng: hai đầu nửa ngày cộng phần giữa', () => {
    // 01 chiều (0.5) + 02 trọn (1) + 03 sáng (0.5) = 2
    expect(soNgayGoiY('2026-09-01', '2026-09-03', 'afternoon', 'morning')).toBe(2)
  })

  it('đếm CẢ cuối tuần — hệ chưa có lịch làm việc nên không tự trừ', () => {
    // 2026-09-05 là thứ Bảy, 06 Chủ nhật.
    expect(soNgayGoiY('2026-09-04', '2026-09-07', 'full', 'full')).toBe(4)
  })

  it('chưa nhập đủ ngày thì trả 0, không đoán', () => {
    expect(soNgayGoiY('', '2026-09-03', 'full', 'full')).toBe(0)
    expect(soNgayGoiY('2026-09-01', '', 'full', 'full')).toBe(0)
    expect(soNgayGoiY(undefined, undefined, undefined, undefined)).toBe(0)
  })

  it('ngày về TRƯỚC ngày đi là lỗi nhập, trả 0 chứ không ra số âm', () => {
    expect(soNgayGoiY('2026-09-05', '2026-09-01', 'full', 'full')).toBe(0)
  })

  it('buổi lạ thì coi như cả ngày, đừng ra NaN', () => {
    expect(soNgayGoiY('2026-09-01', '2026-09-01', 'linh-tinh', 'full')).toBe(1)
  })
})
