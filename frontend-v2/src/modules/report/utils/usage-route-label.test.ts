import { describe, expect, it } from 'vitest'

import { labelRouteInApp } from './usage-route-label'

describe('labelRouteInApp', () => {
  it('maps a detail pattern to module + list screen marked as detail', () => {
    const label = labelRouteInApp('/procurement/purchase-orders/:id')
    expect(label).toMatchObject({ module: 'Thu mua', known: true })
    expect(label.screen).toBe('Đơn mua hàng (chi tiết)')
  })

  it('maps the list path itself without a detail suffix', () => {
    expect(labelRouteInApp('/procurement/purchase-orders').screen).toBe('Đơn mua hàng')
  })

  it('does not match a path that merely shares a string prefix', () => {
    //  Chỉ khớp theo ĐOẠN đường dẫn: không được dán nhãn «Đơn mua hàng» cho một đường chỉ giống chuỗi đầu.
    const label = labelRouteInApp('/procurement/purchase-orders-archive')
    expect(label.screen).not.toContain('Đơn mua hàng')
    expect(label.screen).toContain('purchase-orders-archive')
  })

  it('falls back to the legacy label for unknown patterns', () => {
    const label = labelRouteInApp('/legacy/thing/:id')
    expect(label).toEqual({ module: '', screen: 'Giao diện cũ: /legacy/thing/:id', known: false })
  })

  it('handles empty and root input without throwing', () => {
    expect(labelRouteInApp('').known).toBe(false)
    expect(labelRouteInApp('/').known).toBe(false)
  })
})
