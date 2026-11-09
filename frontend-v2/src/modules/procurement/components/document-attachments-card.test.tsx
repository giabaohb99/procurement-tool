import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { AttachmentFile } from '../api/purchase-request-support-api'
import { DocumentAttachmentsCard } from './document-attachments-card'

const removeFile = vi.fn()
let files: AttachmentFile[] = []

//  Thẻ này nói về CHỮ và hộp hỏi lại, không nói về mạng — cắt các lượt gọi API.
vi.mock('../hooks/use-purchase-request-support', () => ({
  usePurchaseRequestAttachments: () => ({ data: files, isLoading: false, isError: false }),
  useDocumentTypes: () => ({ data: [] }),
  useUploadPurchaseRequestAttachments: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useDeletePurchaseRequestAttachment: () => ({ mutateAsync: removeFile, isPending: false }),
  useUploadDocumentBatches: () => ({ mutateAsync: vi.fn(), isPending: false }),
}))

function file(overrides: Partial<AttachmentFile> = {}): AttachmentFile {
  return {
    id: 71,
    file_id: 71,
    filename: 'hoa-don.pdf',
    url: '',
    content_type: 'application/pdf',
    size: 2048,
    sha256: '',
    doc_type: '',
    entity: 'purchase_order',
    entity_id: 5,
    ...overrides,
  }
}

function renderBaseCard(props: Partial<Parameters<typeof DocumentAttachmentsCard>[0]> = {}) {
  return render(
    <MemoryRouter>
      <DocumentAttachmentsCard entity="purchase_order" entityId={5} canManage {...props} />
    </MemoryRouter>,
  )
}

/** duoc-CR-741 — chữ trên thẻ chứng từ ở màn Thu mua (`v1Wording`) theo đúng bản v1. */
describe('DocumentAttachmentsCard — chữ theo bản v1', () => {
  beforeEach(() => {
    files = [file()]
    removeFile.mockReset()
  })

  function renderCard(props: Partial<Parameters<typeof DocumentAttachmentsCard>[0]> = {}) {
    return renderBaseCard({ v1Wording: true, ...props })
  }

  it('names the chain link and the per-folder upload like v1, keeps the v2 zip button', () => {
    renderCard()
    expect(screen.getByRole('link', { name: 'Chuỗi chứng từ (PYC/PKS)' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Tải chuỗi chứng từ (.zip)' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Upload thêm file cho mục này' })).toBeInTheDocument()
  })

  it('offers no chain buttons outside the purchase order', () => {
    renderCard({ entity: 'purchase_request' })
    expect(screen.queryByRole('link', { name: 'Chuỗi chứng từ (PYC/PKS)' })).toBeNull()
  })

  it('asks the v1 question before deleting a file, and Hủy keeps it', async () => {
    renderCard()
    await userEvent.click(screen.getByRole('button', { name: 'Xóa tệp' }))
    const dialog = screen.getByRole('alertdialog')
    expect(within(dialog).getByText('Xóa file "hoa-don.pdf"?')).toBeInTheDocument()
    await userEvent.click(within(dialog).getByRole('button', { name: 'Hủy' }))
    expect(removeFile).not.toHaveBeenCalled()

    await userEvent.click(screen.getByRole('button', { name: 'Xóa tệp' }))
    await userEvent.click(screen.getByRole('button', { name: 'Đồng ý' }))
    expect(removeFile).toHaveBeenCalledWith(71)
  })

  it('upload dialog row tooltip uses the v1 word', async () => {
    renderCard()
    await userEvent.click(screen.getByRole('button', { name: 'Upload chứng từ' }))
    expect(screen.getByTitle('Xóa dòng')).toBeInTheDocument()
  })
})

