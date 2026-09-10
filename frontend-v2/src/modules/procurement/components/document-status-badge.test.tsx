import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import {
  PO_DOCUMENT_STATUS,
  PO_PROGRESS_STATUS,
  PR_LINE_STATUS,
} from '@/shared/constants/statuses'

import {
  PO_STATUS_LABELS,
  PR_STATUS_LABELS,
  SR_STATUS_LABELS,
} from '../types/purchase-document'
import { DocumentStatusBadge, ProgressStatusBadge, StatusBadge } from './document-status-badge'

/**
 * B-06: sáu cột trạng thái của cụm ĐMH + YCMH đổi sang lưu MÃ tiếng Anh.
 *
 * Rủi ro của việc đổi đó nằm gọn ở hai huy hiệu này: quên dịch một mã là cột hiện
 * `doc_pending` giữa một màn tiếng Việt, mà không có gì đỏ lên báo. Test dò cả bộ mã
 * chứ không chọn vài mã tiêu biểu — chỗ sót luôn là mã ít gặp.
 */
describe('ProgressStatusBadge', () => {
  it.each(PO_PROGRESS_STATUS.map((o) => [o.value, o.label]))(
    'tiến độ dòng ĐMH mã %s hiện nhãn tiếng Việt',
    (value, label) => {
      render(<ProgressStatusBadge status={value} />)
      expect(screen.getByText(label)).toBeInTheDocument()
    },
  )

  it.each(PR_LINE_STATUS.map((o) => [o.value, o.label]))(
    'trạng thái dòng YCMH mã %s hiện nhãn tiếng Việt',
    (value, label) => {
      // Cùng một huy hiệu phục vụ hai bộ mã: năm mã giữa chuỗi trùng nghĩa, YCMH
      // thêm `no_po` ở đầu. Nhãn của `no_po` chỉ có ở bộ YCMH nên dễ rơi nhất.
      render(<ProgressStatusBadge status={value} />)
      expect(screen.getByText(label)).toBeInTheDocument()
    },
  )

  it('mã lạ thì hiện nguyên mã chứ không nuốt mất dòng', () => {
    render(<ProgressStatusBadge status="ma_la" />)
    expect(screen.getByText('ma_la')).toBeInTheDocument()
  })

  it('rỗng thì để trắng, không vẽ huy hiệu nào', () => {
    // Trước đây trả về gạch ngang. Đợt chuẩn hóa ô rỗng (24/08/2026) bỏ hết gạch
    // ngang giữ chỗ ở bảng và ô xem — ô rỗng để trắng. Huy hiệu vì thế không
    // được vẽ gì, kẻo bảng lại có gạch ngang trong khi các cột khác đã để trắng.
    const { container } = render(<ProgressStatusBadge status="" />)
    expect(container).toBeEmptyDOMElement()
  })
})

/**
 * bao-CR-363: khách chụp màn YCMH trên prod, khoanh đỏ ba mốc trùng màu — "Đã điều phối"
 * và "Đã mua hàng" cùng xanh, "Đang xử lý" cùng hổ phách với "Chờ duyệt". Gốc lỗi là bảng
 * tông chỉ có 5 màu cho 11 mốc, nên nhiều mốc dồn chung một tông.
 *
 * ⚠️ Đây là chỗ DUY NHẤT trong bộ test được phép khẳng định theo LỚP CSS thay vì theo vai
 * trò/nội dung: thứ đang kiểm chính là màu, mà màu thì không đọc ra được từ chữ trong ô.
 * Test không ghim màu cụ thể (đổi tông là việc bình thường) mà ghim đúng một điều: hai mốc
 * ĐỨNG LIỀN NHAU trong vòng đời phải khác lớp màu.
 */
function toneClassOf(status: string, labels: Record<string, string>): string {
  const { container, unmount } = render(<StatusBadge status={status} labels={labels} />)
  const cls = container.querySelector('[data-slot="badge"]')?.className ?? ''
  unmount()
  return cls
}

