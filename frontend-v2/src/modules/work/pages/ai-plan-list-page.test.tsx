import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AiPlanListPage } from './ai-plan-list-page'

const apiGet = vi.fn()
vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: vi.fn(),
  apiPut: vi.fn(),
}))
vi.mock('../components/work-sidebar-peek-button', () => ({ WorkSidebarPeekButton: () => null }))

function build(url = '/project/ai-plans') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[url]}>
        <AiPlanListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function lastParams() {
  const calls = apiGet.mock.calls.filter(([url]) => url === '/api/ai-plans')
  return (calls.at(-1)?.[1] as { params: Record<string, unknown> } | undefined)?.params
}

beforeEach(() => {
  localStorage.clear()
  apiGet.mockReset().mockResolvedValue({
    total: 1,
    items: [
      {
        id: 5,
        status: 1,
        status_label: 'Chờ duyệt',
        title: 'Tiếp khách',
        deadline: '2026-10-30',
        channel_label: 'Web',
        counts: { phases: 2, tasks: 7, subtasks: 0 },
        created_at: '2026-10-22T09:00:00',
        list_id: 0,
        list_url: null,
      },
    ],
  })
})

describe('AiPlanListPage', () => {
  it('opens on the plans waiting for my approval', async () => {
    build()
    await screen.findAllByText('Tiếp khách')
    expect(lastParams()).toMatchObject({ status: 1, page: 1 })
  })

  it('sends no status at all when "Tất cả" is picked from the URL', async () => {
    build('/project/ai-plans?status=all')
    await waitFor(() => expect(lastParams()).toBeDefined())
    expect(lastParams()?.status).toBeUndefined()
  })

  it('describes the size without the zero parts', async () => {
    build()
    expect((await screen.findAllByText('2 giai đoạn · 7 việc')).length).toBeGreaterThan(0)
  })
})
