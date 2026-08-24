import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { DocumentNeedsReviewBanner } from './document-needs-review-banner'

afterEach(() => {
  vi.restoreAllMocks()
})

describe('DocumentNeedsReviewBanner', () => {
  it('văn bản thường không cần rà thì không hiện băng', () => {
    const { container } = render(<DocumentNeedsReviewBanner needsReview={false} note="" />)

    expect(container).toBeEmptyDOMElement()
  })

  it('bản clone luôn có lối mở bản gốc dù chưa bị đánh dấu cần rà', async () => {
    const user = userEvent.setup()
    const open = vi.spyOn(window, 'open').mockImplementation(() => null)

    render(<DocumentNeedsReviewBanner needsReview={false} note="" sourceDocumentId={42} />)

    expect(screen.getByText(/bản riêng nhận từ văn bản gốc/i)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /Xem bản gốc/i }))

    expect(open).toHaveBeenCalledWith(expect.stringContaining('/42'), '_blank', 'noopener')
  })

  it('bản gốc đổi thì chuyển sang cảnh báo và vẫn mở được bản gốc', () => {
    render(
      <DocumentNeedsReviewBanner
        needsReview
        note="Bản gốc đã lên phiên bản 2.0."
        sourceDocumentId={42}
      />,
    )

    expect(screen.getByText('Văn bản này cần rà lại.')).toBeInTheDocument()
    expect(screen.getByText(/phiên bản 2.0/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Xem bản gốc/i })).toBeInTheDocument()
  })

  //  LỖI THẬT (22/08/2026): bản riêng chưa bị đánh dấu vẫn bày nút rà. Người
  //  dùng gõ lý do, bấm xác nhận, rồi ăn báo đỏ «Văn bản này không có dấu cần rà
  //  lại» — mà họ không làm gì sai. Nút chỉ có việc khi ĐANG có dấu.
  it('bản riêng CHƯA bị đánh dấu thì không bày nút rà', () => {
    render(
      <DocumentNeedsReviewBanner
        needsReview={false}
        note=""
        sourceDocumentId={42}
        canWrite
        onConfirm={vi.fn()}
      />,
    )

    expect(screen.getByText(/bản riêng nhận từ văn bản gốc/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Rà lại' })).not.toBeInTheDocument()
  })

  it('có dấu cần rà lại thì mới bày nút, và bấm là gọi callback', async () => {
    const user = userEvent.setup()
    const onConfirm = vi.fn()

    render(
      <DocumentNeedsReviewBanner
        needsReview
        note=""
        sourceDocumentId={42}
        canWrite
        onConfirm={onConfirm}
      />,
    )

    await user.click(screen.getByRole('button', { name: 'Rà lại' }))

    expect(onConfirm).toHaveBeenCalledOnce()
  })

  it('không có quyền sửa thì không bày nút dù đang có dấu', () => {
    render(<DocumentNeedsReviewBanner needsReview note="" canWrite={false} onConfirm={vi.fn()} />)

    expect(screen.queryByRole('button', { name: 'Rà lại' })).not.toBeInTheDocument()
  })
})
