import { fireEvent, render, screen, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { ErpModule } from '@/app/router/module-definition'
import { ModuleSearchTrigger } from './module-search-trigger'

//  `vi.mock` được đẩy lên ĐẦU tệp, trước mọi import — biểu tượng và hằng phải lấy BÊN TRONG hàm giả lập.
vi.mock('@/app/router/module-registry', async () => {
  const { BookOpen, ShoppingCart } = await import('lucide-react')
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
      { label: 'Đơn mua hàng', path: '/procurement/purchase-orders', entity: 'purchase_order' },
      { label: 'Phân công phụ trách', path: '/procurement/assignees', entity: 'category_assignee', manage: true },
    ],
    routes: [],
  }
  const help: ErpModule = {
    id: 'help',
    title: 'Hướng dẫn sử dụng',
    description: 'Tài liệu dùng hệ thống.',
    icon: BookOpen,
    path: '',
    accent: ACCENT,
    enabled: true,
    externalUrl: () => 'https://help.example/start',
    nav: [],
    routes: [],
  }
  //  Tiện ích cá nhân ẩn khỏi lưới thẻ: không được hiện trong hộp tìm.
  const appearance: ErpModule = {
    id: 'appearance',
    title: 'Giao diện',
    description: 'Tùy chỉnh giao diện.',
    icon: BookOpen,
    path: '/appearance',
    accent: ACCENT,
    enabled: true,
    hiddenFromLauncher: true,
    nav: [{ label: 'Tùy chỉnh giao diện', path: '/appearance' }],
    routes: [],
  }
  return { allModules: [procurement, help, appearance] }
})

//  Người này đọc được ĐMH nhưng KHÔNG quản lý được Phân công phụ trách.
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (entity: string, action: string) => entity === 'purchase_order' && action === 'read' }),
  useNavContext: () => ({}),
}))

function CurrentPath() {
  return <p data-testid="path">{useLocation().pathname}</p>
}

function renderTrigger() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <ModuleSearchTrigger />
      <Routes>
        <Route path="*" element={<CurrentPath />} />
      </Routes>
    </MemoryRouter>,
  )
}

afterEach(() => vi.restoreAllMocks())

describe('ModuleSearchTrigger (duoc-CR-781)', () => {
  it('opens with Ctrl+K and lists the modules before anything is typed', () => {
    renderTrigger()
    fireEvent.keyDown(window, { key: 'k', ctrlKey: true })
    const dialog = screen.getByRole('dialog')
    expect(within(dialog).getByText('Thu mua')).toBeInTheDocument()
    expect(within(dialog).getByText('Hướng dẫn sử dụng')).toBeInTheDocument()
    expect(within(dialog).queryByText('Giao diện')).not.toBeInTheDocument()
  })

  it('finds a screen typed without diacritics and opens it with Enter', () => {
    renderTrigger()
    fireEvent.click(screen.getByRole('button', { name: /Tìm phân hệ, chức năng/ }))
    const input = screen.getByPlaceholderText(/Tìm phân hệ, chức năng/)
    fireEvent.change(input, { target: { value: 'don mua' } })
    //  Tên kết quả bị tách khúc để tô chữ khớp — tìm theo dòng (vai `option`) chứ không theo một nút chữ.
    //  Tên đọc ra phải giữ khoảng trắng — bản đầu bọc mỗi khúc một thẻ, đọc thành "Đơnmuahàng".
    expect(screen.getByRole('option', { name: /^Đơn mua hàng/ })).toBeInTheDocument()

    fireEvent.keyDown(input, { key: 'Enter' })
    expect(screen.getByTestId('path')).toHaveTextContent('/procurement/purchase-orders')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('never offers a screen the person cannot open', () => {
    renderTrigger()
    fireEvent.keyDown(window, { key: 'k', metaKey: true })
    fireEvent.change(screen.getByPlaceholderText(/Tìm phân hệ, chức năng/), {
      target: { value: 'phan cong' },
    })
    expect(screen.queryByText('Phân công phụ trách')).not.toBeInTheDocument()
    expect(screen.getByText(/Không có phân hệ hay chức năng nào khớp "phan cong"/)).toBeInTheDocument()
  })

  it('opens an external module in a new tab instead of routing inside the app', () => {
    const open = vi.spyOn(window, 'open').mockReturnValue(null)
    renderTrigger()
    fireEvent.keyDown(window, { key: 'k', ctrlKey: true })
    fireEvent.click(screen.getByRole('option', { name: /Hướng dẫn sử dụng/ }))
    expect(open).toHaveBeenCalledWith('https://help.example/start', '_blank', 'noopener,noreferrer')
    expect(screen.getByTestId('path')).toHaveTextContent('/')
  })

  it('starts a fresh search each time it is reopened', () => {
    renderTrigger()
    fireEvent.keyDown(window, { key: 'k', ctrlKey: true })
    fireEvent.change(screen.getByPlaceholderText(/Tìm phân hệ, chức năng/), { target: { value: 'don' } })
    fireEvent.keyDown(window, { key: 'k', ctrlKey: true })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()

    fireEvent.keyDown(window, { key: 'k', ctrlKey: true })
    expect(screen.getByPlaceholderText(/Tìm phân hệ, chức năng/)).toHaveValue('')
  })
})
