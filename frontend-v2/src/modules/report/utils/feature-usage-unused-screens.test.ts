import { describe, expect, it } from 'vitest'

import type { ErpModule } from '@/app/router/module-definition'

import { findUnusedScreens } from './feature-usage-unused-screens'

const mod = (over: Partial<ErpModule>): ErpModule =>
  ({ id: 'm', title: 'Thu mua', path: '/procurement', enabled: true, nav: [], routes: [], ...over }) as unknown as ErpModule

const item = (label: string, path: string, children?: { label: string; path: string }[]) => ({ label, path, children })

describe('findUnusedScreens (duoc-CR-655)', () => {
  const modules = [
    mod({ nav: [item('Tổng quan', '/procurement'), item('Yêu cầu mua hàng', '/procurement/requests'), item('Đơn mua hàng', '/procurement/orders')] }),
  ]

  it('lists menu screens with no seen route equal to or under their path', () => {
    const unused = findUnusedScreens(modules, ['/procurement/requests/:id'])
    expect(unused.map((u) => u.label)).toEqual(['Đơn mua hàng'])
    expect(unused[0]).toEqual({ module: 'Thu mua', label: 'Đơn mua hàng', path: '/procurement/orders' })
  })

  it('does not treat a longer sibling path as a match (requests vs requests-archive)', () => {
    const unused = findUnusedScreens(modules, ['/procurement/requests-archive'])
    expect(unused.map((u) => u.label)).toContain('Yêu cầu mua hàng')
  })

  it('judges children instead of a parent group, and skips disabled modules and the module root', () => {
    const grouped = [
      mod({ nav: [item('Danh mục', '/procurement/catalog', [{ label: 'Sản phẩm', path: '/procurement/catalog/products' }])] }),
      mod({ id: 'off', title: 'Sắp có', path: '/soon', enabled: false, nav: [item('Chưa làm', '/soon/x')] }),
    ]
    expect(findUnusedScreens(grouped, []).map((u) => u.label)).toEqual(['Sản phẩm'])
  })

  it('ignores query strings on the menu path and the seen route', () => {
    const m = [mod({ nav: [item('Lọc sẵn', '/procurement/requests?status=draft')] })]
    expect(findUnusedScreens(m, ['/procurement/requests?x=1'])).toEqual([])
  })
})
