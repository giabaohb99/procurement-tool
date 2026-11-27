import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { CalendarOff, Users } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { SidebarProvider } from '@/shared/ui/sidebar'
import { ModuleSidebar } from './module-sidebar'

//  Chân menu phiên bản (bao-CR-722) gọi API + bộ đệm truy vấn, không thuộc chốt đang kiểm.
vi.mock('./sidebar-version-footer', () => ({ SidebarVersionFooter: () => null }))

//  `null` = có mọi quyền (mặc định của các bài kiểm cũ); bao-CR-792 cần giả người chỉ đọc được vài khóa.
let readable: string[] | null = null
beforeEach(() => {
  readable = null
})

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string) => readable === null || readable.includes(entity),
    canAny: () => true,
  }),
  useNavContext: () => ({}),
}))

const testModule: ErpModule = {
  id: 'test',
  title: 'Test Module',
  description: 'Test Description',
  icon: Users,
  path: '/test',
  accent: 'bg-rose-500/10 text-rose-600 dark:text-rose-400',
  enabled: true,
  nav: [
    {
      label: 'Nghỉ phép',
      path: '/test/leave-requests',
      icon: CalendarOff,
      children: [
        {
          label: 'Đơn nghỉ phép',
          path: '/test/leave-requests',
        },
        {
          label: 'Lịch nghỉ',
          path: '/test/leave-calendar',
        },
      ],
    },
  ],
  routes: [],
}

