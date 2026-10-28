import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'

import { HeadcountPlanCsvActions } from './headcount-plan-csv-actions'

const downloadFile = vi.fn()
const httpPost = vi.fn()
let granted: string[] = []

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return {
    ...actual,
    downloadFile: (...args: unknown[]) => downloadFile(...args),
    httpClient: { post: (...args: unknown[]) => httpPost(...args) },
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
  httpPost.mockReset()
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
    build('/hr/headcount-plans?year=2026&company_id=all&department_id=0&page=3')
    fireEvent.click(screen.getByRole('button', { name: /Xuất CSV/ }))
    await vi.waitFor(() => expect(downloadFile).toHaveBeenCalled())
    expect(downloadFile).toHaveBeenCalledWith('/api/headcount-plans/export/csv', 'ke-hoach-nhan-su.csv', {
      year: '2026',
      department_id: '0',
    })
    expect(screen.queryByRole('button', { name: /Nhập CSV/ })).not.toBeInTheDocument()
  })

  it('hides import unless the viewer can both create and update — the backend asks for both', () => {
    granted = ['headcount_plan.create']
    const { container } = build()
    expect(container).toBeEmptyDOMElement()
  })

  it('lists every rejected CSV row in a dialog — nothing was written', async () => {
    granted = ['headcount_plan.create', 'headcount_plan.write']
    httpPost.mockRejectedValue({
      response: { data: { success: false, error: { message: 'Tệp CSV có lỗi, chưa ghi dòng nào: Dòng 2: mã pháp nhân không tồn tại | Dòng 4: trùng' } } },
    })
    build()
    const input = screen.getByLabelText('Chọn tệp CSV kế hoạch nhân sự')
    fireEvent.change(input, { target: { files: [new File(['year\n'], 'kh.csv', { type: 'text/csv' })] } })
    expect(await screen.findByText('Chưa nhập được tệp')).toBeInTheDocument()
    expect(screen.getByText('Dòng 2: mã pháp nhân không tồn tại')).toBeInTheDocument()
    expect(screen.getByText('Dòng 4: trùng')).toBeInTheDocument()
    expect(httpPost.mock.calls[0]?.[0]).toBe('/api/headcount-plans/import/csv')
  })
})
