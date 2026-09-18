import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { SealWorkflowGuideCard } from './seal-workflow-guide-card'

describe('SealWorkflowGuideCard', () => {
  it('hiển thị đầy đủ 4 bước quy trình duyệt dấu', () => {
    render(<SealWorkflowGuideCard />)

    expect(screen.getByText('Quy trình Trình ký & Đóng dấu văn bản')).toBeInTheDocument()
    expect(screen.getByText('Tạo yêu cầu')).toBeInTheDocument()
    expect(screen.getByText('TBP Thẩm định')).toBeInTheDocument()
    expect(screen.getByText('Văn thư Đóng dấu')).toBeInTheDocument()
    expect(screen.getByText('Hoàn tất & Lưu trữ')).toBeInTheDocument()
  })
})
