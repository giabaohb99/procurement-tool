import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { ACTION } from '@/modules/approval/types/approval'
import { ApprovalInboxCard } from './approval-inbox-card'
import type { InboxRow } from './approval-inbox-row'

function pendingRow(overrides: Partial<InboxRow> = {}): InboxRow {
  return {
    id: 'pending-1',
    kind: 'pending',
    entityId: 365,
    code: '',
    title: 'Văn bản nghỉ lễ 02/09 pháp nhân con',
    nodeName: 'Bước 1',
    startedByName: 'Nguyễn Văn A',
    dueAt: '2026-09-20',
    isOverdue: false,
    decidedAt: null,
    action: null,
    actionLabel: '',
    instanceStatusLabel: '',
    comment: '',
    onBehalfOfName: '',
    ...overrides,
  }
}

function doneRow(overrides: Partial<InboxRow> = {}): InboxRow {
  return {
    ...pendingRow(),
    id: 'done-1',
    kind: 'done',
    code: '01/2026/TB-SAM',
    startedByName: '',
    dueAt: null,
    decidedAt: '2026-08-22T14:30:00',
    action: ACTION.approve,
    actionLabel: 'Duyệt',
    instanceStatusLabel: 'Đã duyệt',
    ...overrides,
  }
}

describe('ApprovalInboxCard', () => {
  /**
   * ⚠️ Bài kiểm quan trọng nhất của tệp này.
   *
   * `DataTableMobileCards` bọc kết quả của `renderCard` trong MỘT `<button>` để
   * cả thẻ bấm được bằng bàn phím lẫn trình đọc màn hình — và ở màn này đó là
   * đường DUY NHẤT vào văn bản để duyệt. Nút lồng trong nút là HTML sai: trình
   * duyệt tự gỡ cây DOM ra, và trên máy cảm ứng thì hai vùng chạm đè nhau.
   */
  it('không dựng nút nào bên trong thẻ — cả thẻ đã là một nút bấm được', () => {
    const { container } = render(<ApprovalInboxCard row={doneRow()} />)
    expect(container.querySelectorAll('button')).toHaveLength(0)
  })

  it('đưa TÊN văn bản lên trước, số hiệu xuống dòng phụ', () => {
    render(<ApprovalInboxCard row={doneRow()} />)
    const title = screen.getByText('Văn bản nghỉ lễ 02/09 pháp nhân con')
    const code = screen.getByText('01/2026/TB-SAM')
    //  `compareDocumentPosition` đọc thứ tự trong cây DOM — đó cũng là thứ tự
    //  người dùng đọc và thứ tự trình đọc màn hình phát ra.
    expect(title.compareDocumentPosition(code) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  })

  /**
   * Hộp duyệt phần lớn là văn bản ĐANG TRÌNH, chưa cấp số. «Chưa cấp số» là một
   * lời nói chứ không phải một mã — để `font-mono` thì nó dãn ra và đọc như lỗi
   * hiển thị (bài học duoc-CR-364).
   */
  it('nói rõ «Chưa cấp số» và KHÔNG lấy chữ đều nét cho câu đó', () => {
    render(<ApprovalInboxCard row={pendingRow({ code: '' })} />)
    expect(screen.getByText('Chưa cấp số').className).not.toContain('font-mono')
  })

  it('dòng CHỜ mang huy hiệu «Cần duyệt», quá hạn thì đổi thành «Quá hạn»', () => {
    const { rerender } = render(<ApprovalInboxCard row={pendingRow()} />)
    expect(screen.getByText('Cần duyệt')).toBeInTheDocument()
    expect(screen.queryByText('Quá hạn')).not.toBeInTheDocument()

    rerender(<ApprovalInboxCard row={pendingRow({ isOverdue: true })} />)
    expect(screen.getByText('Quá hạn')).toBeInTheDocument()
  })

  /**
   * ⚠️ Huy hiệu tình trạng là thứ DUY NHẤT phân biệt hai nửa của bảng gộp — ở
   * bảng nó là cột không ẩn được và được ghim phải. Bỏ nó khỏi thẻ cho gọn là
   * xóa luôn ranh giới giữa «việc cần làm» và «việc đã xong».
   */
  it('dòng ĐÃ BẤM mang huy hiệu việc đã làm chứ không phải «Cần duyệt»', () => {
    render(<ApprovalInboxCard row={doneRow({ actionLabel: 'Trả lại', action: ACTION.return })} />)
    expect(screen.getByText('Trả lại')).toBeInTheDocument()
    expect(screen.queryByText('Cần duyệt')).not.toBeInTheDocument()
  })

  /**
   * ⚠️ «Tôi đã ký bước của mình» KHÁC «phiếu đã xong». Ở bảng hai thứ đó là hai
   * cột, và chính TIÊU ĐỀ cột phân biệt chúng; thẻ không có tiêu đề cột, nên
   * trạng thái phiếu phải mang theo chữ «Phiếu». Thiếu nó thì hai huy hiệu đứng
   * liền nhau đọc ra «Duyệt · Đã duyệt» — hai chữ gần như đồng nghĩa.
   */
  it('gắn chữ «Phiếu» cho trạng thái tờ phiếu, không để nó thành huy hiệu trần', () => {
    render(<ApprovalInboxCard row={doneRow()} />)
    expect(screen.getByText('Phiếu: Đã duyệt')).toBeInTheDocument()
  })

  /**
   * Đây là chỗ thẻ làm được mà bảng gộp không làm được: bảng phải có đủ cột cho
   * cả hai loại dòng rồi vẽ "—" vào ô loại kia không có, nên ở khổ hẹp người
   * dùng gặp một rừng gạch ngang. Thẻ chỉ dựng dòng nào có nghĩa với chính nó.
   */
  it('không vẽ ô rỗng của loại dòng kia', () => {
    const { container: cho } = render(<ApprovalInboxCard row={pendingRow()} />)
    expect(cho.textContent).not.toContain('—')
    expect(cho.textContent).not.toContain('Phiếu:')

    const { container: xong } = render(<ApprovalInboxCard row={doneRow()} />)
    expect(xong.textContent).not.toContain('—')
    expect(xong.textContent).not.toContain('Hạn ')
  })

  it('dòng CHỜ nói ai trình và hạn nào', () => {
    render(<ApprovalInboxCard row={pendingRow()} />)
    expect(screen.getByText('Nguyễn Văn A')).toBeInTheDocument()
    expect(screen.getByText(/^Hạn /)).toBeInTheDocument()
  })

  /**
   * Trường rỗng thì bỏ hẳn dòng chứ không dựng một dòng trống: thẻ cao thấp so
   * le đã đành, mà một dòng trắng giữa thẻ đọc ra như dữ liệu bị mất.
   */
  it('bỏ hẳn dòng phụ khi loại dòng đó không có trường nào để nói', () => {
    const { container } = render(
      <ApprovalInboxCard row={pendingRow({ startedByName: '', dueAt: null })} />,
    )
    expect(container.textContent).not.toContain('Hạn')
    expect(screen.getByText('Cần duyệt')).toBeInTheDocument()
  })

  it('không nổ khi việc đã bấm mang mã hành động lạ', () => {
    //  `action` do backend gửi; mã mới thêm mà frontend chưa biết thì rơi vào
    //  nhánh `?? 'outline'` — không được ném lỗi làm trắng cả danh sách.
    render(<ApprovalInboxCard row={doneRow({ action: 99, actionLabel: 'Việc lạ' })} />)
    expect(screen.getByText('Việc lạ')).toBeInTheDocument()
  })
})
