import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { ApprovalStageNote } from './approval-stage-note'

describe('ApprovalStageNote', () => {
  it('nói rõ phiếu đang chờ ở chặng nào bên cạnh badge trạng thái', () => {
    render(<ApprovalStageNote summary="Đang ở chặng 3/3 · Duyệt Brand & Pháp chế" />)

    expect(screen.getByText('Đang ở chặng 3/3 · Duyệt Brand & Pháp chế')).toBeInTheDocument()
  })

  it('không vẽ gì khi phiếu chưa vào bộ máy duyệt', () => {
    //  Vẽ một dòng rỗng cạnh badge thì bảng danh sách lệch hàng, và người xem
    //  đọc ra "có luồng nhưng hỏng" thay vì "không qua luồng".
    const { container } = render(<ApprovalStageNote summary="" />)

    expect(container).toBeEmptyDOMElement()
  })

  it.each([undefined, null, '   '])('coi %p là không có luồng', (summary) => {
    const { container } = render(<ApprovalStageNote summary={summary} />)

    expect(container).toBeEmptyDOMElement()
  })

  it('giữ nguyên câu dài trong thuộc tính title để ô hẹp vẫn tra cứu được', () => {
    const summary = 'Đang ở chặng 2/5 · Nguyễn Văn A, Trần Thị B, Lê Văn C'
    render(<ApprovalStageNote summary={summary} />)

    expect(screen.getByTitle(summary)).toBeInTheDocument()
  })
})
