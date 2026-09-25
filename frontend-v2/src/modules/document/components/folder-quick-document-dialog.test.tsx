import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { useEffect } from 'react'
import type { UseFormReturn } from 'react-hook-form'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { DocumentRecordFormValues } from '../schemas/document-record-schema'
import { DOCUMENT_CONTENT_MODE } from '../types/document-record'
import { FolderQuickDocumentDialog } from './folder-quick-document-dialog'

const { mutateAsyncMock, sendMock, toastError, fieldPreset } = vi.hoisted(() => ({
  mutateAsyncMock: vi.fn(),
  sendMock: vi.fn(async () => undefined),
  toastError: vi.fn(),
  //  Tên người dùng đã gõ sẵn trước khi chọn tệp — `''` = chưa gõ gì.
  fieldPreset: { title: '', folderId: 0 },
}))

vi.mock('sonner', () => ({ toast: { error: toastError, success: vi.fn() } }))
vi.mock('@/core/auth/use-auth', () => ({
  useAuth: () => ({ user: { id: 1, company_id: 7, department_id: 3, employee_id: 9 } }),
}))
vi.mock('../hooks/use-documents', () => ({
  useSaveDocument: () => ({ mutateAsync: mutateAsyncMock, isPending: false }),
}))
vi.mock('../helpers/send-pending-access-and-files', () => ({
  sendPendingAccessAndFiles: sendMock,
}))
vi.mock('./document-access-fields', () => ({ DocumentAccessFields: () => null }))
vi.mock('../hooks/use-document-approval-preview', () => ({
  useDocumentApprovalPreview: () => ({ data: undefined, isLoading: false }),
}))
vi.mock('./document-approver-preview-line', () => ({ DocumentApproverPreviewLine: () => null }))
//  Ô chọn thật đã có test riêng của `SearchSelect` — ở đây chỉ điền ô CÒN
//  THIẾU (loại văn bản); pháp nhân/phòng/người chịu trách nhiệm phải tự lên
//  từ thư mục + hồ sơ người đăng nhập, đó chính là thứ cần kiểm.
vi.mock('./folder-quick-document-fields', () => ({
  FolderQuickDocumentFields: ({
    form,
    onFolderIdChange,
  }: {
    form: UseFormReturn<DocumentRecordFormValues>
    onFolderIdChange: (id: number) => void
  }) => {
    useEffect(() => {
      form.setValue('doc_type_id', 4)
      if (fieldPreset.title) form.setValue('title', fieldPreset.title)
      //  Mô phỏng người dùng đổi ô «Lưu vào thư mục» sang thư mục khác.
      if (fieldPreset.folderId) onFolderIdChange(fieldPreset.folderId)
      // eslint-disable-next-line react-hooks/exhaustive-deps -- chỉ điền một lần lúc mount
    }, [])
    return null
  },
}))

function renderDialog(folderCompanyId = 2) {
  const onOpenChange = vi.fn()
  render(
    <MemoryRouter>
      <FolderQuickDocumentDialog
        open
        onOpenChange={onOpenChange}
        folderId={23}
        folderCompanyId={folderCompanyId}
      />
    </MemoryRouter>,
  )
  return { onOpenChange }
}

function pickFiles(...names: string[]) {
  const input = document.querySelector<HTMLInputElement>('input[type="file"]')
  if (!input) throw new Error('không thấy ô chọn tệp')
  fireEvent.change(input, {
    target: { files: names.map((name) => new File(['x'], name, { type: 'application/pdf' })) },
  })
}

function submit() {
  fireEvent.click(screen.getByRole('button', { name: 'Tạo văn bản' }))
}

