import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { DocumentSubmittedLockNotice } from './document-submitted-lock-notice'

/**
 * Khóa mà không nói lý do thì người soạn tưởng hệ hỏng. Băng này phải nêu đủ
 * hai điều: vì sao khóa, và ĐI ĐƯỜNG NÀO để sửa tiếp.
 */
describe('DocumentSubmittedLockNotice', () => {
  it('im lặng khi văn bản chưa gửi duyệt', () => {
    const { container } = render(<DocumentSubmittedLockNotice submitted={false} />)

    expect(container).toBeEmptyDOMElement()
  })

  it('nói rõ đang khóa và chỉ đường rút phiếu để sửa tiếp', () => {
    render(<DocumentSubmittedLockNotice submitted />)

    expect(screen.getByText(/đang trình duyệt nên nội dung và thông tin đã khóa/i)).toBeInTheDocument()
    expect(screen.getByText(/rút phiếu/i)).toBeInTheDocument()
    expect(screen.getByText(/nháp/i)).toBeInTheDocument()
  })
})