describe('ModuleSidebar with submenu', () => {
  it('renders parent and sub-items when item has children', () => {
    render(
      <MemoryRouter initialEntries={['/test/leave-requests']}>
        <SidebarProvider>
          <ModuleSidebar module={testModule} onResizeWidth={vi.fn()} />
        </SidebarProvider>
      </MemoryRouter>,
    )

    expect(screen.getByText('Nghỉ phép')).toBeInTheDocument()
    expect(screen.getByText('Đơn nghỉ phép')).toBeInTheDocument()
    expect(screen.getByText('Lịch nghỉ')).toBeInTheDocument()
  })

  it('highlights the active child link matching the current route', () => {
    render(
      <MemoryRouter initialEntries={['/test/leave-calendar']}>
        <SidebarProvider>
          <ModuleSidebar module={testModule} onResizeWidth={vi.fn()} />
        </SidebarProvider>
      </MemoryRouter>,
    )

    const calendarLink = screen.getByRole('link', { name: /lịch nghỉ/i })
    expect(calendarLink).toHaveAttribute('aria-current', 'page')
  })

  it('renders ChevronDown icon in the parent button with ml-auto', () => {
    render(
      <MemoryRouter initialEntries={['/test/leave-requests']}>
        <SidebarProvider>
          <ModuleSidebar module={testModule} onResizeWidth={vi.fn()} />
        </SidebarProvider>
      </MemoryRouter>,
    )

    const parentButton = screen.getByRole('button', { name: /nghỉ phép/i })
    expect(parentButton).toBeInTheDocument()
    const chevron = parentButton.querySelector('svg.lucide-chevron-down')
    expect(chevron).toBeInTheDocument()
    expect(chevron).toHaveClass('ml-auto')
  })

  it('navigates to default child path when clicking parent button', () => {
    function RouteWatcher() {
      const { pathname } = useLocation()
      return <div data-testid="current-path">{pathname}</div>
    }

    render(
      <MemoryRouter initialEntries={['/other-page']}>
        <SidebarProvider>
          <ModuleSidebar module={testModule} onResizeWidth={vi.fn()} />
          <RouteWatcher />
        </SidebarProvider>
      </MemoryRouter>,
    )

    expect(screen.getByTestId('current-path')).toHaveTextContent('/other-page')
    const parentButton = screen.getByRole('button', { name: /nghỉ phép/i })
    fireEvent.click(parentButton)

    expect(screen.getByTestId('current-path')).toHaveTextContent('/test/leave-requests')
    expect(screen.getByText('Đơn nghỉ phép')).toBeInTheDocument()
  })

  it('toggles submenu open and closed when clicking chevron without navigating', () => {
    function RouteWatcher() {
      const { pathname } = useLocation()
      return <div data-testid="current-path">{pathname}</div>
    }

    render(
      <MemoryRouter initialEntries={['/test/leave-calendar']}>
        <SidebarProvider>
          <ModuleSidebar module={testModule} onResizeWidth={vi.fn()} />
          <RouteWatcher />
        </SidebarProvider>
      </MemoryRouter>,
    )

    expect(screen.getByTestId('current-path')).toHaveTextContent('/test/leave-calendar')
    const parentButton = screen.getByRole('button', { name: /nghỉ phép/i })
    const chevron = parentButton.querySelector('svg.lucide-chevron-down')!
    expect(chevron).not.toHaveClass('-rotate-90')

    // Click chevron to collapse
    fireEvent.click(chevron)
    expect(chevron).toHaveClass('-rotate-90')
    // Path should remain unchanged
    expect(screen.getByTestId('current-path')).toHaveTextContent('/test/leave-calendar')

    // Click chevron again to expand
    fireEvent.click(chevron)
    expect(chevron).not.toHaveClass('-rotate-90')
    expect(screen.getByTestId('current-path')).toHaveTextContent('/test/leave-calendar')
  })

  //  duoc-CR-784 (25/11/2026): bấm DÒNG CHA khi đang ở một mục con phải thu / mở được (trước chỉ mở, không thu).
  it('collapses then expands the submenu when clicking the parent while a child is active, without navigating', () => {
    function RouteWatcher() {
      const { pathname } = useLocation()
      return <div data-testid="current-path">{pathname}</div>
    }

    render(
      <MemoryRouter initialEntries={['/test/leave-calendar']}>
        <SidebarProvider>
          <ModuleSidebar module={testModule} onResizeWidth={vi.fn()} />
          <RouteWatcher />
        </SidebarProvider>
      </MemoryRouter>,
    )

    const parentButton = screen.getByRole('button', { name: /nghỉ phép/i })
    const chevron = parentButton.querySelector('svg.lucide-chevron-down')!
    expect(chevron).not.toHaveClass('-rotate-90')
    expect(screen.getByText('Lịch nghỉ')).toBeInTheDocument()

    fireEvent.click(parentButton)
    expect(chevron).toHaveClass('-rotate-90')
    expect(screen.queryByText('Lịch nghỉ')).not.toBeInTheDocument()
    //  Thu lại thì dòng cha sáng thay cho mục con đang xem.
    expect(parentButton).toHaveAttribute('data-active', 'true')
    expect(screen.getByTestId('current-path')).toHaveTextContent('/test/leave-calendar')

    fireEvent.click(parentButton)
    expect(chevron).not.toHaveClass('-rotate-90')
    expect(screen.getByText('Lịch nghỉ')).toBeInTheDocument()
    expect(screen.getByTestId('current-path')).toHaveTextContent('/test/leave-calendar')
  })
})

//  bao-CR-792 — khuôn của Giá nguyên vật liệu sản xuất sau khi tách khóa: mỗi mục con một khóa riêng.
describe('ModuleSidebar parent whose children use different permission keys', () => {
  const splitModule: ErpModule = {
    ...testModule,
    nav: [
      {
        label: 'Cụm tách khóa',
        path: '/test/split',
        icon: CalendarOff,
        entities: ['leave_request', 'leave_balance', 'leave_type'],
        children: [
          { label: 'Màn đầu', path: '/test/split', entity: 'leave_request', end: true },
          { label: 'Màn hai', path: '/test/split/two', entity: 'leave_balance' },
          { label: 'Màn ba', path: '/test/split/three', entity: 'leave_type' },
        ],
      },
    ],
  }

  function renderSplit() {
    function RouteWatcher() {
      const { pathname } = useLocation()
      return <div data-testid="current-path">{pathname}</div>
    }
    render(
      <MemoryRouter initialEntries={['/other-page']}>
        <SidebarProvider>
          <ModuleSidebar module={splitModule} onResizeWidth={vi.fn()} />
          <RouteWatcher />
        </SidebarProvider>
      </MemoryRouter>,
    )
  }

  it('shows the parent with only the readable children, and a click on it opens the first of them', () => {
    readable = ['leave_balance', 'leave_type']
    renderSplit()
    fireEvent.click(screen.getByRole('button', { name: /cụm tách khóa/i }))
    expect(screen.getByTestId('current-path')).toHaveTextContent('/test/split/two')
    expect(screen.queryByText('Màn đầu')).not.toBeInTheDocument()
    expect(screen.getByText('Màn hai')).toBeInTheDocument()
    expect(screen.getByText('Màn ba')).toBeInTheDocument()
  })

  it('hides the parent when no child is readable', () => {
    readable = ['purchase_order']
    renderSplit()
    expect(screen.queryByRole('button', { name: /cụm tách khóa/i })).not.toBeInTheDocument()
  })
})

