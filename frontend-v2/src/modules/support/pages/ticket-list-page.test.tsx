import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ListParams } from '@/shared/types/api'
import { TicketListPage } from './ticket-list-page'

/**
 * duoc-CR-744 — bấm tiêu đề cột Phiếu hỗ trợ phải gửi `sort_by` lên server. Trước đây không cột nào khai
 * `sortable` nên bấm không có gì xảy ra, dù backend đã đọc `sort_by`.
 */
const calls: ListParams[] = []
let isHandler = true

vi.mock('../hooks/use-tickets', () => ({
  useTickets: (params: ListParams) => {
    calls.push(params)
    return { data: { total: 0, items: [] }, isLoading: false, isError: false, refetch: vi.fn() }
  },
  useTakeTicket: () => ({ mutate: vi.fn(), isPending: false }),
}))
vi.mock('@/core/auth/use-auth', () => ({ useAuth: () => ({ user: { id: 1 } }) }))
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => isHandler, canAccess: () => true }),
}))
vi.mock('@/app/components/profile/create-ticket-dialog', () => ({ CreateTicketDialog: () => null }))

function build(url = '/support/tickets') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <TicketListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const header = (text: string) => screen.getByText(text, { selector: 'thead span' })
const last = () => calls[calls.length - 1]

beforeEach(() => {
  calls.length = 0
  isHandler = true
})

describe('TicketListPage — sắp xếp cột (duoc-CR-744)', () => {
  it('sends the column key as sort_by for every data column', async () => {
    const user = userEvent.setup()
    build()

    const cases: [string, string][] = [
      ['Chủ đề', 'subject'],
      ['Người gửi', 'requester_name'],
      ['Bộ phận', 'department'],
      ['Ưu tiên', 'priority'],
      ['Trạng thái', 'status'],
      ['Người xử lý', 'assignee_name'],
      ['Cập nhật', 'updated_at'],
    ]
    for (const [text, key] of cases) {
      await user.click(header(text))
      expect(last().sort_by, text).toBe(key)
    }
  })

  it('asks for the most urgent / newest first on the first click of Ưu tiên and Cập nhật', async () => {
    const user = userEvent.setup()
    build()

    await user.click(header('Ưu tiên'))
    expect(last()).toMatchObject({ sort_by: 'priority', sort_dir: 'desc' })
    await user.click(header('Cập nhật'))
    expect(last()).toMatchObject({ sort_by: 'updated_at', sort_dir: 'desc' })
    await user.click(header('Chủ đề'))
    expect(last()).toMatchObject({ sort_by: 'subject', sort_dir: 'asc' })
  })

  it('cycles asc -> desc -> off and drops both params on the third click', async () => {
    const user = userEvent.setup()
    build()

    await user.click(header('Người xử lý'))
    expect(last()).toMatchObject({ sort_by: 'assignee_name', sort_dir: 'asc', page: 1 })
    await user.click(header('Người xử lý'))
    expect(last()).toMatchObject({ sort_by: 'assignee_name', sort_dir: 'desc' })
    await user.click(header('Người xử lý'))
    expect(last().sort_by).toBeUndefined()
    expect(last().sort_dir).toBeUndefined()
  })

  it('goes back to page 1 and keeps the other filters when the sort changes', async () => {
    const user = userEvent.setup()
    build('/support/tickets?status=open&sort_by=status&sort_dir=asc')

    expect(last()).toMatchObject({ status: 'open', sort_by: 'status', sort_dir: 'asc' })
    await user.click(header('Bộ phận'))
    expect(last()).toMatchObject({ status: 'open', sort_by: 'department', page: 1 })
  })

  it('restores the sort from the URL (shareable link)', () => {
    build('/support/tickets?sort_by=priority&sort_dir=desc')
    expect(last()).toMatchObject({ sort_by: 'priority', sort_dir: 'desc' })
  })
})
