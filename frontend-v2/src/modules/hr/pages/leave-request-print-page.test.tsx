import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type * as CoreApiModule from '@/core/api'
import type * as ReactRouterModule from 'react-router-dom'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

type ReactRouter = typeof ReactRouterModule

import type { LeaveAttachment } from '../api/leave-attachment-api'
import { LEAVE_SESSION, LEAVE_STATUS, type LeaveRequest } from '../types/leave'
import { LeaveRequestPrintPage } from './leave-request-print-page'

const testRequest = vi.hoisted(() => ({ current: null as LeaveRequest | null }))
const testAttachments = vi.hoisted(() => ({ current: [] as LeaveAttachment[] }))
const fetchBlobUrl = vi.hoisted(() => vi.fn<(url: string) => Promise<string>>())

vi.mock('../hooks/use-leave', () => ({
  useLeaveRequest: () => ({
    data: testRequest.current,
    isLoading: false,
  }),
}))

vi.mock('../hooks/use-leave-attachments', () => ({
  useLeaveAttachments: () => ({ data: testAttachments.current, isLoading: false }),
}))

//  Mock ở tầng `@/core/api` (luật testing.md) — hook nạp ảnh chạy THẬT.
vi.mock('@/core/api', async (importOriginal) => ({
  ...(await importOriginal<typeof CoreApiModule>()),
  fetchBlobUrl,
}))

function attachment(id: number, filename: string, content_type: string): LeaveAttachment {
  return { id, file_id: id, filename, url: '', content_type, size: 1 }
}

beforeEach(() => {
  testAttachments.current = []
  fetchBlobUrl.mockReset()
  //  jsdom không có `URL.revokeObjectURL` — hook gọi nó lúc rời trang.
  URL.revokeObjectURL = vi.fn()
})

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<ReactRouter>('react-router-dom')
  return {
    ...actual,
    useParams: () => ({ id: '10' }),
  }
})

function mockRequest(overrides: Partial<LeaveRequest> = {}): LeaveRequest {
  return {
    id: 10,
    code: 'NP-2026-0010',
    company_id: 1,
    department_id: 2,
    department_name: 'Lập trình & IT nội bộ',
    employee_id: 3,
    employee_name: 'Phạm Lê Triết Giang',
    employee_position: 'Chuyên viên',
    leave_type_id: 1,
    leave_type_name: 'Phép năm',
    from_date: '2026-06-09',
    to_date: '2026-06-09',
    from_session: LEAVE_SESSION.FULL,
    to_session: LEAVE_SESSION.FULL,
    unit: 1,
    total_days: 1,
    reason: 'Em xin phép nghỉ 1 ngày để đưa vợ con về Châu Đốc',
    contact_phone: '0973555582',
    contact_address: 'Cần Thơ',
    status: LEAVE_STATUS.APPROVED,
    approval_instance_id: 5,
    document_id: 0,
    decision_note: '',
    decided_by_name: 'Trần Quang Phú',
    decided_at: '2026-06-09T08:00:00',
    handovers: [],
    ...overrides,
  }
}

/** Ô vuông (checkbox in ra giấy) của một dòng loại hình nghỉ. */
function boxOf(label: RegExp) {
  return within(screen.getByRole('row', { name: label })).getByRole('img')
}

