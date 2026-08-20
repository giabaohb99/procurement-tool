import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { DocumentVersion } from '../types/document-record'
import { DocumentDraftHolderNotice } from './document-draft-holder-notice'

/**
 * C14 — hai người cùng bấm "mở phiên bản mới" thì người thua phải biết HỎI AI.
 * Trước đây chỗ này chỉ ghi "đang có bản nháp mở", không nêu tên ai.
 */
function draft(overrides: Partial<DocumentVersion> = {}): DocumentVersion {
  return {
    id: 9,
    document_id: 1,
    version_no: '2.0',
    major: 2,
    minor: 0,
    status: 1,
    status_label: 'Nháp',
    is_locked: false,
    change_kind: 1,
    change_summary: 'Bổ sung Điều 5',
    change_reason: '',
    requires_reconfirm: true,
    effective_from: null,
    content_sha256: '',
    margin_left_mm: 30,
    margin_right_mm: 20,
    auto_heading_number: false,
    header_left: '',
    header_right: '',
    footer_left: '',
    footer_right: '',
    prev_version_id: 8,
    approved_at: '',
    approved_by_name: '',
    created_by_name: 'Trần Văn A',
    created_at: '2026-08-17T09:30:00',
    is_current: false,
    ...overrides,
  }
}

describe('DocumentDraftHolderNotice', () => {
  it('nêu đích danh người đang giữ và bản nháp số mấy', () => {
    render(<DocumentDraftHolderNotice draft={draft()} />)

    expect(screen.getByText(/Trần Văn A/)).toBeInTheDocument()
    expect(screen.getByText(/2\.0/)).toBeInTheDocument()
  })

  it('tài khoản tạo bản nháp đã bị xóa thì vẫn nói được là có người giữ', () => {
    render(<DocumentDraftHolderNotice draft={draft({ created_by_name: '' })} />)

    expect(screen.getByText(/một người khác/)).toBeInTheDocument()
  })

  it('hiện thời điểm mở bản nháp để biết nó treo bao lâu rồi', () => {
    render(<DocumentDraftHolderNotice draft={draft()} />)

    expect(screen.getByText(/Mở từ/)).toBeInTheDocument()
  })

  it('không có thời điểm mở thì bỏ hẳn câu đó, không hiện "Mở từ" cụt', () => {
    render(<DocumentDraftHolderNotice draft={draft({ created_at: '' })} />)

    expect(screen.queryByText(/Mở từ/)).not.toBeInTheDocument()
  })

  it('bấm "Xem bản nháp" thì gọi callback để nhảy tới đúng bản đó', async () => {
    const onOpenDraft = vi.fn()
    render(<DocumentDraftHolderNotice draft={draft()} onOpenDraft={onOpenDraft} />)

    await userEvent.click(screen.getByRole('button', { name: /Xem bản nháp/ }))

    expect(onOpenDraft).toHaveBeenCalledOnce()
  })

  it('không truyền callback thì không hiện nút — nút bấm không làm gì còn tệ hơn là không có nút', () => {
    render(<DocumentDraftHolderNotice draft={draft()} />)

    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})
