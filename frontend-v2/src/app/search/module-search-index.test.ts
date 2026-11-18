import { Box, ShoppingCart, Users } from 'lucide-react'
import { describe, expect, it } from 'vitest'

import type { ErpModule } from '@/app/router/module-definition'
import type { CanFn } from '@/app/router/module-visibility'
import { buildModuleSearchEntries, searchModuleEntries } from './module-search-index'

const ACCENT = 'bg-sky-500/10 text-sky-600 dark:text-sky-400'

const procurement: ErpModule = {
  id: 'procurement',
  title: 'Thu mua',
  description: 'Yêu cầu báo giá, khảo sát, yêu cầu và đơn mua hàng.',
  icon: ShoppingCart,
  path: '/procurement',
  accent: ACCENT,
  enabled: true,
  nav: [
    { label: 'Tổng quan', path: '/procurement', end: true },
    { label: 'Yêu cầu mua hàng', path: '/procurement/purchase-requests', entity: 'purchase_request', group: 'Mua hàng' },
    { label: 'Đơn mua hàng', path: '/procurement/purchase-orders', entity: 'purchase_order', group: 'Mua hàng' },
    {
      label: 'Tra cứu thị trường',
      path: '/procurement/customs',
      children: [
        { label: 'Giá nhập khẩu', path: '/procurement/customs/prices', entity: 'customs_price' },
        { label: 'Biểu thuế', path: '/procurement/customs/tariff', entity: 'customs_price' },
      ],
    },
    //  Lối tắt sang Tài chính và màn con chỉ để gác route: không được thành dòng tìm.
    { label: 'Công nợ phải trả', path: '/finance/payables', entity: 'payable', crossModule: true },
    { label: 'Chi tiết ẩn', path: '/procurement/hidden', hidden: true },
  ],
  routes: [],
}

const hr: ErpModule = {
  id: 'hr',
  title: 'Nhân sự',
  description: 'Nhân viên, phòng ban, pháp nhân và phân quyền tài khoản.',
  icon: Users,
  path: '/hr',
  accent: ACCENT,
  enabled: true,
  nav: [{ label: 'Nhân viên', path: '/hr/employees', entity: 'employee' }],
  routes: [],
}

const comingSoon: ErpModule = {
  id: 'sales',
  title: 'Bán hàng',
  description: 'Đơn hàng, khách hàng và doanh thu.',
  icon: Box,
  path: '/sales',
  accent: ACCENT,
  enabled: false,
  nav: [{ label: 'Đơn hàng', path: '/sales/orders' }],
  routes: [],
}

//  Tiện ích cá nhân: có route nhưng không có thẻ trên lưới — không được lọt vào hộp tìm.
const appearance: ErpModule = {
  id: 'appearance',
  title: 'Giao diện',
  description: 'Tùy chỉnh giao diện.',
  icon: Box,
  path: '/appearance',
  accent: ACCENT,
  enabled: true,
  hiddenFromLauncher: true,
  nav: [{ label: 'Tùy chỉnh giao diện', path: '/appearance' }],
  routes: [],
}

const MODULES = [procurement, hr, comingSoon, appearance]

function canWith(granted: string[]): CanFn {
  return (entity, action) => granted.includes(`${entity}:${action}`)
}

const ALL = canWith([
  'purchase_request:read',
  'purchase_order:read',
  'customs_price:read',
  'payable:read',
  'employee:read',
])

