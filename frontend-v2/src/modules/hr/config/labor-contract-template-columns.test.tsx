import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { LaborContractTemplate } from '../types/labor-contract'
import { buildLaborContractTemplateColumns } from './labor-contract-template-columns'

const template: LaborContractTemplate = {
  id: 7, company_id: 1, company_name: 'Công ty A', company_code: 'CTA', contract_type: 2, name: 'Mẫu 12 tháng',
  note: '', original_filename: 'mau.docx', file_size: 2048, placeholders: [], is_active: true,
  created_at: '2026-10-01T03:00:00', created_by_name: 'HR', contract_count: 0,
}

function renderActions(canWrite: boolean, canDelete: boolean, row = template) {
  const actions = {
    canWrite, canDelete,
    onDownload: vi.fn(), onEditContent: vi.fn(), onEditInfo: vi.fn(),
    onReplaceFile: vi.fn(), onToggleActive: vi.fn(), onDelete: vi.fn(),
  }
  const col = buildLaborContractTemplateColumns(actions).find((c) => c.key === 'actions')
  if (!col) throw new Error('thiếu cột Thao tác')
  render(<>{col.cell(row)}</>)
  return actions
}

describe('cột Thao tác của bảng Mẫu hợp đồng', () => {
  it('chỉ có quyền đọc: còn Tải tệp và Xem nội dung, không có Sửa thông tin', () => {
    renderActions(false, false)
    expect(screen.getByRole('button', { name: /Tải tệp mẫu/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Xem nội dung mẫu/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Sửa thông tin/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /Soạn nội dung/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /Thay tệp/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /Ngừng dùng|Bật dùng/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /Xóa mẫu/ })).toBeNull()
  })

  it('có quyền sửa nhưng không xóa: thấy Thay tệp và Ngừng dùng, không thấy Xóa', () => {
    renderActions(true, false)
    expect(screen.getByRole('button', { name: /Thay tệp mẫu/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Ngừng dùng mẫu/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Xóa mẫu/ })).toBeNull()
  })

  //  duoc-CR-606 — hai nút mới phải gọi ĐÚNG callback với ĐÚNG mẫu của dòng.
  it('có quyền sửa: Soạn nội dung và Sửa thông tin gọi đúng callback với mẫu của dòng', () => {
    const actions = renderActions(true, false)
    fireEvent.click(screen.getByRole('button', { name: /Soạn nội dung mẫu Mẫu 12 tháng/ }))
    fireEvent.click(screen.getByRole('button', { name: /Sửa thông tin mẫu Mẫu 12 tháng/ }))
    expect(actions.onEditContent).toHaveBeenCalledWith(template)
    expect(actions.onEditInfo).toHaveBeenCalledWith(template)
    expect(actions.onReplaceFile).not.toHaveBeenCalled()
  })

  it('mẫu đã ngừng thì nút đổi thành Bật dùng; có quyền xóa thì có nút Xóa', () => {
    renderActions(true, true, { ...template, is_active: false })
    expect(screen.getByRole('button', { name: /Bật dùng mẫu/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Xóa mẫu/ })).toBeInTheDocument()
  })
})


//  Lỗi thật (test Chrome 06/10): local có hai pháp nhân cùng tên «CÔNG TY TNHH DEGO HOLDING» (id 1
//  mã DEGO, id 17 mã DEGO HOLDING). Bảng chỉ hiện tên ⇒ mẫu của công ty này trông như của công ty kia.
describe('company column', () => {
  function renderCompany(row: LaborContractTemplate) {
    const col = buildLaborContractTemplateColumns({
      canWrite: false, canDelete: false,
      onDownload: vi.fn(), onEditContent: vi.fn(), onEditInfo: vi.fn(),
      onReplaceFile: vi.fn(), onToggleActive: vi.fn(), onDelete: vi.fn(),
    }).find((c) => c.key === 'company')
    if (!col) throw new Error('thiếu cột Pháp nhân')
    return render(<>{col.cell(row)}</>)
  }

  it('shows the company code under the name so same-name companies can be told apart', () => {
    renderCompany({ ...template, company_name: 'CÔNG TY TNHH DEGO HOLDING', company_code: 'DEGO HOLDING' })
    expect(screen.getByText('CÔNG TY TNHH DEGO HOLDING')).toBeInTheDocument()
    expect(screen.getByText('DEGO HOLDING')).toBeInTheDocument()
  })

  it('renders only the name when the company has no code, without an empty line', () => {
    const { container } = renderCompany({ ...template, company_code: '' })
    expect(container.textContent).toBe('Công ty A')
  })
})
