import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import {
  PO_DOCUMENT_STATUS,
  PO_PROGRESS_STATUS,
  PR_LINE_STATUS,
} from '@/shared/constants/statuses'

import { DocumentStatusBadge, ProgressStatusBadge } from './document-status-badge'

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
