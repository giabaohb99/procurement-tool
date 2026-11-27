import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { CalendarOff, Landmark, Users } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { SidebarProvider } from '@/shared/ui/sidebar'
import { ModuleTopbar } from './module-topbar'

//  Cụm bên phải cần provider đăng nhập / truy vấn — không liên quan đường dẫn, bỏ đi.
vi.mock('@/shared/notifications/notification-bell', () => ({ NotificationBell: () => null }))
vi.mock('./demo-account-switcher', () => ({ DemoAccountSwitcher: () => null }))
vi.mock('./user-menu', () => ({ UserMenu: () => null }))

//  bao-CR-792: link cấp mục menu hỏi quyền từng mục con. `null` = có mọi quyền (các bài kiểm cũ không quan tâm quyền).
let readable: string[] | null = null
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (entity: string) => readable === null || readable.includes(entity) }),
  useNavContext: () => ({}),
}))

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
      label: 'Tiến độ đơn mua hàng',
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
      //  Khuôn của Tra cứu thị trường: mục "Giá thị trường" gom các thẻ ẩn qua `matchPaths`.
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
      //  Khuôn của Giá nguyên vật liệu sản xuất (duoc-CR-784): "Bảng giá" gom màn ẩn "Báo giá" qua `matchPaths`,
      //  "Báo giá" bật `breadcrumbOwnLabel` nên ghi thêm cấp cuối; "Nhập liệu" ẩn mà KHÔNG bật cờ.
      label: 'Giá nguyên vật liệu',
      path: '/test/cost',
      children: [
        { label: 'Tác động', path: '/test/cost', end: true },
        { label: 'Bảng giá', path: '/test/cost/prices', matchPaths: ['/test/cost/quotes', '/test/cost/inputs'] },
        { label: 'Báo giá', path: '/test/cost/quotes', hidden: true, breadcrumbOwnLabel: true },
        { label: 'Nhập liệu', path: '/test/cost/inputs', hidden: true },
      ],
    },
    {
      //  bao-CR-792 — khuôn của Giá nguyên vật liệu sản xuất sau khi tách khóa: mỗi mục con một khóa, đường mục cha =
      //  mục con đầu tiên khai báo.
      label: 'Cụm tách khóa',
      path: '/test/split',
      entities: ['leave_request', 'leave_balance', 'leave_type'],
      children: [
        { label: 'Màn đầu', path: '/test/split', entity: 'leave_request', end: true },
        { label: 'Màn hai', path: '/test/split/two', entity: 'leave_balance' },
        { label: 'Màn ba', path: '/test/split/three', entity: 'leave_type' },
      ],
    },
    {
      //  Mục trùng tên phân hệ — khuôn của "Nhân sự" › "Nhân sự".
      label: 'Thu mua',
      path: '/test/dup',
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
  beforeEach(() => {
    readable = null
  })

  describe('parent whose children use different permission keys (bao-CR-792)', () => {
    it('links the parent level to the first child the user may read, not to the forbidden first screen', () => {
      readable = ['leave_balance', 'leave_type']
      const nav = renderAt('/test/split/three')
      expect(crumbTexts(nav)).toEqual(['Thu mua', 'Cụm tách khóa', 'Màn ba'])
      expect(within(nav).getByRole('link', { name: 'Cụm tách khóa' })).toHaveAttribute('href', '/test/split/two')
    })

    it('keeps the parent path when the user may read the screen that sits there', () => {
      readable = ['leave_request', 'leave_type']
      const nav = renderAt('/test/split/three')
      expect(within(nav).getByRole('link', { name: 'Cụm tách khóa' })).toHaveAttribute('href', '/test/split')
    })
  })

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

  //  Bốn thẻ tra giá gom về "Giá thị trường" — cấp ba phải ghi mục ĐANG SÁNG ở menu trái,
  //  không ghi tên thẻ ẩn ("Biểu đồ").
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
    expect(crumbTexts(nav)).toEqual(['Thu mua', 'Tiến độ đơn mua hàng'])
  })

  //  Anh Được báo 02/11/2026: phân hệ "Nhân sự" › mục "Nhân sự" hiện hai lần cùng một chữ.
  it('hides the module level when the menu item has the same label as the module', () => {
    const nav = renderAt('/test/dup')
    expect(crumbTexts(nav)).toEqual(['Thu mua'])
    expect(nav.querySelectorAll('[aria-current="page"]')).toHaveLength(1)
  })

  it('turns the menu level into a link back to the list on a detail page below it', () => {
    const nav = renderAt('/test/dup/304')
    expect(crumbTexts(nav)).toEqual(['Thu mua'])
    expect(within(nav).getByRole('link', { name: 'Thu mua' })).toHaveAttribute('href', '/test/dup')
  })

  it('keeps the menu level as the current page on the list itself', () => {
    const nav = renderAt('/test/report/purchase')
    //  `BreadcrumbPage` của shadcn mang `role="link"` + `aria-disabled` — kiểm bằng
    //  `aria-current` và việc KHÔNG có `href`, không bằng vai trò.
    const crumb = within(nav).getByText('Báo cáo mua hàng')
    expect(crumb).toHaveAttribute('aria-current', 'page')
    expect(crumb).not.toHaveAttribute('href')
  })

  describe('breadcrumbOwnLabel (mục ẩn tự ghi tên làm cấp cuối)', () => {
    it('appends the hidden item own label after the lit item, which becomes a link back', () => {
      const nav = renderAt('/test/cost/quotes')
      expect(crumbTexts(nav)).toEqual(['Thu mua', 'Giá nguyên vật liệu', 'Bảng giá', 'Báo giá'])
      expect(within(nav).getByRole('link', { name: 'Bảng giá' })).toHaveAttribute('href', '/test/cost/prices')
      expect(within(nav).getByRole('link', { name: 'Giá nguyên vật liệu' })).toHaveAttribute('href', '/test/cost')
      const current = nav.querySelectorAll('[aria-current="page"]')
      expect(current).toHaveLength(1)
      expect(current[0]).toHaveTextContent('Báo giá')
    })

    it('keeps the lit item name for a hidden item WITHOUT the flag', () => {
      const nav = renderAt('/test/cost/inputs')
      expect(crumbTexts(nav)).toEqual(['Thu mua', 'Giá nguyên vật liệu', 'Bảng giá'])
      expect(nav.querySelectorAll('[aria-current="page"]')[0]).toHaveTextContent('Bảng giá')
    })

    it('only applies on the exact path of the flagged item, not below it', () => {
      const nav = renderAt('/test/cost/quotes/5')
      expect(crumbTexts(nav)).toEqual(['Thu mua', 'Giá nguyên vật liệu', 'Bảng giá'])
    })

    it('leaves the lit item as the current page on its own path', () => {
      const nav = renderAt('/test/cost/prices')
      expect(crumbTexts(nav)).toEqual(['Thu mua', 'Giá nguyên vật liệu', 'Bảng giá'])
      expect(within(nav).getByText('Bảng giá')).toHaveAttribute('aria-current', 'page')
    })
  })

  it('keeps a single level at the module root', () => {
    const nav = renderAt('/test')
    expect(crumbTexts(nav)).toEqual(['Thu mua'])
  })
})
