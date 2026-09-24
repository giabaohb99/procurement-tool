import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { DocumentFilesTab } from './document-files-tab'
import { useDocumentFiles, useUploadDocumentFile } from '../hooks/use-document-files'
import type { DocumentVersionFile } from '../api/document-api'

/**
 * `DocumentFileList` / `DocumentFileViewerLayout` là hai component RIÊNG, có
 * việc riêng của chúng (bảng, khung xem + cây). Bài kiểm ở đây chỉ canh HỢP
 * ĐỒNG RẼ NHÁNH của `DocumentFilesTab` (0 / 1 / nhiều tệp, trạng thái URL) —
 * mock hai component con để không phụ thuộc vào chi tiết bên trong chúng
 * (viewer còn gọi `/api/attachments/{id}/view` thật, không việc gì bài này
 * phải lo tới đó).
 */
vi.mock('./document-file-list', () => ({
  DocumentFileList: ({ files, onOpen }: { files: DocumentVersionFile[]; onOpen: (f: DocumentVersionFile) => void }) => (
    <div data-testid="file-list">
      <span>Danh sách {files.length} tệp</span>
      {files.map((file) => (
        <button key={file.id} type="button" onClick={() => onOpen(file)}>
          Mở {file.filename}
        </button>
      ))}
    </div>
  ),
}))

vi.mock('./document-file-viewer-layout', () => ({
  DocumentFileViewerLayout: ({
    files,
    selectedId,
    onBackToList,
  }: {
    files: DocumentVersionFile[]
    selectedId: number
    onBackToList?: () => void
  }) => (
    <div data-testid="file-viewer">
      <span>Đang xem tệp {files.find((f) => f.id === selectedId)?.filename}</span>
      {onBackToList && (
        <button type="button" onClick={onBackToList}>
          Về danh sách
        </button>
      )}
    </div>
  ),
}))

vi.mock('../hooks/use-document-files', () => ({
  useDocumentFiles: vi.fn(),
  useUploadDocumentFile: vi.fn(),
}))

function file(overrides: Partial<DocumentVersionFile> = {}): DocumentVersionFile {
  return {
    id: 1,
    file_id: 1,
    filename: 'a.pdf',
    url: '',
    content_type: 'application/pdf',
    size: 1024,
    sha256: '',
    doc_type: '',
    entity: 'document_version',
    entity_id: 10,
    version_id: 10,
    version_no: '1.0',
    is_current_version: true,
    created_by_name: 'Người Test',
    created_at: '2026-09-01T00:00:00',
    ...overrides,
  }
}

function mockFiles(items: DocumentVersionFile[], overrides: Partial<ReturnType<typeof useDocumentFiles>> = {}) {
  vi.mocked(useDocumentFiles).mockReturnValue({
    data: items,
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
    ...overrides,
  } as unknown as ReturnType<typeof useDocumentFiles>)
}

const uploadMutate = vi.fn()

function renderTab(
  props: Partial<Parameters<typeof DocumentFilesTab>[0]> = {},
  initialPath = '/document/documents/1?tab=files',
) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[initialPath]}>
        <DocumentFilesTab
          documentId={1}
          currentVersionId={10}
          documentCode="DEGO-QC-001"
          canWrite
          {...props}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(useUploadDocumentFile).mockReturnValue({
    mutate: uploadMutate,
    isPending: false,
  } as unknown as ReturnType<typeof useUploadDocumentFile>)
  uploadMutate.mockReset()
})

