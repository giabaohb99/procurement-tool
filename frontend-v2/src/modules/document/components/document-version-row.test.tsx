import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { VERSION_STATUS, type DocumentVersion } from '../types/document-record'
import { DocumentVersionRow } from './document-version-row'

function ban(overrides: Partial<DocumentVersion> = {}): DocumentVersion {
  return {
    id: 9,
    document_id: 1,
    version_no: '2.0',
    major: 2,
    minor: 0,
    status: VERSION_STATUS.approved,
    status_label: 'Đã duyệt',
    is_locked: true,
    change_kind: 1,
    change_summary: 'Bổ sung Điều 5',
    change_reason: '',
    requires_reconfirm: false,
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
    is_current: true,
    ...overrides,
  }
}

function ve(version: DocumentVersion, onSelect = vi.fn()) {
  render(
    <ul>
      <DocumentVersionRow version={version} viewing={false} onSelect={onSelect} endOfList />
    </ul>,
  )
  return onSelect
}

describe('DocumentVersionRow', () => {
  it('nói rõ mức sửa thay vì để người dùng đoán số bản nhảy kiểu gì', () => {
    ve(ban({ change_kind: 1 }))
    expect(screen.getByText('Sửa lớn')).toBeInTheDocument()
  })

  it('bản đầu tiên không gán mức sửa — chưa sửa gì thì không phải sửa lớn hay nhỏ', () => {
    ve(ban({ change_kind: 0 }))
    expect(screen.queryByText('Sửa lớn')).not.toBeInTheDocument()
    expect(screen.queryByText('Sửa nhỏ')).not.toBeInTheDocument()
  })

  it('trả lý do sửa ra màn hình — hộp thoại đã bắt khai thì phải đọc lại được', () => {
    ve(ban({ change_reason: 'Theo kết luận họp ngày 10/8' }))
    expect(screen.getByText(/Theo kết luận họp ngày 10\/8/)).toBeInTheDocument()
  })

  it('nói ra hệ quả nặng nhất của sửa lớn: người đã đọc bản cũ phải xác nhận lại', () => {
    ve(ban({ requires_reconfirm: true }))
    expect(screen.getByText(/xác nhận đọc lại/)).toBeInTheDocument()
  })

  //  Lỗi thật: `is_locked` chỉ bật lúc DUYỆT XONG, nên bản đang trình duyệt có
  //  `is_locked = false`. Đọc theo cột đó thì dòng «Đang duyệt» ghi "Sửa được",
  //  mở ra gõ xong bấm lưu là ăn 409 của `chan_khi_dang_duyet`.
  it('bản đang trình duyệt vẫn là chỉ đọc, dù is_locked chưa bật', () => {
    ve(
      ban({
        status: VERSION_STATUS.submitted,
        status_label: 'Đang duyệt',
        is_locked: false,
        is_current: false,
      }),
    )
    expect(screen.getByText('Chỉ đọc')).toBeInTheDocument()
    expect(screen.queryByText('Sửa được')).not.toBeInTheDocument()
  })

  it('bản nháp thì ghi sửa được', () => {
    ve(ban({ status: VERSION_STATUS.draft, status_label: 'Nháp', is_locked: false, is_current: false }))
    expect(screen.getByText('Sửa được')).toBeInTheDocument()
  })

  it('bấm vào dòng thì mở đúng phiên bản đó', async () => {
    const onSelect = ve(ban())
    await userEvent.click(screen.getByRole('button', { name: /Mở phiên bản 2\.0/ }))
    expect(onSelect).toHaveBeenCalledOnce()
  })

  //  Nút `?` nằm LỒNG trong vùng bấm của dòng. Bấm nó mà chạy luôn hành vi của
  //  dòng thì người dùng chỉ định đọc giải thích lại bị nhảy sang bản khác.
  it('bấm nút giải thích không kéo theo hành vi mở phiên bản', async () => {
    const onSelect = ve(ban())
    await userEvent.click(screen.getByRole('button', { name: /«Đã duyệt» nghĩa là gì/ }))
    expect(onSelect).not.toHaveBeenCalled()
  })
})
