import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { LineAttachments, type LineAttachmentsLabels } from './line-attachments'

//  Chặn ở tầng HOOK: bài kiểm này chỉ soi chữ trên khung đính kèm và lệnh xóa / tải gửi đi.
const removeFile = vi.fn()
const uploadFiles = vi.fn()
let serverFiles: { id: number; filename: string; content_type: string; url: string }[] = []

vi.mock('../hooks/use-purchase-request-support', () => ({
  usePurchaseRequestAttachments: () => ({ data: serverFiles, isLoading: false }),
  useUploadPurchaseRequestAttachments: () => ({ mutateAsync: uploadFiles, isPending: false }),
  useDeletePurchaseRequestAttachment: () => ({ mutateAsync: removeFile, isPending: false }),
}))

/** Bộ chữ của popup dòng Phiếu khảo sát (v1 `SurveyDetail.tsx`). */
const SURVEY_LABELS: Partial<LineAttachmentsLabels> = {
  uploadMode: 'button',
  uploadLabel: 'Tải file lên',
  uploadingLabel: 'Đang tải…',
  deleteConfirmTitle: 'Xác nhận',
  deleteConfirmDescription: 'Xóa file?',
  deleteConfirmLabel: 'Đồng ý',
}

/** Bộ chữ của popup dòng YCBG (v1 `SurveyRequestDetail.tsx`). */
const SURVEY_REQUEST_LABELS: Partial<LineAttachmentsLabels> = {
  uploadMode: 'dropzone',
  uploadLabel: 'Kéo thả hoặc bấm chọn file',
  uploadHint: 'jpg / png / webp / pdf — có thể nhiều hình',
  pendingUploadHint: 'jpg / png / webp / pdf',
  deleteTooltip: 'Xóa',
  deleteConfirmTitle: 'Xác nhận',
  deleteConfirmDescription: 'Xóa hình/tài liệu này?',
  deleteConfirmLabel: 'Đồng ý',
  removePendingTooltip: 'Bỏ',
}

function renderBox(props: Partial<Parameters<typeof LineAttachments>[0]> = {}) {
  return render(
    <LineAttachments
      entity="survey_line"
      lineId={7}
      canManage
      pendingFiles={[]}
      onPendingFilesChange={vi.fn()}
      {...props}
    />,
  )
}

beforeEach(() => {
  removeFile.mockReset()
  uploadFiles.mockReset()
  serverFiles = [{ id: 31, filename: 'bao-gia.pdf', content_type: 'application/pdf', url: '/f/31' }]
  //  jsdom không có `URL.createObjectURL` — ô xem trước tệp chờ cần nó.
  URL.createObjectURL = vi.fn(() => 'blob:preview')
  URL.revokeObjectURL = vi.fn()
})

describe('LineAttachments — chữ theo từng màn của bản v1 (duoc-CR-741)', () => {
  it('keeps the old v2 wording when a screen passes no labels', () => {
    renderBox()

    expect(screen.getByRole('button', { name: /Thêm tệp/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Xóa tệp' })).toBeInTheDocument()
  })

  it('Phiếu khảo sát: upload button reads Tải file lên and delete asks Xác nhận / Xóa file? with Đồng ý', async () => {
    const user = userEvent.setup()
    renderBox({ labels: SURVEY_LABELS })

    expect(screen.getByRole('button', { name: /Tải file lên/ })).toBeInTheDocument()
    expect(screen.queryByText('Kéo thả hoặc bấm chọn file')).toBeNull()

    await user.click(screen.getByRole('button', { name: 'Xóa tệp' }))
    expect(await screen.findByRole('alertdialog', { name: 'Xác nhận' })).toHaveAccessibleDescription(
      'Xóa file?',
    )
    expect(screen.getByRole('button', { name: 'Hủy' })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Đồng ý' }))
    expect(removeFile).toHaveBeenCalledWith(31)
  })

  it('does not delete when the user backs out with Hủy', async () => {
    const user = userEvent.setup()
    renderBox({ labels: SURVEY_LABELS })

    await user.click(screen.getByRole('button', { name: 'Xóa tệp' }))
    await user.click(await screen.findByRole('button', { name: 'Hủy' }))

    expect(removeFile).not.toHaveBeenCalled()
  })

  it('YCBG: drop zone instead of a button, delete tooltip Xóa, confirm Xác nhận / Xóa hình/tài liệu này?', async () => {
    const user = userEvent.setup()
    renderBox({ entity: 'survey_request_line', labels: SURVEY_REQUEST_LABELS })

    expect(screen.queryByRole('button', { name: /Tải file lên|Thêm tệp/ })).toBeNull()
    expect(screen.getByRole('button', { name: 'Kéo thả hoặc bấm chọn file' })).toBeInTheDocument()
    expect(screen.getByText('jpg / png / webp / pdf — có thể nhiều hình')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Xóa' }))
    expect(await screen.findByRole('alertdialog', { name: 'Xác nhận' })).toHaveAccessibleDescription(
      'Xóa hình/tài liệu này?',
    )
    await user.click(screen.getByRole('button', { name: 'Đồng ý' }))
    expect(removeFile).toHaveBeenCalledWith(31)
  })

  it('YCBG unsaved line: files go to the pending tray, each with a Bỏ button', async () => {
    const user = userEvent.setup()
    const onPendingFilesChange = vi.fn()
    const pending = new File(['x'], 'anh.png', { type: 'image/png' })
    serverFiles = []
    renderBox({
      lineId: 0,
      entity: 'survey_request_line',
      labels: SURVEY_REQUEST_LABELS,
      pendingFiles: [pending],
      onPendingFilesChange,
    })

    //  Dòng chưa lưu: dòng gợi ý ngắn, không có "có thể nhiều hình".
    expect(screen.getByText('jpg / png / webp / pdf')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Bỏ' }))
    expect(onPendingFilesChange).toHaveBeenCalledWith([])
    expect(uploadFiles).not.toHaveBeenCalled()
  })

  it('a read-only viewer sees neither the drop zone nor any delete button', () => {
    renderBox({ canManage: false, labels: SURVEY_REQUEST_LABELS })

    expect(screen.queryByRole('button', { name: 'Kéo thả hoặc bấm chọn file' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Xóa' })).toBeNull()
  })
})
