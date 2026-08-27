import { describe, expect, it } from 'vitest'

import { BELL_ALERT_LIMIT, pickBellAlerts } from './bell-alerts'
import type { SystemAlert } from './notification-types'

function alert(level: SystemAlert['level'], title: string): SystemAlert {
  return { type: 'payable', level, title, link: '/payables' }
}

describe('chọn cảnh báo cho chuông', () => {
  it('vẽ đủ khi ít hơn hạn mức, không báo cắt bớt', () => {
    const items = [alert('danger', 'A'), alert('warn', 'B')]
    const { shown, hidden } = pickBellAlerts(items)
    expect(shown).toHaveLength(2)
    expect(hidden).toBe(0)
  })

  it('cắt còn đúng hạn mức và đếm phần bị cắt', () => {
    //  `/api/alerts` trả TOÀN BỘ, không phân trang — trên dữ liệu thật riêng
    //  công nợ quá hạn đã vài chục dòng (lỗi thấy được 27/08/2026: chuông vẽ hết,
    //  đẩy phần thông báo lên tít trên).
    const items = Array.from({ length: 30 }, (_, i) => alert('warn', `A${i}`))
    const { shown, hidden } = pickBellAlerts(items)
    expect(shown).toHaveLength(BELL_ALERT_LIMIT)
    expect(hidden).toBe(30 - BELL_ALERT_LIMIT)
  })

  it('cảnh báo NGUY HIỂM luôn được ưu tiên, không bị cảnh báo nhẹ che mất', () => {
    //  Backend xếp theo LOẠI (giao hàng → công nợ → hợp đồng) chứ không theo mức
    //  độ, nên cắt thẳng thì mấy cái "sắp tới hạn" đứng trước có thể đẩy một cái
    //  "QUÁ HẠN" ra khỏi tầm nhìn.
    const items = [
      ...Array.from({ length: 6 }, (_, i) => alert('warn', `nhe-${i}`)),
      alert('danger', 'QUÁ HẠN'),
    ]
    const { shown } = pickBellAlerts(items)
    expect(shown[0].title).toBe('QUÁ HẠN')
    expect(shown.filter((item) => item.level === 'danger')).toHaveLength(1)
  })

  it('giữ nguyên thứ tự backend trả về trong cùng một mức độ', () => {
    const items = [alert('warn', 'một'), alert('warn', 'hai'), alert('warn', 'ba')]
    expect(pickBellAlerts(items, 3).shown.map((item) => item.title)).toEqual(['một', 'hai', 'ba'])
  })

  it('không đụng vào mảng gốc', () => {
    //  Sắp xếp tại chỗ thì cache của TanStack Query bị xáo theo, và lần vẽ sau
    //  thứ tự đã khác — kiểu lỗi chỉ lộ ra sau vài nhịp poll.
    const items = [alert('warn', 'A'), alert('danger', 'B')]
    pickBellAlerts(items)
    expect(items.map((item) => item.title)).toEqual(['A', 'B'])
  })

  it('danh sách rỗng thì không có gì để vẽ và không báo cắt', () => {
    expect(pickBellAlerts([])).toEqual({ shown: [], hidden: 0 })
  })
})
