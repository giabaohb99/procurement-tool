import { describe, expect, it } from 'vitest'

import { buildNotificationParams } from './notification-filter'

describe('buildNotificationParams', () => {
  const base = { page: 1, pageSize: 20, tab: 'all' as const, search: '' }

  it('tab Tất cả thì KHÔNG gửi tham số unread', () => {
    expect(buildNotificationParams(base)).toEqual({ page: 1, page_size: 20 })
  })

  it('tab Chưa đọc gửi unread=true', () => {
    expect(buildNotificationParams({ ...base, tab: 'unread' })).toEqual({
      page: 1,
      page_size: 20,
      unread: 'true',
    })
  })

  it('cắt khoảng trắng của từ khóa trước khi gửi', () => {
    expect(buildNotificationParams({ ...base, search: '  đơn mua  ' })).toMatchObject({
      q: 'đơn mua',
    })
  })

  it('từ khóa toàn khoảng trắng thì bỏ hẳn q, không gửi chuỗi rỗng', () => {
    expect(buildNotificationParams({ ...base, search: '   ' })).not.toHaveProperty('q')
  })

  it('giữ nguyên trang và cỡ trang đang xem', () => {
    expect(buildNotificationParams({ ...base, page: 3, pageSize: 50 })).toMatchObject({
      page: 3,
      page_size: 50,
    })
  })
})
