import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { TooltipProvider } from '@/shared/ui/tooltip'
import type { SealRequest } from '../types/seal-request'
import { SealRequestListPage } from './seal-request-list-page'

//  duoc-CR-744: chặn ở tầng hook dữ liệu để bắt BỘ THAM SỐ gửi đi khi bấm tiêu đề cột.
const listCalls: Array<Record<string, unknown>> = []

const rows = [
  { id: 2, code: 'DD-2', title: 'Hợp đồng thuê kho', purpose: 'p', status: 2, copies: 2, companies: [] },
  { id: 1, code: 'DD-1', title: '', purpose: 'Biên bản bàn giao', status: 3, copies: 1, companies: [] },
] as unknown as SealRequest[]

vi.mock('../hooks/use-seal-requests', () => ({
  useSealRequests: (params: Record<string, unknown>) => {
    listCalls.push(params)
    return { data: { total: rows.length, items: rows }, isLoading: false, isError: false }
  },
}))

vi.mock('@/modules/hr/hooks/use-companies', () => ({
  useCompanies: () => ({ data: { total: 0, items: [] } }),
}))
vi.mock('@/modules/hr/hooks/use-departments', () => ({
  useDepartments: () => ({ data: { total: 0, items: [] } }),
}))
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAccess: () => true }),
}))

function renderPage(url = '/approval-seal/requests') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <TooltipProvider>
          <SealRequestListPage />
        </TooltipProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function lastCall() {
  return listCalls[listCalls.length - 1]
}

function header(text: string) {
  return screen.getByText(text, { selector: 'thead span' })
}

beforeEach(() => {
  listCalls.length = 0
})

describe('SealRequestListPage - sắp xếp cột (duoc-CR-744)', () => {
  it('sends sort_by for every sortable header, using the column key', async () => {
    const user = userEvent.setup()
    renderPage()

    const cases: [string, string][] = [
      ['Mã phiếu', 'code'],
      ['Văn bản / Mục đích', 'purpose'],
      ['Công ty đóng dấu', 'company_name'],
      ['Số bản', 'copies'],
      ['Người tạo', 'requester'],
      ['Trạng thái', 'status'],
      ['Ngày tạo', 'created_at'],
    ]
    for (const [text, key] of cases) {
      await user.click(header(text))
      expect(lastCall().sort_by, text).toBe(key)
      expect(lastCall().sort_dir, text).toBe('asc')
    }
  })

  it('cycles asc -> desc -> no sort, dropping both params on the third click', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.click(header('Văn bản / Mục đích'))
    await user.click(header('Văn bản / Mục đích'))
    expect(lastCall()).toMatchObject({ sort_by: 'purpose', sort_dir: 'desc' })
    await user.click(header('Văn bản / Mục đích'))
    expect(lastCall().sort_by).toBeUndefined()
    expect(lastCall().sort_dir).toBeUndefined()
  })

  it('restores the sort from the URL on first render', () => {
    renderPage('/approval-seal/requests?sort_by=requester&sort_dir=desc')
    expect(lastCall()).toMatchObject({ sort_by: 'requester', sort_dir: 'desc' })
  })

  it('goes back to page 1 when the sort changes', async () => {
    const user = userEvent.setup()
    renderPage()
    await user.click(header('Trạng thái'))
    expect(lastCall().page).toBe(1)
  })
})
