import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { PurchaseOrder } from '../types/purchase-document'
import type { LinkedSurveyRequest } from '../types/purchase-request-detail'
import { PurchaseRequestLinkedDocumentsCard } from './purchase-request-linked-documents-card'

/**
 * Thẻ "Chứng từ liên quan" trên màn chi tiết YCMH (bao-CR-422).
 *
 * Lý do thẻ này ra đời là một lỗi BÀY, không phải lỗi tính: danh sách ĐMH trước
 * đây nấp sau một nút TỰ ẨN khi chưa có đơn nào, còn đường về YCBG thì chỉ bày
 * được một phiếu nguồn. Nên bộ kiểm này canh đúng hai chỗ đó — thẻ phải nói cả
 * khi rỗng, và phải bày ĐỦ nguồn.
 */

let grantedPermissions: string[] = []

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string, action: string) => grantedPermissions.includes(`${entity}:${action}`),
  }),
}))

let mockOrders: PurchaseOrder[] = []
let mockOrdersLoading = false
let mockOrdersError = false
const relatedOrdersCalls: string[] = []

vi.mock('../hooks/use-purchase-request-support', () => ({
  useRelatedPurchaseOrders: (code: string) => {
    relatedOrdersCalls.push(code)
    return {
      data: { items: mockOrders, total: mockOrders.length, page: 1, page_size: 200 },
      isLoading: mockOrdersLoading,
      isError: mockOrdersError,
    }
  },
}))

function buildSurveyRequest(overrides: Partial<LinkedSurveyRequest> = {}): LinkedSurveyRequest {
  return {
    id: 501,
    code: 'YCBG05092601',
    status: 'survey_done',
    request_date: '2026-09-03',
    requester: 'Nguyễn Văn A',
    ...overrides,
  }
}

function buildOrder(overrides: Partial<PurchaseOrder> = {}): PurchaseOrder {
  return {
    id: 91,
    code: 'DMH-2026-091',
    supplier_name: 'CÔNG TY A',
    supplier_code: 'NCC-A',
    order_date: '2026-09-10',
    amount: 1500000,
    status: 'approved',
    ...overrides,
  } as PurchaseOrder
}

function renderCard(surveyRequests?: LinkedSurveyRequest[]) {
  return render(
    <MemoryRouter>
      <PurchaseRequestLinkedDocumentsCard
        data={{ code: 'PR-2026-012', survey_requests: surveyRequests }}
      />
    </MemoryRouter>,
  )
}

describe('PurchaseRequestLinkedDocumentsCard', () => {
  beforeEach(() => {
    grantedPermissions = ['survey_request:read', 'purchase_order:read']
    mockOrders = []
    mockOrdersLoading = false
    mockOrdersError = false
    relatedOrdersCalls.length = 0
  })

  it('still says so when the request has neither a source quote nor any order', () => {
    // Chính là ca đã làm đại ca không tìm ra chỗ xem đơn: nút cũ tự ẩn khi rỗng nên
    // màn hình im lặng. Thẻ mới phải trả lời "chưa có", đừng biến mất.
    renderCard([])

    expect(screen.getByText('Chứng từ liên quan')).toBeInTheDocument()
    expect(
      screen.getByText('Phiếu này lập tay, không sinh ra từ yêu cầu báo giá nào.'),
    ).toBeInTheDocument()
    expect(
      screen.getByText('Chưa có đơn mua hàng nào được lập từ phiếu này.'),
    ).toBeInTheDocument()
  })

  it('treats a missing survey_requests key like an empty list', () => {
    // Phiếu do bản backend cũ trả về không có khóa này. Thiếu khóa mà nổ thì cả
    // trang chi tiết trắng, nặng hơn nhiều so với việc thiếu một dòng liên kết.
    renderCard(undefined)

    expect(
      screen.getByText('Phiếu này lập tay, không sinh ra từ yêu cầu báo giá nào.'),
    ).toBeInTheDocument()
  })

  it('lists every source quote request, not just the first one', () => {
    renderCard([
      buildSurveyRequest(),
      buildSurveyRequest({ id: 502, code: 'YCBG05092602', status: 'pr_created' }),
    ])

    expect(screen.getByText('Yêu cầu báo giá nguồn (2)')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /YCBG05092601/ })).toHaveAttribute(
      'href',
      '/procurement/survey-requests/501',
    )
    expect(screen.getByRole('link', { name: /YCBG05092602/ })).toHaveAttribute(
      'href',
      '/procurement/survey-requests/502',
    )
    expect(screen.getByText('Đã tạo YCMH')).toBeInTheDocument()
  })

  it('shows the quote code as plain text when the viewer cannot open quote requests', () => {
    // Người yêu cầu thường không có survey_request:read — bấm vào chỉ ăn 403, nên
    // bày mã dạng chữ chứ không dựng link cụt.
    grantedPermissions = ['purchase_order:read']
    renderCard([buildSurveyRequest()])

    expect(screen.queryByRole('link', { name: /YCBG05092601/ })).toBeNull()
    expect(screen.getByText('YCBG05092601')).toBeInTheDocument()
  })

  it('links each purchase order to its detail page', () => {
    mockOrders = [buildOrder(), buildOrder({ id: 92, code: 'DMH-2026-092' })]
    renderCard([])

    expect(screen.getByText('Đơn mua hàng đã lập (2)')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /DMH-2026-092/ })).toHaveAttribute(
      'href',
      '/procurement/purchase-orders/92',
    )
  })

  it('does not even ask for orders when the viewer has no purchase_order:read', () => {
    // Hỏi cũng chỉ ăn 403 và đẻ ra toast lỗi cho người không liên quan.
    grantedPermissions = ['survey_request:read']
    mockOrders = [buildOrder()]
    renderCard([])

    expect(relatedOrdersCalls).toEqual([''])
    expect(screen.queryByText(/Đơn mua hàng đã lập/)).toBeNull()
    expect(screen.queryByText('DMH-2026-091')).toBeNull()
  })

  it('keeps the quote list readable when the order query fails', () => {
    // Hỏng một nửa không được kéo theo nửa kia: YCBG đi sẵn trong phiếu, không
    // phụ thuộc lượt gọi ĐMH.
    mockOrdersError = true
    renderCard([buildSurveyRequest()])

    expect(screen.getByRole('link', { name: /YCBG05092601/ })).toBeInTheDocument()
    expect(
      screen.getByText('Chưa đọc được danh sách đơn mua hàng, thử tải lại trang.'),
    ).toBeInTheDocument()
  })
})