//  duoc-CR-784: mục không `group` khai SAU một nhóm (cụm Giá nguyên vật liệu sản xuất) đứng đúng chỗ, không tiêu đề.
describe('ModuleSidebar sections', () => {
  it('renders an ungrouped parent declared between two groups in place, without a group label', () => {
    const sectionsModule: ErpModule = {
      ...testModule,
      nav: [
        { label: 'Tổng quan', path: '/test', end: true },
        { label: 'Đơn mua', path: '/test/orders', group: 'Mua hàng' },
        {
          label: 'Giá nguyên vật liệu',
          path: '/test/cost',
          icon: CalendarOff,
          children: [{ label: 'Tác động', path: '/test/cost', end: true }],
        },
        { label: 'Phiếu khảo sát', path: '/test/surveys', group: 'Khảo sát' },
      ],
    }
    const { container } = render(
      <MemoryRouter initialEntries={['/test']}>
        <SidebarProvider>
          <ModuleSidebar module={sectionsModule} onResizeWidth={vi.fn()} />
        </SidebarProvider>
      </MemoryRouter>,
    )

    const labels = [...container.querySelectorAll('[data-sidebar="group-label"]')].map((el) => el.textContent)
    expect(labels).toEqual(['Mua hàng', 'Khảo sát'])
    const order = ['Tổng quan', 'Đơn mua', 'Giá nguyên vật liệu', 'Phiếu khảo sát'].map((text) =>
      screen.getByText(text),
    )
    for (let i = 1; i < order.length; i++) {
      expect(order[i - 1].compareDocumentPosition(order[i]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    }
  })
})

//  duoc-CR-754: mục `childrenAsTabs` vẽ thành MỘT dòng — mục con là dải tab trên trang, không phải submenu.
describe('ModuleSidebar with childrenAsTabs', () => {
  const tabsModule: ErpModule = {
    ...testModule,
    nav: [
      {
        label: 'Thiết lập',
        path: '/test/settings',
        icon: Users,
        childrenAsTabs: true,
        children: [
          { label: 'Cài đặt', path: '/test/settings' },
          { label: 'Loại nghỉ', path: '/test/leave-types', matchPaths: ['/test/holidays'] },
        ],
      },
    ],
  }

  function renderAt(path: string) {
    render(
      <MemoryRouter initialEntries={[path]}>
        <SidebarProvider>
          <ModuleSidebar module={tabsModule} onResizeWidth={vi.fn()} />
        </SidebarProvider>
      </MemoryRouter>,
    )
  }

  it('shows one link to the first child and never lists the children in the menu', () => {
    renderAt('/test/other')
    const link = screen.getByRole('link', { name: /thiết lập/i })
    expect(link).toHaveAttribute('href', '/test/settings')
    expect(screen.queryByText('Cài đặt')).not.toBeInTheDocument()
    expect(screen.queryByText('Loại nghỉ')).not.toBeInTheDocument()
  })

  it('stays highlighted on any child screen, including a child matchPath', () => {
    renderAt('/test/holidays/3')
    const button = screen.getByText('Thiết lập').closest('[data-active]')
    expect(button).toHaveAttribute('data-active', 'true')
  })
})