describe('buildModuleSearchEntries — only what the person may open (duoc-CR-781)', () => {
  it('lists open modules and their visible menu items, never a coming-soon or launcher-hidden module', () => {
    const entries = buildModuleSearchEntries(MODULES, ALL)
    expect(entries.map((entry) => entry.label)).toEqual([
      'Thu mua',
      'Tổng quan',
      'Yêu cầu mua hàng',
      'Đơn mua hàng',
      'Giá nhập khẩu',
      'Biểu thuế',
      'Nhân sự',
      'Nhân viên',
    ])
  })

  it('drops cross-module shortcuts and hidden route guards so nothing shows twice or leads nowhere', () => {
    const labels = buildModuleSearchEntries(MODULES, ALL).map((entry) => entry.label)
    expect(labels).not.toContain('Công nợ phải trả')
    expect(labels).not.toContain('Chi tiết ẩn')
  })

  it('hides a screen the person has no right to, and the whole module when nothing inside is left', () => {
    //  Chỉ có quyền Nhân sự: Thu mua vẫn còn mục Tổng quan (không khai entity = mở) nên phân hệ còn,
    //  nhưng Đơn mua hàng / Yêu cầu mua hàng / Tra cứu thị trường phải biến mất.
    const labels = buildModuleSearchEntries(MODULES, canWith(['employee:read'])).map((e) => e.label)
    expect(labels).not.toContain('Đơn mua hàng')
    expect(labels).not.toContain('Giá nhập khẩu')
    expect(labels).toContain('Nhân viên')

    const noHr = buildModuleSearchEntries([hr], canWith([]))
    expect(noHr).toEqual([])
  })

  it('carries the menu group and the parent item as the trail of a child', () => {
    const entries = buildModuleSearchEntries(MODULES, ALL)
    expect(entries.find((entry) => entry.label === 'Đơn mua hàng')?.trail).toEqual(['Mua hàng'])
    expect(entries.find((entry) => entry.label === 'Biểu thuế')?.trail).toEqual(['Tra cứu thị trường'])
  })

  it('gives every entry a unique id even when two modules share a label', () => {
    const entries = buildModuleSearchEntries(MODULES, ALL)
    expect(new Set(entries.map((entry) => entry.id)).size).toBe(entries.length)
  })
})

describe('searchModuleEntries — ranking and Vietnamese matching (duoc-CR-781)', () => {
  const entries = buildModuleSearchEntries(MODULES, ALL)
  const labelsOf = (query: string) =>
    searchModuleEntries(entries, query).flatMap((group) => group.entries.map((entry) => entry.label))

  it('shows only the module list before anything is typed, not a wall of every screen', () => {
    const groups = searchModuleEntries(entries, '   ')
    expect(groups).toHaveLength(1)
    expect(groups[0].entries.map((entry) => entry.label)).toEqual(['Thu mua', 'Nhân sự'])
  })

  it('matches without diacritics and regardless of case, including đ', () => {
    expect(labelsOf('DON MUA')).toContain('Đơn mua hàng')
    expect(labelsOf('bieu thue')).toEqual(['Biểu thuế'])
  })

  it('matches every typed word across module, group and label, not one contiguous phrase', () => {
    //  Không ô nào chứa trọn "thu mua don", nhưng đủ ba chữ ở tên phân hệ + tên mục.
    expect(labelsOf('thu mua don')).toContain('Đơn mua hàng')
    //  Gõ tên mục cha thì ra các mục con của nó.
    expect(labelsOf('tra cuu')).toEqual(['Giá nhập khẩu', 'Biểu thuế'])
  })

  it('finds a module by what it does, from its description', () => {
    expect(labelsOf('phan quyen')).toEqual(['Nhân sự'])
  })

  it('puts the exact label first and the module card above its own screens', () => {
    expect(labelsOf('đơn mua hàng')[0]).toBe('Đơn mua hàng')
    const thuMua = searchModuleEntries(entries, 'thu mua')
    expect(thuMua[0].entries[0].label).toBe('Thu mua')
  })

  it('returns nothing for a word no entry has, and treats regex characters as plain text', () => {
    expect(searchModuleEntries(entries, 'khongcogi')).toEqual([])
    expect(searchModuleEntries(entries, '.*')).toEqual([])
    expect(searchModuleEntries(entries, '(')).toEqual([])
  })

  it('survives an empty catalogue', () => {
    expect(searchModuleEntries([], '')).toEqual([])
    expect(searchModuleEntries([], 'don')).toEqual([])
  })
})
