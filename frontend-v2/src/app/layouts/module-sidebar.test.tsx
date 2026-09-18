import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { CalendarOff, Users } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { SidebarProvider } from '@/shared/ui/sidebar'
import { ModuleSidebar } from './module-sidebar'

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: () => true,
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
})
