import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'
import type { HeadcountPlanDocumentLink } from '../types/headcount-plan'
import { HeadcountPlanLinkedDocuments } from './headcount-plan-linked-documents'

const apiGet = vi.fn()
const uploadBasisDocument = vi.fn()

vi.mock('../api/headcount-plan-api', () => ({
  headcountPlanApi: { uploadBasisDocument: (...args: unknown[]) => uploadBasisDocument(...args) },
}))

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return { ...actual, apiGet: (...args: unknown[]) => apiGet(...args) }
})

const DOCS: HeadcountPlanDocumentLink[] = [
  { document_id: 1, can_read: true, code: '12/QĐ-BGĐ', title: 'Duyệt ngân sách nhân sự 2026', status: 4 },
  { document_id: 2, can_read: false },
  { document_id: 3, can_read: false, deleted: true },
]

function build(props: Partial<React.ComponentProps<typeof HeadcountPlanLinkedDocuments>> = {}) {
  const onChange = vi.fn()
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <HeadcountPlanLinkedDocuments documents={DOCS} onChange={onChange} readOnly={false} canSearch {...props} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
  return onChange
}

beforeEach(() => {
  apiGet.mockReset().mockResolvedValue({ items: [], total: 0 })
  uploadBasisDocument.mockReset()
})

describe('linked documents', () => {
  it('shows number, title, status label and an open link for a readable document', () => {
    build()
    expect(screen.getByText('12/QĐ-BGĐ')).toBeInTheDocument()
    expect(screen.getByText('Duyệt ngân sách nhân sự 2026')).toBeInTheDocument()
    expect(screen.getByText('Có hiệu lực')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Mở/ })).toHaveAttribute('href', '/document/documents/1')
  })

  it('says "not allowed" for an unreadable document and never shows any of its data', () => {
    build()
    expect(screen.getByText('Văn bản bạn chưa được xem')).toBeInTheDocument()
    expect(screen.getAllByRole('link')).toHaveLength(1)
  })

  it('says "deleted" for a deleted document', () => {
    build()
    expect(screen.getByText('Văn bản đã xóa')).toBeInTheDocument()
  })

  it('removing one link keeps the unreadable ones — PUT replaces the whole list', () => {
    const onChange = build()
    fireEvent.click(screen.getAllByRole('button', { name: 'Gỡ văn bản khỏi kế hoạch' })[0])
    expect(onChange).toHaveBeenCalledWith([DOCS[1], DOCS[2]])
  })

  it('does not search the Document module at all without document.read (would 403)', () => {
    build({ canSearch: false })
    expect(screen.queryByLabelText('Tìm văn bản để gắn')).not.toBeInTheDocument()
    expect(screen.getByText(/chưa có quyền xem phân hệ Văn bản/)).toBeInTheDocument()
    expect(apiGet).not.toHaveBeenCalled()
  })

  it('does not query for a 1-character search, then adds a picked result without duplicates', async () => {
    apiGet.mockResolvedValue({
      items: [
        { id: 1, display_code: '12/QĐ-BGĐ', title: 'Đã gắn rồi', status: 4, status_label: 'Có hiệu lực' },
        { id: 9, display_code: '05/TTr', title: 'Tờ trình tuyển dụng', status: 4, status_label: 'Có hiệu lực' },
      ],
      total: 2,
    })
    const onChange = build()
    const input = screen.getByLabelText('Tìm văn bản để gắn')
    fireEvent.change(input, { target: { value: 't' } })
    await new Promise((r) => setTimeout(r, 450))
    expect(apiGet).not.toHaveBeenCalled()
    fireEvent.change(input, { target: { value: 'tờ trình' } })
    const pick = await screen.findByRole('button', { name: /Tờ trình tuyển dụng/ })
    expect(screen.queryByRole('button', { name: /Đã gắn rồi/ })).not.toBeInTheDocument()
    fireEvent.click(pick)
    expect(onChange).toHaveBeenCalledWith([
      ...DOCS,
      { document_id: 9, code: '05/TTr', title: 'Tờ trình tuyển dụng', status: 4, status_label: 'Có hiệu lực', can_read: true },
    ])
  })

  it('renders no remove buttons and no search when read-only', () => {
    build({ readOnly: true })
    expect(screen.queryByRole('button', { name: 'Gỡ văn bản khỏi kế hoạch' })).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Tìm văn bản để gắn')).not.toBeInTheDocument()
  })

  describe('upload a basis file', () => {
    const pdf = () => new File(['%PDF-1.4'], 'quyet-dinh.pdf', { type: 'application/pdf' })
    const pick = (file: File) =>
      fireEvent.change(screen.getByLabelText('Chọn tệp căn cứ để tải lên'), { target: { files: [file] } })

    it('adds the document created from the file, with number, title and an open link', async () => {
      const created = { document_id: 77, can_read: true, code: 'DEGO-CCKHNS-001', title: 'Căn cứ kế hoạch nhân sự – quyet-dinh.pdf', status: 1 }
      uploadBasisDocument.mockResolvedValue(created)
      const onChange = build()
      pick(pdf())
      await waitFor(() => expect(onChange).toHaveBeenCalledWith([...DOCS, created]))
      expect(uploadBasisDocument.mock.calls[0][0].name).toBe('quyet-dinh.pdf')
    })

    it('shows the progress percentage while uploading and locks the button', async () => {
      let report: (n: number) => void = () => undefined
      uploadBasisDocument.mockImplementation(
        (_file: File, onProgress: (n: number) => void) =>
          new Promise(() => {
            report = onProgress
          }),
      )
      build()
      pick(pdf())
      const busy = await screen.findByRole('button', { name: /Đang tải lên/ })
      expect(busy).toBeDisabled()
      report(42)
      expect(await screen.findByRole('button', { name: 'Đang tải lên… 42%' })).toBeInTheDocument()
    })

    it('shows the Vietnamese server error and does not change the list', async () => {
      uploadBasisDocument.mockRejectedValue({ response: { data: { success: false, error: { message: 'Định dạng .exe không được phép' } } } })
      const onChange = build()
      pick(new File(['MZ'], 'chay.exe'))
      expect(await screen.findByRole('alert')).toHaveTextContent('Định dạng .exe không được phép')
      expect(onChange).not.toHaveBeenCalled()
    })

    it('refuses a file over 50 MB without calling the server', () => {
      const big = new File(['x'], 'to.pdf')
      Object.defineProperty(big, 'size', { value: 51 * 1024 * 1024 })
      build()
      pick(big)
      expect(screen.getByRole('alert')).toHaveTextContent('lớn hơn 50 MB')
      expect(uploadBasisDocument).not.toHaveBeenCalled()
    })

    it('has no upload button when read-only or without document.read', () => {
      build({ readOnly: true })
      expect(screen.queryByRole('button', { name: 'Tải tệp lên' })).not.toBeInTheDocument()
    })

    it('has no upload button without document.read', () => {
      build({ canSearch: false })
      expect(screen.queryByRole('button', { name: 'Tải tệp lên' })).not.toBeInTheDocument()
    })
  })
})
