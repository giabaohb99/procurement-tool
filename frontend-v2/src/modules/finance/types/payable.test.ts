import { describe, expect, it } from 'vitest'

import { PAYABLE_STATUS_OPTIONS, AGING_BUCKETS, agingLabel, payableStatusLabel } from './payable'

describe('agingLabel', () => {
  it('gắn chữ "ngày" vào khoảng số để đọc trên bảng không tưởng là tiền', () => {
    expect(agingLabel('1-30')).toBe('1-30 ngày')
    expect(agingLabel('>90')).toBe('>90 ngày')
  })

  it('giữ nguyên "Chưa đến hạn" vì đó là câu chứ không phải khoảng ngày', () => {
    expect(agingLabel('Chưa đến hạn')).toBe('Chưa đến hạn')
  })

  it('nợ chưa có hạn trả thì backend trả chuỗi rỗng — không hiện "ngày" cụt', () => {
    expect(agingLabel('')).toBe('')
  })

  it('mọi nhóm tuổi nợ backend sinh ra đều ra được nhãn', () => {
    for (const bucket of AGING_BUCKETS) {
      expect(agingLabel(bucket), bucket).toBeTruthy()
    }
  })
})

describe('trạng thái công nợ', () => {
  it('ô lọc gửi lên MÃ, chỉ hiện ra nhãn tiếng Việt', () => {
    // Gửi nhãn ("Đã thanh toán") thay vì mã thì backend lọc không khớp dòng nào mà
    // cũng không báo lỗi — bảng rỗng trông y như "chưa có công nợ".
    expect(PAYABLE_STATUS_OPTIONS).toEqual([
      { value: 'unpaid', label: 'Chờ thanh toán' },
      { value: 'partial', label: 'Thanh toán một phần' },
      { value: 'paid', label: 'Đã thanh toán' },
    ])
  })

  it('mã lạ (dòng chưa chạy migration B-05) vẫn hiện ra nguyên văn, không nuốt mất', () => {
    // Bỏ trắng ô trạng thái là người dùng tưởng khoản nợ không có trạng thái nào.
    expect(payableStatusLabel('Đã TT')).toBe('Đã TT')
    expect(payableStatusLabel('paid')).toBe('Đã thanh toán')
    expect(payableStatusLabel('')).toBe('')
  })
})