describe('DocumentFilesTab — rẽ theo số tệp', () => {
  it('0 tệp + có quyền sửa → trạng thái rỗng kèm vùng tải lên', () => {
    mockFiles([])
    renderTab({ canWrite: true })
    expect(screen.getByText('Văn bản chưa có tệp đính kèm nào.')).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /Kéo thả tệp vào đây hoặc bấm để tải lên/ }),
    ).toBeInTheDocument()
  })

  it('0 tệp + KHÔNG có quyền sửa → không có vùng tải lên (chỉ đọc)', () => {
    mockFiles([])
    renderTab({ canWrite: false })
    expect(screen.getByText('Văn bản chưa có tệp đính kèm nào.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Kéo thả tệp/ })).not.toBeInTheDocument()
  })

  it('0 tệp nhưng CHƯA CÓ phiên bản (currentVersionId null) → không bày nút tải, chưa có chỗ để gắn tệp', () => {
    mockFiles([])
    renderTab({ canWrite: true, currentVersionId: null })
    expect(screen.queryByRole('button', { name: /Kéo thả tệp/ })).not.toBeInTheDocument()
  })

  it('1 tệp → mở THẲNG khung xem, không bày danh sách', () => {
    mockFiles([file({ id: 5, filename: 'hop-dong.pdf' })])
    renderTab()
    expect(screen.getByTestId('file-viewer')).toBeInTheDocument()
    expect(screen.getByText('Đang xem tệp hop-dong.pdf')).toBeInTheDocument()
    expect(screen.queryByTestId('file-list')).not.toBeInTheDocument()
  })

  it('nhiều tệp, KHÔNG có `file=` trên URL → bày danh sách', () => {
    mockFiles([file({ id: 1, filename: 'a.pdf' }), file({ id: 2, filename: 'b.pdf' })])
    renderTab({}, '/document/documents/1?tab=files')
    expect(screen.getByTestId('file-list')).toBeInTheDocument()
    expect(screen.getByText('Danh sách 2 tệp')).toBeInTheDocument()
  })

  it('nhiều tệp, CÓ `file=<id>` hợp lệ trên URL → mở thẳng khung xem đúng tệp đó (dán link)', () => {
    mockFiles([file({ id: 1, filename: 'a.pdf' }), file({ id: 2, filename: 'b.pdf' })])
    renderTab({}, '/document/documents/1?tab=files&file=2')
    expect(screen.getByTestId('file-viewer')).toBeInTheDocument()
    expect(screen.getByText('Đang xem tệp b.pdf')).toBeInTheDocument()
  })

  it('nhiều tệp, `file=` trỏ tới id KHÔNG tồn tại → rơi về danh sách, không nổ', () => {
    mockFiles([file({ id: 1, filename: 'a.pdf' }), file({ id: 2, filename: 'b.pdf' })])
    renderTab({}, '/document/documents/1?tab=files&file=999')
    expect(screen.getByTestId('file-list')).toBeInTheDocument()
  })

  it('bấm một dòng trong danh sách → chuyển sang khung xem đúng tệp', async () => {
    const user = userEvent.setup()
    mockFiles([file({ id: 1, filename: 'a.pdf' }), file({ id: 2, filename: 'b.pdf' })])
    renderTab({}, '/document/documents/1?tab=files')

    await user.click(screen.getByRole('button', { name: 'Mở b.pdf' }))
    expect(screen.getByText('Đang xem tệp b.pdf')).toBeInTheDocument()
  })

  it('bấm «Về danh sách» trong khung xem → quay lại bảng danh sách', async () => {
    const user = userEvent.setup()
    mockFiles([file({ id: 1, filename: 'a.pdf' }), file({ id: 2, filename: 'b.pdf' })])
    renderTab({}, '/document/documents/1?tab=files&file=1')

    await user.click(screen.getByRole('button', { name: 'Về danh sách' }))
    expect(screen.getByTestId('file-list')).toBeInTheDocument()
  })
})

describe('DocumentFilesTab — tải/lỗi', () => {
  it('đang tải thì hiện khung xương, không gọi tới hai component con', () => {
    mockFiles([], { isLoading: true, data: undefined })
    renderTab()
    expect(screen.queryByTestId('file-list')).not.toBeInTheDocument()
    expect(screen.queryByTestId('file-viewer')).not.toBeInTheDocument()
  })

  it('lỗi tải danh sách → báo lỗi kèm nút thử lại, không hiểu nhầm thành "0 tệp"', () => {
    mockFiles([], { isError: true })
    renderTab()
    expect(screen.getByText('Chưa tải được danh sách tệp')).toBeInTheDocument()
    expect(screen.queryByText('Văn bản chưa có tệp đính kèm nào.')).not.toBeInTheDocument()
  })
})

describe('DocumentFilesTab — tải tệp lên lúc rỗng', () => {
  it('chọn tệp qua vùng thả gọi đúng mutation tải lên', async () => {
    const user = userEvent.setup()
    mockFiles([])
    renderTab({ canWrite: true, currentVersionId: 77 })

    const dropzone = screen.getByRole('button', { name: /Kéo thả tệp vào đây hoặc bấm để tải lên/ })
    const input = dropzone.querySelector('input[type="file"]') as HTMLInputElement
    const picked = new File(['noi dung'], 'scan.pdf', { type: 'application/pdf' })
    await user.upload(input, picked)

    expect(uploadMutate).toHaveBeenCalledWith([picked])
  })
})
