import { render, screen } from '@testing-library/react'
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

describe('LeaveRequestPrintPage', () => {
  it('renders complete leave request sheet with correct fields and structure', () => {
    testRequest.current = mockRequest()
    render(
      <MemoryRouter>
        <LeaveRequestPrintPage />
      </MemoryRouter>,
    )

    // Tiêu đề và biểu tượng
    expect(screen.getByText('ĐƠN XIN NGHỈ PHÉP')).toBeInTheDocument()
    expect(screen.getByAltText('DEGO HOLDING')).toBeInTheDocument()

    // Kính gửi
    expect(screen.getByText(/Trưởng phòng\/Bộ phận\/Nhóm:/)).toBeInTheDocument()
    expect(screen.getByText(/Trưởng phòng HCNS/)).toBeInTheDocument()

    // Thông tin nhân sự & chữ ký
    expect(screen.getAllByText(/Phạm Lê Triết Giang/)).toHaveLength(2)
    expect(screen.getByText(/0973555582/)).toBeInTheDocument()
    expect(screen.getAllByText(/Lập trình & IT nội bộ/)).toHaveLength(2)

    // Lý do & thời gian
    expect(
      screen.getByText(/Em xin phép nghỉ 1 ngày để đưa vợ con về Châu Đốc/),
    ).toBeInTheDocument()
    expect(screen.getByText(/thứ ba 09\/06\/2026/)).toBeInTheDocument()

    // Bàn giao công việc mặc định
    expect(
      screen.getByText(/Cá nhân tự sắp xếp công việc\. Team hỗ trợ công việc/),
    ).toBeInTheDocument()

    // Chữ ký 3 cột
    expect(screen.getByText('P.HCNS')).toBeInTheDocument()
    expect(screen.getByText('Trưởng Phòng/Bộ phận')).toBeInTheDocument()
    expect(screen.getByText('Trần Quang Phú')).toBeInTheDocument()
    expect(screen.getByText('Người làm đơn')).toBeInTheDocument()
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
      screen.getByText(/3 ngày, từ ngày 10\/06\/2026 đến ngày 12\/06\/2026/),
    ).toBeInTheDocument()
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