describe('StatusBadge lifecycle colours', () => {
  // Đúng thứ tự backend đặt cho PYC (`purchase_request/service.py`), bỏ hai mốc rẽ nhánh
  // `rejected` / `cancelled` vì chúng không nối tiếp mốc nào.
  const PR_FLOW = [
    'draft',
    'submitted',
    'approved',
    'dispatched',
    'processing',
    'purchasing',
    'purchased',
    'completed',
  ]

  it('gives every consecutive pair of purchase-request milestones a different colour', () => {
    for (let i = 1; i < PR_FLOW.length; i += 1) {
      const truoc = toneClassOf(PR_FLOW[i - 1], PR_STATUS_LABELS)
      const sau = toneClassOf(PR_FLOW[i], PR_STATUS_LABELS)
      expect(sau, `${PR_FLOW[i - 1]} và ${PR_FLOW[i]} đang cùng một màu`).not.toBe(truoc)
    }
  })

  it('never paints two purchase-request milestones with the same colour', () => {
    // Không chỉ cặp liền kề: cả 8 mốc phải phân biệt được khi quét mắt một lượt
    // trên màn danh sách, vì người dùng lọc theo màu chứ không đọc từng chữ.
    const mau = PR_FLOW.map((s) => toneClassOf(s, PR_STATUS_LABELS))
    expect(new Set(mau).size).toBe(PR_FLOW.length)
  })

  it('keeps returned apart from both rejected and pending', () => {
    // "Bị trả lại" sửa rồi gửi duyệt lại được, "Đã từ chối" là khóa phiếu — hai thứ đó
    // KHÔNG được nhìn giống nhau. Trước CR-363 nó lại còn trùng luôn với "Chờ duyệt".
    const traLai = toneClassOf('rejected', PR_STATUS_LABELS)
    expect(traLai).not.toBe(toneClassOf('cancelled', PR_STATUS_LABELS))
    expect(traLai).not.toBe(toneClassOf('submitted', PR_STATUS_LABELS))
  })

  it('gives every consecutive pair of purchase-order milestones a different colour', () => {
    const PO_FLOW = ['draft', 'submitted', 'approved', 'partial', 'received', 'completed']
    for (let i = 1; i < PO_FLOW.length; i += 1) {
      const truoc = toneClassOf(PO_FLOW[i - 1], PO_STATUS_LABELS)
      const sau = toneClassOf(PO_FLOW[i], PO_STATUS_LABELS)
      expect(sau, `${PO_FLOW[i - 1]} và ${PO_FLOW[i]} đang cùng một màu`).not.toBe(truoc)
    }
  })

  it('gives every consecutive pair of survey-request milestones a different colour', () => {
    const SR_FLOW = ['draft', 'submitted', 'approved', 'processing', 'survey_done', 'pr_created', 'done']
    for (let i = 1; i < SR_FLOW.length; i += 1) {
      const truoc = toneClassOf(SR_FLOW[i - 1], SR_STATUS_LABELS)
      const sau = toneClassOf(SR_FLOW[i], SR_STATUS_LABELS)
      expect(sau, `${SR_FLOW[i - 1]} và ${SR_FLOW[i]} đang cùng một màu`).not.toBe(truoc)
    }
  })

  it('falls back to the neutral tone for an unknown code instead of dropping the row', () => {
    render(<StatusBadge status="ma_la" labels={PR_STATUS_LABELS} />)
    expect(screen.getByText('ma_la')).toBeInTheDocument()
  })

  it('renders nothing for an empty status', () => {
    const { container } = render(<StatusBadge status="" labels={PR_STATUS_LABELS} />)
    expect(container).toBeEmptyDOMElement()
  })
})

describe('DocumentStatusBadge', () => {
  it.each(PO_DOCUMENT_STATUS.map((o) => [o.value, o.label]))(
    'hồ sơ chứng từ mã %s hiện nhãn tiếng Việt',
    (value, label) => {
      render(<DocumentStatusBadge status={value} />)
      expect(screen.getByText(label)).toBeInTheDocument()
    },
  )

  it('mã lạ thì hiện nguyên mã', () => {
    render(<DocumentStatusBadge status="ma_la" />)
    expect(screen.getByText('ma_la')).toBeInTheDocument()
  })
})
