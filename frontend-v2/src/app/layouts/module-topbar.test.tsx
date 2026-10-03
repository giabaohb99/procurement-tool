import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { CalendarOff, Landmark, Users } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { SidebarProvider } from '@/shared/ui/sidebar'
import { ModuleTopbar } from './module-topbar'

//  Cụm bên phải cần provider đăng nhập / truy vấn — không liên quan đường dẫn, bỏ đi.
vi.mock('@/shared/notifications/notification-bell', () => ({ NotificationBell: () => null }))
vi.mock('./demo-account-switcher', () => ({ DemoAccountSwitcher: () => null }))
vi.mock('./user-menu', () => ({ UserMenu: () => null }))

const testModule: ErpModule = {
  id: 'test',
  title: 'Thu mua',
  description: '',
  icon: Users,
  path: '/test',
  accent: '',
  enabled: true,
  nav: [
    {
      label: 'Báo cáo mua hàng',
      path: '/test/report/purchase',
    },
    {
      label: 'Tiến độ mua hàng',
      path: '/test/report/purchase-progress',
    },
    {
      //  Mục con có đường KHÔNG nằm dưới đường mục cha (Lịch nghỉ ≠ /leave-requests/…).
      label: 'Nghỉ phép',
      path: '/test/leave-requests',
      icon: CalendarOff,
      children: [
        { label: 'Đơn nghỉ phép', path: '/test/leave-requests' },
        { label: 'Lịch nghỉ', path: '/test/leave-calendar' },
      ],
    },
    {
      //  Khuôn của Tra cứu thị trường: mục «Giá thị trường» gom các thẻ ẩn qua `matchPaths`.
      label: 'Tra cứu thị trường',
      path: '/test/prices',
      icon: Landmark,
      children: [
        {
          label: 'Giá thị trường',
          path: '/test/prices',
          end: true,
          matchPaths: ['/test/prices/chart'],
        },
        { label: 'Biểu đồ', path: '/test/prices/chart', hidden: true },
        { label: 'Tra cứu hóa chất', path: '/test/prices/legal' },
      ],
    },
    {
      label: 'Trùng tên',
      path: '/test/same',
      children: [{ label: 'Trùng tên', path: '/test/same' }],
    },
  ],
  routes: [],
}

function renderAt(pathname: string) {
  render(
    <MemoryRouter initialEntries={[pathname]}>
      <SidebarProvider>
        <ModuleTopbar module={testModule} />
      </SidebarProvider>
    </MemoryRouter>,
  )
  return screen.getByRole('navigation', { name: /breadcrumb/i })
}

/** Chữ của từng cấp breadcrumb, theo thứ tự. */
function crumbTexts(nav: HTMLElement): string[] {
  return within(nav)
    .getAllByRole('listitem')
    .map((item) => item.textContent?.trim() ?? '')
    .filter(Boolean)
}

describe('ModuleTopbar breadcrumb', () => {
  it('shows three levels for a submenu child whose path is outside the parent path', () => {
    const nav = renderAt('/test/leave-calendar')
    expect(crumbTexts(nav)).toEqual(['Thu mua', 'Nghỉ phép', 'Lịch nghỉ'])
  })

  it('makes the middle level a link to the parent and only the last level the current page', () => {
    const nav = renderAt('/test/leave-calendar')
    expect(within(nav).getByRole('link', { name: 'Nghỉ phép' })).toHaveAttribute(
      'href',
      '/test/leave-requests',
    )
    const current = nav.querySelectorAll('[aria-current="page"]')
    expect(current).toHaveLength(1)
    expect(current[0]).toHaveTextContent('Lịch nghỉ')
  })

  //  Bốn thẻ tra giá gom về «Giá thị trường» — cấp ba phải ghi mục ĐANG SÁNG ở menu trái,
  //  không ghi tên thẻ ẩn («Biểu đồ»).
  it('names the visible grouping item, not the hidden tab, when matched through matchPaths', () => {
    const nav = renderAt('/test/prices/chart')
    expect(crumbTexts(nav)).toEqual(['Thu mua', 'Tra cứu thị trường', 'Giá thị trường'])
  })

  it('shows Giá thị trường at the shared root path of parent and child', () => {
    const nav = renderAt('/test/prices')
    expect(crumbTexts(nav)).toEqual(['Thu mua', 'Tra cứu thị trường', 'Giá thị trường'])
  })

  it('shows a regular submenu child as the third level', () => {
    const nav = renderAt('/test/prices/legal')
    expect(crumbTexts(nav)).toEqual(['Thu mua', 'Tra cứu thị trường', 'Tra cứu hóa chất'])
  })

  it('does not repeat a child that has the same label as its parent', () => {
    const nav = renderAt('/test/same')
    expect(crumbTexts(nav)).toEqual(['Thu mua', 'Trùng tên'])
  })

  //  Hồi quy 26/09/2026: `startsWith` trần làm `/report/purchase` nuốt `/report/purchase-progress`.
  it('matches on a path boundary, not a bare prefix', () => {
    const nav = renderAt('/test/report/purchase-progress')
    expect(crumbTexts(nav)).toEqual(['Thu mua', 'Tiến độ mua hàng'])
  })

  it('keeps a single level at the module root', () => {
    const nav = renderAt('/test')
    expect(crumbTexts(nav)).toEqual(['Thu mua'])
  })
})
