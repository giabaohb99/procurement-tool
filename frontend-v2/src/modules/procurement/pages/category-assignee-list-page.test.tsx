// duoc-CR-744 — bấm tiêu đề cột màn Phân công phụ trách phải sắp xếp được. Trước đây bốn cột khai
// `sortable` nhưng bảng không nhận `onSortChange` nên tiêu đề không bấm được.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { CategoryAssigneeListPage } from './category-assignee-list-page'

const ITEMS = [
  { id: 1, item_group_id: 1, item_group_name: 'Đồ điện', primary_employee_id: 1, primary_name: 'Trần Bình', primary_code: 'NV02', backup_employee_id: 0, backup_name: null, department_id: 5, department_name: 'Sản xuất' },
  { id: 2, item_group_id: 2, item_group_name: 'Bao bì', primary_employee_id: 2, primary_name: 'Ân Nguyễn', primary_code: 'NV01', backup_employee_id: 3, backup_name: 'Lê Cường', backup_code: 'NV03', department_id: 6, department_name: 'Kinh doanh' },
  { id: 3, item_group_id: 3, item_group_name: 'Hóa chất', primary_employee_id: 0, primary_name: null, backup_employee_id: 4, backup_name: 'An Phạm', backup_code: 'NV04', department_id: 5, department_name: 'Sản xuất' },
]

vi.mock('@/core/api/http-client', () => ({
  httpClient: {
    get: async (url: string) => {
      if (url === '/api/category-assignees') return { data: { items: ITEMS, total: ITEMS.length } }
      return { data: { items: [] } }
    },
    delete: vi.fn(),
  },
}))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAccess: () => true }),
}))

vi.mock('@/modules/hr/hooks/use-departments', () => ({
  useDepartments: () => ({ data: { items: [] } }),
}))

function build(url = '/procurement/category-assignees') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <CategoryAssigneeListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function header(text: string) {
  return screen.getByText(text, { selector: 'thead span' })
}

/** Thứ tự phân loại đang hiện trên bảng (cột Phân loại; ô đầu là cột mã `id` do DataTable thêm). */
function groupOrder(): string[] {
  return Array.from(document.querySelectorAll('tbody tr'))
    .map((tr) => tr.querySelectorAll('td')[1]?.textContent?.trim() ?? '')
    .filter(Boolean)
}

async function ready() {
  await waitFor(() => expect(groupOrder()).toHaveLength(3))
}

describe('CategoryAssigneeListPage — sắp xếp cột (duoc-CR-744)', () => {
  it('sorts Phân loại ascending then descending, then back to the original order', async () => {
    const user = userEvent.setup()
    build()
    await ready()

    await user.click(header('Phân loại'))
    expect(groupOrder()).toEqual(['Bao bì', 'Đồ điện', 'Hóa chất'])
    await user.click(header('Phân loại'))
    expect(groupOrder()).toEqual(['Hóa chất', 'Đồ điện', 'Bao bì'])
    await user.click(header('Phân loại'))
    expect(groupOrder()).toEqual(['Đồ điện', 'Bao bì', 'Hóa chất'])
  })

  it('sorts NSTM chính by the name shown, with the unassigned row last in both directions', async () => {
    const user = userEvent.setup()
    build()
    await ready()

    await user.click(header('NSTM chính'))
    expect(groupOrder()).toEqual(['Bao bì', 'Đồ điện', 'Hóa chất'])
    await user.click(header('NSTM chính'))
    expect(groupOrder()).toEqual(['Đồ điện', 'Bao bì', 'Hóa chất'])
  })

  it('sorts NSTM dự phòng and Phòng by the shown text', async () => {
    const user = userEvent.setup()
    build()
    await ready()

    await user.click(header('NSTM dự phòng'))
    expect(groupOrder()).toEqual(['Hóa chất', 'Bao bì', 'Đồ điện'])
    await user.click(header('Phòng'))
    expect(groupOrder()).toEqual(['Bao bì', 'Đồ điện', 'Hóa chất'])
  })

  it('restores the order from the URL so a reload or shared link keeps it', async () => {
    build('/procurement/category-assignees?sort_by=item_group_name&sort_dir=desc')
    await ready()
    expect(groupOrder()).toEqual(['Hóa chất', 'Đồ điện', 'Bao bì'])
  })

  it('does not make the action column sortable', async () => {
    build()
    await ready()
    expect(document.querySelector('thead th[aria-sort]')).toBeNull()
    expect(screen.getByText('Thao tác', { selector: 'thead span' })).toBeTruthy()
  })
})
