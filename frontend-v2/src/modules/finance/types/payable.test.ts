import { describe, expect, it } from 'vitest'

import { AGING_BUCKETS, agingLabel, payableStatusOptions } from './payable'

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

describe('payableStatusOptions', () => {
  it('gửi lên chuỗi VIẾT TẮT của DB, chỉ hiện ra nhãn đầy đủ', () => {
    // Gửi nhãn đầy đủ ("Đã thanh toán") thì backend lọc không khớp dòng nào mà
    // cũng không báo lỗi — bảng rỗng trông y như "chưa có công nợ".
    expect(payableStatusOptions()).toEqual([
      { value: 'Chờ TT', label: 'Chờ thanh toán' },
      { value: 'Trả một phần', label: 'Thanh toán một phần' },
      { value: 'Đã TT', label: 'Đã thanh toán' },
    ])
  })
})
