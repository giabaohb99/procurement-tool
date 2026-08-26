import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { DocumentPendingIssueNotice } from './document-pending-issue-notice'

/**
 * «Chờ ban hành» là trạng thái dễ đọc nhầm là hệ đứng: chữ ký đủ rồi, phiên
 * duyệt đóng rồi, mà văn bản vẫn chưa có số hiệu. Băng này phải nói HAI câu
 * khác nhau cho hai người khác nhau — không thì người soạn ngồi chờ người khác,
 * người khác tưởng xong rồi, và văn bản nằm im vô thời hạn.
 */
describe('DocumentPendingIssueNotice', () => {
  it('bảo người soạn thảo rằng đang chờ CHÍNH HỌ bấm', () => {
    render(<DocumentPendingIssueNotice isDrafter drafterName="Trần A" />)

    expect(screen.getByText(/đang chờ bạn ban hành/i)).toBeInTheDocument()
    //  Không được nói "chờ người soạn thảo" với chính người soạn thảo — đọc
    //  xong họ vẫn ngồi chờ ai đó.
    expect(screen.queryByText(/chờ người soạn thảo/i)).not.toBeInTheDocument()
  })

  it('nói rõ phải chờ AI khi người xem không phải người soạn', () => {
    render(<DocumentPendingIssueNotice isDrafter={false} drafterName="Trần A" />)

    expect(screen.getByText(/chờ người soạn thảo/i)).toBeInTheDocument()
    expect(screen.getByText('Trần A')).toBeInTheDocument()
  })

  it('vẫn nói được là đang chờ khi không biết tên người soạn', () => {
    //  `drafter_name` rỗng khi hồ sơ nhân sự đã bị xóa. Vẫn phải nói ra là văn
    //  bản đang chờ một cú bấm, chỉ là không biết chờ ai.
    render(<DocumentPendingIssueNotice isDrafter={false} />)

    expect(screen.getByText(/chờ người soạn thảo/i)).toBeInTheDocument()
    expect(screen.getByText(/chưa có số hiệu/i)).toBeInTheDocument()
  })
})
