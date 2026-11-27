import { Users } from 'lucide-react'
import { describe, expect, it } from 'vitest'

import type { ErpModule } from '@/app/router/module-definition'
import { procurementModule } from '@/modules/procurement/routes'
import { appRoutes } from '@/shared/constants/app-routes'
import { resolveModuleBreadcrumb } from './resolve-module-breadcrumb'

const hr = {
  id: 'hr',
  title: 'Nhân sự',
  description: '',
  icon: Users,
  path: '/hr',
  accent: '',
  enabled: true,
  nav: [
    { label: 'Tổng quan', path: '/hr', end: true },
    { label: 'Nhân sự', path: '/hr/employees' },
    {
      label: 'Master',
      path: '/hr/departments',
      matchPaths: ['/hr/settings'],
      children: [
        { label: 'Phòng ban', path: '/hr/departments' },
        { label: 'Cài đặt nhân sự', path: '/hr/settings' },
      ],
    },
  ],
  routes: [],
} as unknown as ErpModule

describe('resolveModuleBreadcrumb — pageLabel (chữ cuối khi nó là "trang đang đứng")', () => {
  it('is the child label on a child page under a group', () => {
    expect(resolveModuleBreadcrumb(hr, '/hr/settings').pageLabel).toBe('Cài đặt nhân sự')
  })

  it('is the nav label on a top-level list page, and the module title at the module root', () => {
    expect(resolveModuleBreadcrumb(hr, '/hr/employees').pageLabel).toBe('Nhân sự')
    expect(resolveModuleBreadcrumb(hr, '/hr').pageLabel).toBe('Nhân sự')
  })

  it('is null on a record detail page — the last crumb is a link, the title is the record name', () => {
    expect(resolveModuleBreadcrumb(hr, '/hr/employees/304').pageLabel).toBeNull()
  })

  it('is null on a path no menu item knows, and does not match by bare prefix', () => {
    expect(resolveModuleBreadcrumb(hr, '/hr/unknown').pageLabel).toBeNull()
    expect(resolveModuleBreadcrumb(hr, '/hr/employees-archive').pageLabel).toBeNull()
  })
})

//  duoc-CR-784 — cờ `breadcrumbOwnLabel` bật ở Báo giá VTBB; bao-CR-801 thêm Lịch sử mua nguyên liệu (mở từ mã ở Bảng giá
//  nguyên liệu). Các màn ẩn khác của Thu mua giữ nguyên luật cũ.
describe('resolveModuleBreadcrumb — breadcrumbOwnLabel trên menu Thu mua thật', () => {
  it('ends with Báo giá VTBB after Bảng giá VTBB on the hidden quotes screen', () => {
    const crumb = resolveModuleBreadcrumb(procurementModule, appRoutes.procurement.packagingQuotes)
    expect(crumb.current?.label).toBe('Giá nguyên vật liệu sản xuất')
    expect(crumb.activeChild?.label).toBe('Bảng giá VTBB')
    expect(crumb.ownLabelChild?.label).toBe('Báo giá VTBB')
    //  Tiêu đề trang "Báo giá VTBB" trùng chữ cuối nên `PageHeader` tự ẩn (duoc-CR-714).
    expect(crumb.pageLabel).toBe('Báo giá VTBB')
  })

  it('ends with Lịch sử mua nguyên liệu after Bảng giá nguyên liệu on the hidden material history screen', () => {
    const crumb = resolveModuleBreadcrumb(procurementModule, appRoutes.procurement.packagingMaterialHistory)
    expect(crumb.current?.label).toBe('Giá nguyên vật liệu sản xuất')
    expect(crumb.activeChild?.label).toBe('Bảng giá nguyên liệu')
    expect(crumb.ownLabelChild?.label).toBe('Lịch sử mua nguyên liệu')
    expect(crumb.pageLabel).toBe('Lịch sử mua nguyên liệu')
    //  Màn Lịch sử mua hàng của VTBB (đường chỉ khác tiền tố `material-`) không bị kéo theo.
    const packaging = resolveModuleBreadcrumb(procurementModule, appRoutes.procurement.packagingHistory)
    expect(packaging.activeChild?.label).toBe('Lịch sử mua hàng')
    expect(packaging.ownLabelChild).toBeUndefined()
    //  Và Bảng giá nguyên liệu tự nó không có cấp cuối thừa.
    const prices = resolveModuleBreadcrumb(procurementModule, appRoutes.procurement.packagingMaterialPrices)
    expect(prices.activeChild?.label).toBe('Bảng giá nguyên liệu')
    expect(prices.ownLabelChild).toBeUndefined()
  })

  it('is set on the two hidden screens opened from a price list only', () => {
    const flagged = procurementModule.nav
      .flatMap((item) => [item, ...(item.children ?? [])])
      .filter((item) => item.breadcrumbOwnLabel)
      .map((item) => item.label)
    expect(flagged).toEqual(['Lịch sử mua nguyên liệu', 'Báo giá VTBB'])
  })

  it('keeps Customs hidden tabs and Lô xuất của tôi under Giá thị trường', () => {
    for (const path of [
      appRoutes.procurement.customsPriceSection('chart'),
      appRoutes.procurement.customsPriceSection('tariff'),
      appRoutes.procurement.customsExports,
    ]) {
      const crumb = resolveModuleBreadcrumb(procurementModule, path)
      expect(crumb.ownLabelChild).toBeUndefined()
      expect(crumb.pageLabel).toBe('Giá thị trường')
    }
  })
})