/** duoc-CR-741 — đổi tình trạng hồ sơ bằng menu ở tiêu đề thẻ như bản v1 (chỉ Thu mua). */
describe('DocumentAttachmentsCard — hồ sơ chứng từ', () => {
  beforeEach(() => {
    files = []
  })

  function renderCard(props: Partial<Parameters<typeof DocumentAttachmentsCard>[0]> = {}) {
    return renderBaseCard({ v1Wording: true, ...props })
  }

  it('hides the dossier block when no status is passed (YCMH, phiếu khảo sát)', () => {
    renderCard({ entity: 'purchase_request' })
    expect(screen.queryByText('Hồ sơ chứng từ:')).toBeNull()
  })

  it('shows a plain badge to readers without write access', () => {
    renderCard({ documentStatus: 'partial' })
    expect(screen.getByText('Hồ sơ chứng từ:')).toBeInTheDocument()
    expect(screen.getByText('Đã có thông tin chứng từ')).toBeInTheDocument()
    expect(screen.queryByTitle('Bấm để thay đổi trạng thái hồ sơ chứng từ')).toBeNull()
  })

  it('lets a writer pick a new status, and picking the current one sends nothing', async () => {
    const onDocumentStatusChange = vi.fn()
    renderCard({ documentStatus: 'none', documentStatusEditable: true, onDocumentStatusChange })

    await userEvent.click(screen.getByTitle('Bấm để thay đổi trạng thái hồ sơ chứng từ'))
    expect(screen.getByText('Cập nhật hồ sơ chứng từ')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('menuitem', { name: 'Chưa có chứng từ' }))
    expect(onDocumentStatusChange).not.toHaveBeenCalled()

    await userEvent.click(screen.getByTitle('Bấm để thay đổi trạng thái hồ sơ chứng từ'))
    await userEvent.click(screen.getByRole('menuitem', { name: 'Đã đủ chứng từ' }))
    expect(onDocumentStatusChange).toHaveBeenCalledWith('full')
  })
})

/**
 * Rà mã duoc-CR-741: đổi chữ ở thẻ dùng chung từng lan sang Đề nghị thanh toán, Duyệt dấu,
 * Sản xuất, Hải quan. Đại ca chốt chỉ Thu mua theo chữ v1 — màn khác phải y như trước.
 */
describe('DocumentAttachmentsCard — màn ngoài Thu mua giữ chữ v2', () => {
  beforeEach(() => {
    files = [file({ entity: 'payment_request' })]
    removeFile.mockReset()
  })

  it('payment request keeps the read-only "Hồ sơ:" badge next to the title, no menu', () => {
    renderBaseCard({ entity: 'payment_request', documentStatus: 'partial' })
    expect(screen.getByText('Hồ sơ:')).toBeInTheDocument()
    expect(screen.queryByText('Hồ sơ chứng từ:')).toBeNull()
    expect(screen.queryByTitle('Bấm để thay đổi trạng thái hồ sơ chứng từ')).toBeNull()
  })

  it('a writer outside procurement still gets no status menu even if the props leak in', () => {
    renderBaseCard({
      entity: 'payment_request',
      documentStatus: 'none',
      documentStatusEditable: true,
      onDocumentStatusChange: vi.fn(),
    })
    expect(screen.queryByTitle('Bấm để thay đổi trạng thái hồ sơ chứng từ')).toBeNull()
  })

  it('keeps the v2 folder upload text and the old delete question with a "Xóa" button', async () => {
    renderBaseCard({ entity: 'payment_request' })
    expect(screen.getByRole('button', { name: 'Upload thêm tệp cho mục này' })).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Xóa tệp' }))
    const dialog = screen.getByRole('alertdialog')
    expect(within(dialog).getByText('Xóa "hoa-don.pdf"?')).toBeInTheDocument()
    expect(within(dialog).queryByRole('button', { name: 'Đồng ý' })).toBeNull()
    await userEvent.click(within(dialog).getByRole('button', { name: 'Xóa' }))
    expect(removeFile).toHaveBeenCalledWith(71)
  })

  it('upload dialog keeps the v2 row tooltip', async () => {
    renderBaseCard({ entity: 'payment_request' })
    await userEvent.click(screen.getByRole('button', { name: 'Upload chứng từ' }))
    expect(screen.getByTitle('Xóa mục này')).toBeInTheDocument()
    expect(screen.queryByTitle('Xóa dòng')).toBeNull()
  })

  it('a purchase order rendered without the flag keeps the old chain link name', () => {
    renderBaseCard()
    expect(screen.getByRole('link', { name: 'Xem cả chuỗi chứng từ' })).toBeInTheDocument()
  })
})
