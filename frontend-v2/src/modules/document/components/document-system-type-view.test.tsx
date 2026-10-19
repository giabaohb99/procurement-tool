import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { DocumentType } from '../types/document-type'
import { DocumentSystemTypeView } from './document-system-type-view'

const hdld = {
  id: 9,
  code: 'HDLD',
  name: 'Hợp đồng lao động',
  id_scheme: 2,
  is_active: true,
  is_personal: true,
  needs_approval: false,
  needs_signature: false,
  needs_decision: false,
} as unknown as DocumentType

describe('DocumentSystemTypeView', () => {
  it('chỉ xem: không có nút Lưu / Xóa, có nút về danh sách', () => {
    const onBack = vi.fn()
    render(<DocumentSystemTypeView documentType={hdld} onBack={onBack} />)
    expect(screen.getByText('Loại hệ thống')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /lưu|xóa/i })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /về danh sách/i }))
    expect(onBack).toHaveBeenCalled()
  })
})
