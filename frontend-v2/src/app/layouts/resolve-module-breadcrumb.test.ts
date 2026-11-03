import { Users } from 'lucide-react'
import { describe, expect, it } from 'vitest'

import type { ErpModule } from '@/app/router/module-definition'
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
