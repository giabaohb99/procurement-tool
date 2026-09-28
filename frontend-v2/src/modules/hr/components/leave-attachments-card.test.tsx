import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { LeaveAttachment } from '../api/leave-attachment-api'
import { LeaveAttachmentsCard } from './leave-attachments-card'

const state = vi.hoisted(() => ({
  files: [] as LeaveAttachment[],
  requestedId: -1,
}))

vi.mock('../hooks/use-leave-attachments', () => ({
  useLeaveAttachments: (id: number) => {
    state.requestedId = id
    return { data: id > 0 ? state.files : undefined, isLoading: false }
  },
  useUploadLeaveAttachments: () => ({ mutate: vi.fn(), isPending: false }),
  useDeleteLeaveAttachment: () => ({ mutate: vi.fn(), isPending: false }),
}))

const file = (id: number, filename: string, content_type: string): LeaveAttachment => ({
  id,
  file_id: id,
  filename,
  url: '',
  content_type,
  size: 2048,
})

beforeEach(() => {
  state.files = []
  state.requestedId = -1
})

describe('LeaveAttachmentsCard', () => {
  it('asks to save a draft first when the request has no id yet', () => {
    render(<LeaveAttachmentsCard requestId={0} editable />)
    expect(screen.getByText('Lưu nháp để đính kèm tệp.')).toBeInTheDocument()
    //  Không bày vùng thả: chưa có tờ đơn nào để treo tệp vào.
    expect(screen.queryByText(/Kéo tệp vào đây/)).not.toBeInTheDocument()
  })

  it('offers upload and removal while the request is editable', () => {
    state.files = [file(5, 'giay-kham.jpg', 'image/jpeg')]
    render(<LeaveAttachmentsCard requestId={12} editable />)
    expect(state.requestedId).toBe(12)
    expect(screen.getByText(/Kéo tệp vào đây/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Gỡ tệp' })).toBeInTheDocument()
    //  Ảnh được đánh dấu là sẽ in kèm, để người nộp biết trước.
    expect(screen.getByText(/· in kèm ở mặt sau/)).toBeInTheDocument()
  })

  it('is read-only after submission: view and download stay, upload and remove disappear', () => {
    state.files = [file(5, 'giay-ra-vien.pdf', 'application/pdf')]
    render(<LeaveAttachmentsCard requestId={12} editable={false} />)
    expect(screen.queryByText(/Kéo tệp vào đây/)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Gỡ tệp' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Xem trước giay-ra-vien.pdf/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Tải về giay-ra-vien.pdf/ })).toBeInTheDocument()
    //  PDF không in nên không gắn nhãn «in kèm».
    expect(screen.queryByText(/· in kèm ở mặt sau/)).not.toBeInTheDocument()
  })

  it('says the request has no files, not "drop files here", to a read-only viewer', () => {
    render(<LeaveAttachmentsCard requestId={12} editable={false} />)
    expect(screen.getByText('Đơn này không kèm tệp nào.')).toBeInTheDocument()
  })
})