describe('FolderQuickDocumentDialog', () => {
  beforeEach(() => {
    mutateAsyncMock.mockReset()
    mutateAsyncMock.mockResolvedValue({ id: 101, current_version_id: 501 })
    sendMock.mockClear()
    toastError.mockClear()
    fieldPreset.title = ''
    fieldPreset.folderId = 0
  })

  it('refuses to create without any file — a no-compose document with no file is an empty shell', async () => {
    fieldPreset.title = 'Có tên, không tệp'
    renderDialog()
    submit()
    await waitFor(() => expect(toastError).toHaveBeenCalled())
    expect(mutateAsyncMock).not.toHaveBeenCalled()
  })

  it('creates a files-only document inside the current folder, then uploads to version 1.0', async () => {
    const { onOpenChange } = renderDialog()
    pickFiles('Hop-dong-ABC.signed.pdf', 'Phu-luc.xlsx')
    submit()

    await waitFor(() => expect(mutateAsyncMock).toHaveBeenCalledTimes(1))
    const { values } = mutateAsyncMock.mock.calls[0][0]
    expect(values).toMatchObject({
      //  Chỉ bỏ ĐUÔI cuối — dấu chấm giữa tên là một phần của tên.
      title: 'Hop-dong-ABC.signed',
      doc_type_id: 4,
      company_id: 2,
      department_id: 3,
      owner_employee_id: 9,
      folder_ids: [23],
      primary_folder_id: 23,
      content_mode: DOCUMENT_CONTENT_MODE.files,
      content_html: '',
    })
    await waitFor(() => expect(sendMock).toHaveBeenCalledTimes(1))
    const [documentId, versionId, access, files] = sendMock.mock.calls[0] as unknown as [
      number,
      number,
      unknown[],
      File[],
    ]
    expect([documentId, versionId, access]).toEqual([101, 501, []])
    expect(files.map((file) => file.name)).toEqual(['Hop-dong-ABC.signed.pdf', 'Phu-luc.xlsx'])
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false))
  })

  it('saves into the folder picked in «Lưu vào thư mục», not the folder being viewed', async () => {
    fieldPreset.folderId = 31
    renderDialog()
    pickFiles('a.pdf')
    submit()
    await waitFor(() => expect(mutateAsyncMock).toHaveBeenCalledTimes(1))
    expect(mutateAsyncMock.mock.calls[0][0].values).toMatchObject({
      folder_ids: [31],
      primary_folder_id: 31,
    })
  })

  it('does not overwrite a title the user already typed', async () => {
    fieldPreset.title = 'Hợp đồng mua phân bón 2026'
    renderDialog()
    pickFiles('scan_001.pdf')
    submit()
    await waitFor(() => expect(mutateAsyncMock).toHaveBeenCalledTimes(1))
    expect(mutateAsyncMock.mock.calls[0][0].values.title).toBe('Hợp đồng mua phân bón 2026')
  })

  it('falls back to the user company when the folder belongs to no company (free folder, id 0)', async () => {
    renderDialog(0)
    pickFiles('a.pdf')
    submit()
    await waitFor(() => expect(mutateAsyncMock).toHaveBeenCalledTimes(1))
    expect(mutateAsyncMock.mock.calls[0][0].values.company_id).toBe(7)
  })

  it('a file named only by its extension still yields a non-empty title', async () => {
    renderDialog()
    pickFiles('.pdf')
    submit()
    await waitFor(() => expect(mutateAsyncMock).toHaveBeenCalledTimes(1))
    expect(mutateAsyncMock.mock.calls[0][0].values.title).toBe('.pdf')
  })

  //  Bẫy thứ tư CR-317: bấm liền tay hai lần ra hai văn bản.
  it('a double click creates exactly one document', async () => {
    let resolve: (value: unknown) => void = () => {}
    mutateAsyncMock.mockReturnValue(new Promise((r) => (resolve = r)))
    renderDialog()
    pickFiles('a.pdf')
    submit()
    submit()
    await waitFor(() => expect(mutateAsyncMock).toHaveBeenCalled())
    resolve({ id: 1, current_version_id: 2 })
    await waitFor(() => expect(sendMock).toHaveBeenCalledTimes(1))
    expect(mutateAsyncMock).toHaveBeenCalledTimes(1)
  })

  it('keeps the dialog open and says why when the server rejects the create', async () => {
    mutateAsyncMock.mockRejectedValue(new Error('Loại văn bản đã ngừng dùng'))
    const { onOpenChange } = renderDialog()
    pickFiles('a.pdf')
    submit()
    await waitFor(() => expect(toastError).toHaveBeenCalled())
    expect(sendMock).not.toHaveBeenCalled()
    expect(onOpenChange).not.toHaveBeenCalledWith(false)
    //  Cờ chặn bấm đúp phải mở lại — không thì nút chết cứng tới lúc đóng hộp.
    submit()
    await waitFor(() => expect(mutateAsyncMock).toHaveBeenCalledTimes(2))
  })
})
