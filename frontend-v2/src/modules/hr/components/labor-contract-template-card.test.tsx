import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { LaborContractTemplate } from '../types/labor-contract'
import { LaborContractTemplateCard } from './labor-contract-template-card'

const template: LaborContractTemplate = {
  id: 7, company_id: 1, company_name: 'Công ty A', company_code: 'CTA', contract_type: 2, name: 'Mẫu 12 tháng',
  note: '', original_filename: 'mau.docx', file_size: 2048, placeholders: [], is_active: true,
  created_at: '2026-10-01T03:00:00', created_by_name: 'HR', contract_count: 3,
}

function actions(canWrite = true, canDelete = true) {
  return {
    canWrite, canDelete,
    onDownload: vi.fn(), onEditContent: vi.fn(), onEditInfo: vi.fn(),
    onReplaceFile: vi.fn(), onToggleActive: vi.fn(), onDelete: vi.fn(),
  }
}

describe('LaborContractTemplateCard', () => {
  it('bày tên, pháp nhân kèm mã, loại HĐ, tệp gốc, số HĐ đã dùng và ngày tạo', () => {
    render(<LaborContractTemplateCard template={template} actions={actions()} />)
    expect(screen.getByText('Mẫu 12 tháng')).toBeInTheDocument()
    expect(screen.getByText(/CTA/)).toBeInTheDocument()
    expect(screen.getByText('Công ty A')).toBeInTheDocument()
    expect(screen.getByText('Xác định thời hạn')).toBeInTheDocument()
    expect(screen.getByText(/mau\.docx/)).toBeInTheDocument()
    expect(screen.getByText(/3 HĐ đã dùng/)).toBeInTheDocument()
    expect(screen.getByText(/Tạo 01\/10\/2026 bởi HR/)).toBeInTheDocument()
  })

  it('đang dùng thì không có huy hiệu; ngừng thì có huy hiệu "Ngừng"', () => {
    const { unmount } = render(<LaborContractTemplateCard template={template} actions={actions()} />)
    expect(screen.queryByText('Đang dùng')).toBeNull()
    expect(screen.queryByText('Ngừng')).toBeNull()
    unmount()
    render(<LaborContractTemplateCard template={{ ...template, is_active: false }} actions={actions()} />)
    expect(screen.getByText('Ngừng')).toBeInTheDocument()
  })

  it('menu "⋯" theo sang thẻ và vẫn ẩn mục theo quyền', async () => {
    const user = userEvent.setup()
    const a = actions(false, false)
    render(<LaborContractTemplateCard template={template} actions={a} />)
    await user.click(screen.getByRole('button', { name: /Thao tác với mẫu/ }))
    const items = (await screen.findAllByRole('menuitem')).map((item) => item.textContent)
    expect(items).toEqual(['Xem nội dung', 'Tải tệp mẫu'])
    await user.click(screen.getByRole('menuitem', { name: 'Tải tệp mẫu' }))
    expect(a.onDownload).toHaveBeenCalledWith(template)
  })

  it('không có mã pháp nhân, không có tệp gốc thì bỏ phần đó, không in "undefined"', () => {
    const { container } = render(
      <LaborContractTemplateCard template={{ ...template, company_code: '', original_filename: '', file_size: 0 }} actions={actions()} />,
    )
    expect(container.textContent).not.toMatch(/undefined|null/)
    expect(screen.queryByText(/mau\.docx/)).toBeNull()
  })
})
