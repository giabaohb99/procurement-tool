import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type * as ReactRouterModule from 'react-router-dom'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

type ReactRouter = typeof ReactRouterModule

import type {
  SurveyRequestPrint,
  SurveyRequestPrintLine,
} from '../types/survey-request-detail'
import { SurveyRequestPrintPage } from './survey-request-print-page'

const printData = vi.hoisted(() => ({ current: null as unknown }))

vi.mock('../hooks/use-survey-request', () => ({
  useSurveyRequestPrint: () => ({
    data: printData.current,
    isLoading: false,
    isError: printData.current === null,
  }),
}))

vi.mock('@/modules/hr/hooks/use-companies', () => ({
  useCompanies: () => ({
    data: { items: [{ id: 1, name: 'CÔNG TY TNHH DEGO HOLDING' }] },
  }),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<ReactRouter>('react-router-dom')
  return { ...actual, useParams: () => ({ id: '2930' }) }
})

function makeLine(overrides: Partial<SurveyRequestPrintLine> = {}): SurveyRequestPrintLine {
  return {
    id: 1,
    internal_line_code: '',
    item_group: 'Bao bì',
    requirement_detail: 'Thùng carton 3 lớp',
    other_requirement: 'in 1 màu logo',
    request_qty: 500,
    uom: 'cái',
    proposed_price: 11000,
    product_code: 'SPDEMO01',
    received_date: '',
    result_due_date: '',
    result_date: '',
    assignee: '',
    assignee_name: '',
    pr_id: 0,
    pr_code: '',
    po_id: 0,
    po_code: '',
    is_completed: false,
    line_status: 'confirmed',
    no_option: false,
    option_count: 1,
    has_chosen: true,
    progress_state: '',
    progress_tone: '',
    print_supplier_name: 'Công ty CP Bao Bì Demo A',
    print_supplier_source: 'confirmed',
    chosen_price: 12000,
    chosen_vat: 8,
    chosen_delivery_time: '5 ngày',
    warehouse: 'Kho A',
    required_date: '',
    vat_pct: 8,
    // bao-CR-289: bốn trường tiến độ mới trên dòng — bản in kế thừa từ SurveyRequestLine.
    qty_ordered: 0,
    qty_received: 0,
    expected_date: '',
    progress_note: '',
    purchaser_note: '',
    ...overrides,
  }
}

function makeData(overrides: Partial<SurveyRequestPrint> = {}): SurveyRequestPrint {
  return {
    id: 2930,
    code: 'YCBG-DEMO-P6',
    company_id: 1,
    requester: 'Nguyễn Văn Yêu Cầu',
    requester_id: 5,
    requester_position: 'Nhân viên',
    department_id: 1,
    department: 'Phòng Demo Thu Mua',
    head_of_dept_id: 2,
    head_of_dept: 'Trần Trưởng Phòng',
    purpose: 'Data demo luồng gộp P6',
    request_date: '2026-09-04',
    status: 'survey_done',
    note: 'Phiếu demo, xóa thoải mái.',
    reject_reason: '',
    is_urgent: false,
    suggested_supplier: 'Công ty TNHH Bao Bì Miền Tây',
    suggested_supplier_tax_code: '1801234567',
    suggested_supplier_contact: 'Anh Tú — 0909 123 456',
    created_at: '2026-09-04T08:00:00',
    created_by: 5,
    merged_flow_enabled: true,
    lines: [
      makeLine(),
      // Dòng CHƯA chốt: in giá đề xuất, KHÔNG được sinh thêm dấu (*) hay chú thích.
      makeLine({
        id: 2,
        requirement_detail: 'Túi niêm phong an ninh 20x30',
        other_requirement: '',
        request_qty: 1000,
        uom: 'cái',
        proposed_price: 1500,
        product_code: '',
        line_status: '',
        has_chosen: true,
        print_supplier_name: 'Công ty TNHH Bao Bì Miền Tây',
        print_supplier_source: 'requester',
        chosen_price: 0,
        chosen_vat: 0,
        chosen_delivery_time: '',
        warehouse: '',
        vat_pct: 8,
      }),
    ],
    ...overrides,
  }
}

function renderPage(data: SurveyRequestPrint | null) {
  printData.current = data
  return render(
    <MemoryRouter>
      <SurveyRequestPrintPage />
    </MemoryRouter>,
  )
}

/**
 * bao-CR-288: bản in này là MẪU KẾ TOÁN 003/BM/PKT — chuẩn chứng từ đi thanh toán,
 * khách chốt 04/09/2026 "không được sai chữ nào". Bộ test này KHÓA nguyên văn các
 * nhãn của mẫu; sửa chữ trên form phải có khách duyệt trước, đừng sửa test cho qua.
 */
describe('SurveyRequestPrintPage — mẫu 003/BM/PKT', () => {
  it('renders every fixed label of the accounting form, word for word', () => {
    renderPage(makeData())

    expect(screen.getByText('PHIẾU ĐỀ XUẤT MUA HÀNG HÓA/DỊCH VỤ')).toBeInTheDocument()
    expect(screen.getByText('Mẫu 003/BM/PKT')).toBeInTheDocument()
    expect(screen.getByText('V1-062025')).toBeInTheDocument()

    expect(screen.getByText('THÔNG TIN CHUNG')).toBeInTheDocument()
    expect(screen.getByText('MỤC ĐÍCH & NỘI DUNG ĐỀ XUẤT')).toBeInTheDocument()
    expect(screen.getByText('NHÀ CUNG CẤP DO BỘ PHẬN ĐỀ XUẤT')).toBeInTheDocument()
    expect(screen.getByText('PHẦN DÀNH CHO BỘ PHẬN MUA HÀNG')).toBeInTheDocument()
    expect(screen.getByText('XÉT DUYỆT')).toBeInTheDocument()

    expect(screen.getByText('Người đề xuất:')).toBeInTheDocument()
    expect(screen.getByText('Mục đích mua hàng/dịch vụ:')).toBeInTheDocument()
    expect(screen.getAllByText('Thời gian cần hàng/dịch vụ:')).toHaveLength(2)
    expect(screen.getByText('Báo giá đính kèm:')).toBeInTheDocument()

    for (const label of ['Giám đốc', 'TP/BP mua hàng', 'TP/BP đề xuất', 'Người lập']) {
      expect(screen.getByText(label)).toBeInTheDocument()
    }
    expect(screen.getByText('Phiếu đề xuất này được in từ hệ thống thu mua')).toBeInTheDocument()
  })

  it('keeps the exact 9 item columns of the form — no NCC or delivery column added', () => {
    renderPage(makeData())

    const headers = screen.getAllByRole('columnheader').map((cell) => cell.textContent)
    expect(headers).toEqual([
      'STT',
      'Tên hàng hóa/dịch vụ',
      'Mã hàng',
      'ĐVT',
      'Số lượng',
      'Đơn giá',
      'Thành tiền',
      'Nơi giao',
      'Ghi chú',
    ])
  })

  it('adds no asterisk footnote and leaks no surveyed supplier name into the form', () => {
    const { container } = renderPage(makeData())

    // Soi riêng tờ phiếu (thẻ <article>): textContent của cả trang dính CSS trong
    // <style> vốn có dấu * của selector, không phải chữ in ra giấy.
    const doc = container.querySelector('article')
    expect(doc).not.toBeNull()
    // Lỗi bị khách bắt 04/09/2026: bản đầu tự chế dòng "(*) Dòng chưa chốt phương án..."
    // và dấu * cạnh giá — mẫu chung không có, cấm thêm lại.
    expect(doc?.textContent).not.toContain('*')
    // Mẫu không có cột NCC trên dòng hàng nên tên NCC khảo sát không được xuất hiện.
    expect(doc?.textContent).not.toContain('Công ty CP Bao Bì Demo A')
  })

  it('sums VAT from chosen VAT of confirmed lines and requester VAT of open lines', () => {
    renderPage(makeData())

    // 500 x 12.000 (giá chốt) + 1.000 x 1.500 (giá đề xuất) = 7.500.000
    expect(screen.getByText('7.500.000')).toBeInTheDocument()
    expect(screen.getByText('Tiền VAT:')).toBeInTheDocument()
    // VAT 8% cả hai dòng: 480.000 + 120.000 = 600.000; tổng thanh toán 8.100.000.
    expect(screen.getByText('600.000')).toBeInTheDocument()
    expect(screen.getByText('Tổng cộng thanh toán (gồm VAT):')).toBeInTheDocument()
    expect(screen.getByText('8.100.000')).toBeInTheDocument()
  })

  it('blanks the requester block when switching to "Mẫu thuế"', async () => {
    const user = userEvent.setup()
    renderPage(makeData())

    expect(screen.getAllByText('Nguyễn Văn Yêu Cầu')).not.toHaveLength(0)
    await user.click(screen.getByRole('button', { name: 'Mẫu thuế' }))
    expect(screen.queryByText('Nguyễn Văn Yêu Cầu')).not.toBeInTheDocument()
  })
})
