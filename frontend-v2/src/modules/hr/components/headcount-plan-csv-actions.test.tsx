import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'

import { HeadcountPlanCsvActions } from './headcount-plan-csv-actions'

const downloadFile = vi.fn()
let granted: string[] = []

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return {
    ...actual,
    downloadFile: (...args: unknown[]) => downloadFile(...args),
  }
})
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (entity: string, action: string) => granted.includes(`${entity}.${action}`) }),
}))
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

function build(url = '/hr/headcount-plans') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <HeadcountPlanCsvActions />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  downloadFile.mockReset().mockResolvedValue(undefined)
  granted = []
})

describe('HeadcountPlanCsvActions', () => {
  it('renders nothing for a read-only viewer', () => {
    granted = ['headcount_plan.read']
    const { container } = build()
    expect(container).toBeEmptyDOMElement()
  })

  it('exports exactly the filters on screen, keeping the real 0 and dropping "all" and paging', async () => {
    granted = ['headcount_plan.export']
    build('/hr/headcount-plans?year=2026&period_type=3&company_id=all&department_id=0&page=3')
    fireEvent.click(screen.getByRole('button', { name: /Xuất CSV/ }))
    await vi.waitFor(() => expect(downloadFile).toHaveBeenCalled())
    expect(downloadFile).toHaveBeenCalledWith('/api/headcount-plans/export/csv', 'ke-hoach-nhan-su.csv', {
      year: '2026',
      period_type: '3',
      department_id: '0',
    })
  })

  it('no longer offers the old one-row-per-plan CSV import — lines are imported inside each plan', () => {
    //  Backend bỏ `POST /api/headcount-plans/import/csv` ở gốc (duoc-CR-690); nút cũ còn thì bấm ra 404.
    granted = ['headcount_plan.export', 'headcount_plan.create', 'headcount_plan.write']
    build()
    expect(screen.queryByRole('button', { name: /Nhập CSV/ })).not.toBeInTheDocument()
  })

  it('downloads only once on a double click', async () => {
    granted = ['headcount_plan.export']
    let release: () => void = () => undefined
    downloadFile.mockReturnValue(new Promise<void>((r) => (release = r)))
    build()
    const btn = screen.getByRole('button', { name: /Xuất CSV/ })
    fireEvent.click(btn)
    fireEvent.click(btn)
    release()
    await vi.waitFor(() => expect(downloadFile).toHaveBeenCalledTimes(1))
  })
})
