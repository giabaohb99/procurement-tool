import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ProfileChangeRequestListPage } from './profile-change-request-list-page'

const api = vi.hoisted(() => ({ list: vi.fn(), pendingCount: vi.fn() }))
vi.mock('../api/employee-change-request-api', () => ({ employeeChangeRequestApi: api }))

let granted = new Set<string>()
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (entity: string, action: string) => granted.has(`${entity}.${action}`) }),
}))

function renderPage(url = '/hr/profile-change-requests') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[url]}>
        <ProfileChangeRequestListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const header = (text: string) => screen.getByText(text, { selector: 'thead span' })
const lastParams = () => api.list.mock.calls.at(-1)?.[0] as Record<string, unknown>

beforeEach(() => {
  granted = new Set(['employee.write'])
  api.list.mockReset().mockResolvedValue({ items: [], total: 0 })
  api.pendingCount.mockReset().mockResolvedValue({ count: 0 })
})

//  duoc-CR-748: sắp xếp tại MÁY CHỦ; "Nhóm thay đổi" và "Số trường" tính từ JSON nên không xếp được.
describe('ProfileChangeRequestListPage — sắp xếp cột (duoc-CR-748)', () => {
  it('bấm tiêu đề gửi đúng khóa xếp, cột thời gian xếp giảm trước, và về trang 1', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('Mã NV', { selector: 'thead span' })
    const cases: [string, string, string][] = [
      ['Mã NV', 'employee_code', 'asc'],
      ['Họ tên', 'employee_name', 'asc'],
      ['Trạng thái', 'status', 'asc'],
      ['Ngày gửi', 'created_at', 'desc'],
    ]
    for (const [text, key, dir] of cases) {
      await user.click(header(text))
      await waitFor(() => expect(lastParams()).toMatchObject({ sort_by: key, sort_dir: dir, page: 1 }))
    }
  })

  it('cột tính từ JSON không xếp được, bộ lọc trạng thái vẫn đi cùng khóa xếp', async () => {
    const user = userEvent.setup()
    renderPage('/hr/profile-change-requests?sort_by=employee_name&sort_dir=desc')
    await screen.findByText('Nhóm thay đổi', { selector: 'thead span' })
    await waitFor(() => expect(lastParams()).toMatchObject({ sort_by: 'employee_name', sort_dir: 'desc', status: 1 }))
    await user.click(header('Nhóm thay đổi'))
    await user.click(header('Số trường'))
    expect(lastParams()).toMatchObject({ sort_by: 'employee_name', sort_dir: 'desc' })
  })
})