describe('LeaveRequestPrintPage', () => {
  //  06/10/2026 — mẫu Word 2026 «ĐƠN XIN NGHỈ PHÉP / NGHỈ CHẾ ĐỘ»: Quốc hiệu thay logo, ba mục
  //  đánh số, ba ô loại hình nghỉ, hai ô ký. Mẫu cũ (logo + ba cột ký có P.HCNS) không còn.
  it('renders the 2026 leave form with national header, three numbered sections and two signatures', () => {
    testRequest.current = mockRequest({ company_name: 'Công ty CP DEGO Holding' })
    render(
      <MemoryRouter>
        <LeaveRequestPrintPage />
      </MemoryRouter>,
    )

    expect(screen.getByText('CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM')).toBeInTheDocument()
    expect(screen.getByText('Độc lập - Tự do - Hạnh phúc')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'ĐƠN XIN NGHỈ PHÉP / NGHỈ CHẾ ĐỘ' })).toBeInTheDocument()
    expect(screen.queryByAltText('DEGO HOLDING')).not.toBeInTheDocument()
    expect(screen.getByText(/Cần Thơ, ngày 09 tháng 06 năm 2026/)).toBeInTheDocument()

    // Kính gửi
    expect(screen.getByText('- Ban Giám đốc Công ty CP DEGO Holding')).toBeInTheDocument()
    expect(screen.getByText('- Bộ phận Nhân sự')).toBeInTheDocument()
    expect(screen.getByText('- Trưởng bộ phận: Lập trình & IT nội bộ')).toBeInTheDocument()

    // Ba mục
    expect(screen.getByRole('heading', { name: '1. Thông tin nhân sự' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '2. Nội dung xin nghỉ' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '3. Bàn giao công việc' })).toBeInTheDocument()

    // Thông tin nhân sự: tên ở bảng + ô ký
    expect(screen.getAllByText(/Phạm Lê Triết Giang/)).toHaveLength(2)
    expect(screen.getByText(/Chuyên viên/)).toBeInTheDocument()

    // Nội dung nghỉ
    expect(screen.getByText(/Từ ngày 09\/06\/2026 đến hết ngày 09\/06\/2026/)).toBeInTheDocument()
    expect(screen.getByText(/1 ngày\./)).toBeInTheDocument()
    expect(
      screen.getByText(/Em xin phép nghỉ 1 ngày để đưa vợ con về Châu Đốc/),
    ).toBeInTheDocument()

    // Bàn giao trống vẫn phải nói thành lời (luật hr-leave)
    expect(
      screen.getByText(/Cá nhân tự sắp xếp công việc\. Team hỗ trợ công việc/),
    ).toBeInTheDocument()

    // Hai ô ký, không còn P.HCNS
    expect(screen.getByText('NGƯỜI XIN NGHỈ')).toBeInTheDocument()
    expect(screen.getByText('TRƯỞNG BỘ PHẬN')).toBeInTheDocument()
    expect(screen.getByText('Trần Quang Phú')).toBeInTheDocument()
    expect(screen.queryByText('P.HCNS')).not.toBeInTheDocument()
  })

  it('ticks only the paid-leave box for an annual leave request', () => {
    testRequest.current = mockRequest()
    render(
      <MemoryRouter>
        <LeaveRequestPrintPage />
      </MemoryRouter>,
    )
    expect(boxOf(/Nghỉ phép năm \(có lương\)/)).toHaveAccessibleName('Đã đánh dấu')
    expect(boxOf(/Nghỉ việc riêng/)).toHaveAccessibleName('Chưa đánh dấu')
    expect(boxOf(/Nghỉ chế độ bảo hiểm/)).toHaveAccessibleName('Chưa đánh dấu')
  })

  //  Tên mẫu tệp Word là «Chế độ thai sản» — nghỉ thai sản phải rơi đúng ô bảo hiểm.
  it('ticks the insurance box for a maternity leave and leaves annual leave unticked', () => {
    testRequest.current = mockRequest({ leave_type_name: 'Nghỉ thai sản', total_days: 180 })
    render(
      <MemoryRouter>
        <LeaveRequestPrintPage />
      </MemoryRouter>,
    )
    expect(boxOf(/Nghỉ chế độ bảo hiểm/)).toHaveAccessibleName('Đã đánh dấu')
    expect(boxOf(/Nghỉ phép năm/)).toHaveAccessibleName('Chưa đánh dấu')
  })

  it('names the handover person with what they take over', () => {
    testRequest.current = mockRequest({
      handovers: [
        { id: 1, employee_id: 7, employee_name: 'Lê Văn A', content: 'Duyệt YCMH', sort_order: 1 },
      ],
    })
    render(
      <MemoryRouter>
        <LeaveRequestPrintPage />
      </MemoryRouter>,
    )
    expect(screen.getByText(/Lê Văn A \(Duyệt YCMH\)/)).toBeInTheDocument()
    expect(screen.queryByText(/Cá nhân tự sắp xếp/)).not.toBeInTheDocument()
  })

  it('shows the half-day session and the hour range next to the dates', () => {
    testRequest.current = mockRequest({
      from_session: LEAVE_SESSION.AFTERNOON,
      to_session: LEAVE_SESSION.AFTERNOON,
      total_days: 0.5,
    })
    const { unmount } = render(
      <MemoryRouter>
        <LeaveRequestPrintPage />
      </MemoryRouter>,
    )
    expect(screen.getByText(/Từ ngày 09\/06\/2026 \(buổi chiều\) đến hết ngày 09\/06\/2026 \(buổi chiều\)/)).toBeInTheDocument()
    unmount()

    testRequest.current = mockRequest({
      from_session: LEAVE_SESSION.HOURLY,
      to_session: LEAVE_SESSION.HOURLY,
      from_time: '08:00:00',
      to_time: '10:30:00',
      total_days: 0.25,
    })
    render(
      <MemoryRouter>
        <LeaveRequestPrintPage />
      </MemoryRouter>,
    )
    expect(screen.getByText(/Từ ngày 09\/06\/2026 \(08:00 - 10:30\) đến hết ngày 09\/06\/2026$/)).toBeInTheDocument()
  })

  it('triggers window.print when clicking In đơn button', async () => {
    const user = userEvent.setup()
    const printSpy = vi.spyOn(window, 'print').mockImplementation(() => {})

    testRequest.current = mockRequest()
    render(
      <MemoryRouter>
        <LeaveRequestPrintPage />
      </MemoryRouter>,
    )

    const printButton = screen.getByRole('button', { name: /In đơn/i })
    await user.click(printButton)
    expect(printSpy).toHaveBeenCalledOnce()

    printSpy.mockRestore()
  })

  it('correctly handles multi-day range formatting', () => {
    testRequest.current = mockRequest({
      from_date: '2026-06-10',
      to_date: '2026-06-12',
      total_days: 3,
    })
    render(
      <MemoryRouter>
        <LeaveRequestPrintPage />
      </MemoryRouter>,
    )

    expect(
      screen.getByText(/Từ ngày 10\/06\/2026 đến hết ngày 12\/06\/2026/),
    ).toBeInTheDocument()
    expect(screen.getByText(/3 ngày\./)).toBeInTheDocument()
  })

  it('prints no attachment line and fetches nothing when the request has no files', () => {
    testRequest.current = mockRequest()
    render(
      <MemoryRouter>
        <LeaveRequestPrintPage />
      </MemoryRouter>,
    )
    expect(screen.queryByText(/Tài liệu đính kèm/)).not.toBeInTheDocument()
    expect(screen.queryAllByRole('img', { name: /\.(jpg|png)$/ })).toHaveLength(0)
    expect(fetchBlobUrl).not.toHaveBeenCalled()
  })

  it('appends one page per image through the authenticated view endpoint and names other files', async () => {
    testRequest.current = mockRequest()
    testAttachments.current = [
      attachment(1, 'giay-kham.jpg', 'image/jpeg'),
      attachment(2, 'giay-ra-vien.pdf', 'application/pdf'),
      attachment(3, 'toa-thuoc.png', 'image/png'),
    ]
    fetchBlobUrl.mockImplementation(async (url) => `blob:${url}`)

    render(
      <MemoryRouter>
        <LeaveRequestPrintPage />
      </MemoryRouter>,
    )

    //  Trước khi ảnh về, nút In bị khóa — bấm sớm là mặt sau in ra trang trắng.
    expect(screen.getByRole('button', { name: /Đang nạp ảnh đính kèm/ })).toBeDisabled()

    const first = await screen.findByRole('img', { name: 'giay-kham.jpg' })
    const second = screen.getByRole('img', { name: 'toa-thuoc.png' })
    //  Ảnh RIÊNG TƯ: đi `/view` có token, không bao giờ trỏ `src` thẳng vào API.
    expect(first).toHaveAttribute('src', 'blob:/api/attachments/1/view')
    expect(second).toHaveAttribute('src', 'blob:/api/attachments/3/view')
    expect(fetchBlobUrl).toHaveBeenCalledTimes(2)
    //  PDF không in, chỉ ghi tên.
    expect(screen.queryByRole('img', { name: 'giay-ra-vien.pdf' })).not.toBeInTheDocument()
    expect(
      screen.getByText('giay-ra-vien.pdf; 2 ảnh in kèm ở các trang sau'),
    ).toBeInTheDocument()

    expect(screen.getByRole('button', { name: /In đơn/ })).toBeEnabled()
  })

  it('warns about an image that failed to load instead of printing a blank page', async () => {
    testRequest.current = mockRequest()
    testAttachments.current = [
      attachment(1, 'hong.jpg', 'image/jpeg'),
      attachment(2, 'tot.png', 'image/png'),
    ]
    fetchBlobUrl.mockImplementation(async (url) => {
      if (url.includes('/1/')) throw new Error('403')
      return `blob:${url}`
    })

    render(
      <MemoryRouter>
        <LeaveRequestPrintPage />
      </MemoryRouter>,
    )

    expect(await screen.findByRole('alert')).toHaveTextContent('hong.jpg')
    expect(screen.getByRole('img', { name: 'tot.png' })).toBeInTheDocument()
    expect(screen.queryByRole('img', { name: 'hong.jpg' })).not.toBeInTheDocument()
    //  Một ảnh hỏng không được khóa cả bản in.
    expect(screen.getByRole('button', { name: /In đơn/ })).toBeEnabled()
  })
})
