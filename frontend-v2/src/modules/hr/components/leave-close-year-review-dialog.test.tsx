import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render as rtlRender, screen } from '@testing-library/react'
import type { ReactElement } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { LeaveCloseYearReview } from '../types/leave'
import { LeaveCloseYearReviewDialog } from './leave-close-year-review-dialog'

const state = vi.hoisted(() => ({
  data: undefined as LeaveCloseYearReview | undefined,
  canExport: true,
}))

vi.mock('../hooks/use-leave', () => ({
  useCloseYearReview: () => ({ data: state.data, isLoading: false, isError: false }),
}))
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (_e: string, a: string) => a !== 'export' || state.canExport }),
}))
vi.mock('@/core/api', () => ({ downloadFile: vi.fn() }))

//  DataTable có nút «Tải lại» dùng QueryClient nên phải bọc provider.
const render = (ui: ReactElement) =>
  rtlRender(<QueryClientProvider client={new QueryClient()}>{ui}</QueryClientProvider>)

const review = (): LeaveCloseYearReview => ({
  year: 2026,
  next_year: 2027,
  items: [
    {
      employee_id: 1, employee_code: 'NV001', employee_name: 'An',
      source_type_id: 1, source_type_name: 'Phép năm', dest_type_id: 1, dest_type_name: 'Phép năm',
      ratio: 1, before_days: 8, after_days: 3, diff_days: -5, credited_days: 5, dest_carried_days: 5,
    },
  ],
  totals: { row_count: 1, before_days: 8, after_days: 3, diff_days: -5, credited_days: 5 },
})

beforeEach(() => {
  state.data = review()
  state.canExport = true
})

describe('LeaveCloseYearReviewDialog', () => {
  it('shows old, new and diff numbers per person plus a totals line', () => {
    render(<LeaveCloseYearReviewDialog year={2026} onClose={() => {}} />)
    expect(screen.getByText('An (NV001)')).toBeInTheDocument()
    expect(screen.getByText(/Tổng 1 dòng: số cũ 8 → số mới 3 \(chênh -5\)/)).toBeInTheDocument()
  })

  it('offers Excel export only with the export permission', () => {
    const first = render(<LeaveCloseYearReviewDialog year={2026} onClose={() => {}} />)
    expect(screen.getByRole('button', { name: /Xuất Excel/ })).toBeEnabled()
    first.unmount()
    state.canExport = false
    render(<LeaveCloseYearReviewDialog year={2026} onClose={() => {}} />)
    expect(screen.queryByRole('button', { name: /Xuất Excel/ })).not.toBeInTheDocument()
  })

  it('disables export and explains when nothing was closed for that year', () => {
    state.data = { year: 2026, next_year: 2027, items: [],
      totals: { row_count: 0, before_days: 0, after_days: 0, diff_days: 0, credited_days: 0 } }
    render(<LeaveCloseYearReviewDialog year={2026} onClose={() => {}} />)
    expect(screen.getByRole('button', { name: /Xuất Excel/ })).toBeDisabled()
    expect(screen.getByText(/Chưa có dòng nào được kết sổ cho năm 2026/)).toBeInTheDocument()
  })

  it('renders nothing while closed', () => {
    render(<LeaveCloseYearReviewDialog year={null} onClose={() => {}} />)
    expect(screen.queryByText(/Đối chiếu kết sổ phép/)).not.toBeInTheDocument()
  })
})
