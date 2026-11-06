import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { AvailableSurveyLine, SurveyRequestProcess } from '../types/survey-request-process'
import { SurveyRequestProcessCard } from './survey-request-process-card'

/**
 * duoc-CR-738 — bảng *Kết quả khảo sát đã duyệt* ở màn Xử lý khảo sát (YCBG) bấm tiêu đề cột
 * là sắp phía server như bản v1. Chặn ở tầng `@/core/api` (hook thật) để soi đúng bộ tham số
 * đi ra đường `available-survey-lines`: có `sort_by` / `sort_dir`, trang về 1, bộ lọc giữ nguyên.
 */

const availableCalls: Record<string, unknown>[] = []
let availableTotal = 20

vi.mock('@/core/api', async (importOriginal) => ({
  ...(await importOriginal<Record<string, unknown>>()),
  apiGet: (url: string, config?: { params?: Record<string, unknown> }) => {
    if (url.endsWith('/process')) return Promise.resolve(buildProcess())
    if (url.includes('/available-survey-lines')) {
      availableCalls.push({ ...(config?.params ?? {}) })
      return Promise.resolve({ items: [buildAvailable()], total: availableTotal })
    }
    return Promise.resolve({ items: [], total: 0 })
  },
}))

vi.mock('@/modules/production/hooks/use-suppliers', () => ({
  useSuppliers: () => ({ data: { items: [] } }),
}))

vi.mock('../hooks/use-purchase-request-support', () => ({
  usePurchaseRequestItemGroups: () => ({ data: { items: [] } }),
  usePurchaseRequestProducts: () => ({ data: { items: [] }, isLoading: false, isError: false }),
}))

function buildProcess(): SurveyRequestProcess {
  return {
    id: 28,
    code: 'YCBG28082601',
    status: 'processing',
    request_date: '2026-08-28',
    department: 'Marketing',
    requester: 'Nguyễn Văn A',
    company_id: 1,
    lines: [
      {
        id: 301,
        internal_line_code: 'L1',
        item_group: 'Bao bì',
        requirement_detail: 'Thùng carton',
        other_requirement: '',
        request_qty: 100,
        uom: 'Cái',
        proposed_price: 0,
        assignee: 'NSTM01',
        assignee_name: 'NSTM 01',
        is_completed: false,
        no_option: false,
        options: [],
        can_process: true,
      },
    ],
  }
}

function buildAvailable(): AvailableSurveyLine {
  return {
    id: 900,
    supplier_code: 'NCC-A',
    supplier_name: 'CÔNG TY A',
    internal_code: 'A-01',
    product_name: 'Thùng carton 5 lớp',
    spec: '',
    origin: 'VN',
    quote_unit: 'Cái',
    moq: 100,
    price_by_volume: 12000,
    volume_range: '',
    vat: 8,
    delivery_time: '',
    delivery_place: '',
    shipping_cost: 0,
    sample_ready: false,
    lab_result: '',
    survey_item_group: 'Bao bì',
    survey_code: 'KS-0042',
    survey_item_code: 'VTBB-1',
    result_date: '2026-10-02',
  }
}

function renderCard() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <SurveyRequestProcessCard surveyRequestId={28} status="processing" />
    </QueryClientProvider>,
  )
}

const lastCall = () => availableCalls[availableCalls.length - 1]

beforeEach(() => {
  availableCalls.length = 0
  availableTotal = 20
  window.localStorage.clear()
})

describe('SurveyRequestProcessCard — sắp xếp bảng kết quả khảo sát', () => {
  it('sends no sort params until a header is clicked, so the backend keeps newest first', async () => {
    renderCard()
    await screen.findByText('CÔNG TY A')
    expect(lastCall()).not.toHaveProperty('sort_by')
    expect(lastCall()).not.toHaveProperty('sort_dir')
  })

  it('sorts by the backend key of the clicked column and goes back to page 1, keeping filters', async () => {
    const user = userEvent.setup()
    renderCard()
    await screen.findByText('CÔNG TY A')

    //  Lật sang trang 2 trước — đổi sắp xếp mà giữ trang cũ là xem nhầm khúc giữa danh sách mới.
    await user.click(screen.getByRole('button', { name: 'Trang sau' }))
    await waitFor(() => expect(lastCall()).toMatchObject({ page: 2 }))

    await user.click(screen.getByText('Đơn giá'))
    await waitFor(() =>
      expect(lastCall()).toMatchObject({
        sort_by: 'price_by_volume',
        sort_dir: 'asc',
        page: 1,
        item_group: ['Bao bì'],
      }),
    )

    await user.click(screen.getByText('Đơn giá'))
    await waitFor(() => expect(lastCall()).toMatchObject({ sort_by: 'price_by_volume', sort_dir: 'desc' }))

    //  Nhịp thứ ba thôi sắp xếp: không gửi `sort_by` nữa, backend về mặc định.
    await user.click(screen.getByText('Đơn giá'))
    await waitFor(() => expect(lastCall()).not.toHaveProperty('sort_by'))
  })

  it('maps the NCC column to supplier_code and starts the survey date column at newest first', async () => {
    const user = userEvent.setup()
    renderCard()
    await screen.findByText('CÔNG TY A')

    await user.click(screen.getByText('NCC'))
    await waitFor(() => expect(lastCall()).toMatchObject({ sort_by: 'supplier_code', sort_dir: 'asc' }))

    await user.click(screen.getByText('Ngày KS'))
    await waitFor(() => expect(lastCall()).toMatchObject({ sort_by: 'result_date', sort_dir: 'desc' }))
  })

  it('does not sort by columns the backend cannot order (Phân loại KS, Phiếu KS)', async () => {
    const user = userEvent.setup()
    renderCard()
    await screen.findByText('CÔNG TY A')
    const callsBefore = availableCalls.length

    await user.click(screen.getByText('Phân loại KS'))
    await user.click(screen.getByText('Phiếu KS'))

    expect(availableCalls.length).toBe(callsBefore)
    expect(lastCall()).not.toHaveProperty('sort_by')
  })
})
