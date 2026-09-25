import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { FolderDocumentsTable } from './folder-documents-table'
import type * as DocumentSearchModule from '../hooks/use-document-search'
import { useDocumentSearch } from '../hooks/use-document-search'
import {
  useDocFolder,
  useDocFolderTree,
  useLinkDocumentsToFolder,
  useMoveDocFolder,
  useUnlinkDocumentsFromFolder,
} from '../hooks/use-document-folders'
import { useDocuments } from '../hooks/use-documents'
import { FOLDER_ACCESS_LEVEL, type DocFolderDetail } from '../types/document-folder'

vi.mock('../hooks/use-documents', () => ({ useDocuments: vi.fn(), useDeleteDocument: vi.fn(() => ({ mutate: vi.fn() })) }))
//  Giữ HÀM THẬT (`isFullTextQuery`, `MIN_QUERY_LENGTH`) — luật chọn đường tìm
//  phải là luật thật, chỉ giả hook gọi mạng.
vi.mock('../hooks/use-document-search', async (importOriginal) => ({
  ...(await importOriginal<typeof DocumentSearchModule>()),
  useDocumentSearch: vi.fn(),
}))
vi.mock('../hooks/use-document-types', () => ({ useActiveDocumentTypes: vi.fn(() => []) }))
vi.mock('../hooks/use-document-folders', () => ({
  useDocFolder: vi.fn(),
  useDocFolderTree: vi.fn(),
  useLinkDocumentsToFolder: vi.fn(),
  useUnlinkDocumentsFromFolder: vi.fn(),
  useMoveDocFolder: vi.fn(),
  useCreateDocFolder: vi.fn(() => ({ mutateAsync: vi.fn(), isPending: false })),
  useUpdateDocFolder: vi.fn(() => ({ mutate: vi.fn() })),
  useDeleteDocFolder: vi.fn(() => ({ mutate: vi.fn() })),
}))
vi.mock('@/core/authorization/use-permission', () => ({ usePermission: () => ({ can: () => false }) }))

const VIEW_STORAGE_KEY = 'erp.document.folder-view-grid'

function currentFolder(overrides: Partial<DocFolderDetail> = {}): DocFolderDetail {
  return {
    id: 5, company_id: 1, parent_id: 1, kind: 2, kind_label: 'Thư mục', name: 'Hợp đồng', code: '',
    path: '/1/5/', depth: 2, sort_order: 0, status: 1, status_label: 'Đang dùng', document_count: 0,
    document_count_branch: 0, my_level: FOLDER_ACCESS_LEVEL.manage, description: '', breadcrumb: [],
    effective_access: [],
    ...overrides,
  }
}

beforeEach(() => {
  localStorage.clear()
  vi.mocked(useDocuments).mockReturnValue({ data: { items: [], total: 0 }, isLoading: false, isError: false } as unknown as ReturnType<
    typeof useDocuments
  >)
  vi.mocked(useDocumentSearch).mockReturnValue({ data: undefined, isLoading: false, isError: false } as unknown as ReturnType<
    typeof useDocumentSearch
  >)
  vi.mocked(useDocFolder).mockReturnValue({ data: currentFolder() } as unknown as ReturnType<typeof useDocFolder>)
  vi.mocked(useDocFolderTree).mockReturnValue({ data: [] } as unknown as ReturnType<typeof useDocFolderTree>)
  vi.mocked(useLinkDocumentsToFolder).mockReturnValue({ mutate: vi.fn() } as unknown as ReturnType<
    typeof useLinkDocumentsToFolder
  >)
  vi.mocked(useUnlinkDocumentsFromFolder).mockReturnValue({ mutate: vi.fn() } as unknown as ReturnType<
    typeof useUnlinkDocumentsFromFolder
  >)
  vi.mocked(useMoveDocFolder).mockReturnValue({ mutate: vi.fn() } as unknown as ReturnType<typeof useMoveDocFolder>)
})

function renderTable() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <FolderDocumentsTable folderId={5} folderName="Hợp đồng" onSelectFolder={vi.fn()} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('FolderDocumentsTable — chuyển Lưới/Danh sách, nhớ localStorage', () => {
  it('mặc định là chế độ DANH SÁCH (chưa từng bấm) — bảng hiện, nút Lưới chưa được nhấn', () => {
    renderTable()
    expect(screen.getByRole('button', { name: 'Xem dạng danh sách' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Xem dạng lưới' })).toHaveAttribute('aria-pressed', 'false')
  })

  it('bấm «Xem dạng lưới» → đổi ngay và GHI vào localStorage', async () => {
    const user = userEvent.setup()
    renderTable()
    await user.click(screen.getByRole('button', { name: 'Xem dạng lưới' }))

    expect(screen.getByRole('button', { name: 'Xem dạng lưới' })).toHaveAttribute('aria-pressed', 'true')
    expect(localStorage.getItem(VIEW_STORAGE_KEY)).toBe('1')
  })

  it('đã lưu chế độ LƯỚI ở phiên trước → mở lại (dựng component mới) vẫn ở chế độ Lưới', () => {
    localStorage.setItem(VIEW_STORAGE_KEY, '1')
    renderTable()
    expect(screen.getByRole('button', { name: 'Xem dạng lưới' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Xem dạng danh sách' })).toHaveAttribute('aria-pressed', 'false')
  })

  it('bấm lưới rồi bấm danh sách lại → về danh sách, localStorage cập nhật theo', async () => {
    const user = userEvent.setup()
    renderTable()
    await user.click(screen.getByRole('button', { name: 'Xem dạng lưới' }))
    await user.click(screen.getByRole('button', { name: 'Xem dạng danh sách' }))

    expect(screen.getByRole('button', { name: 'Xem dạng danh sách' })).toHaveAttribute('aria-pressed', 'true')
    expect(localStorage.getItem(VIEW_STORAGE_KEY)).toBe('0')
  })
})

describe('FolderDocumentsTable — không có gì chọn thì không có thanh thao tác', () => {
  it('chưa chọn dòng nào → không hiện thanh «n mục đã chọn»', () => {
    renderTable()
    expect(screen.queryByText(/mục đã chọn/)).not.toBeInTheDocument()
  })
})

describe('FolderDocumentsTable — Hàng 2 (tìm/lọc) GIỐNG HỆT ở cả hai chế độ', () => {
  it('ô tìm + nút «Bộ lọc» có mặt ở CẢ Danh sách lẫn Lưới (bug lead bắt 23/09/2026: Lưới từng rớt từng ô một dòng)', async () => {
    const user = userEvent.setup()
    renderTable()

    expect(screen.getByPlaceholderText(/Tìm tên, số hiệu/)).toBeInTheDocument()
    //  Ba ô Loại/Trạng thái/Năm nay GẤP vào popover «Bộ lọc» (chốt dọn gọn lead
    //  24/09/2026 tối) — mở popover trước khi tìm combobox bên trong.
    await user.click(screen.getByRole('button', { name: 'Bộ lọc' }))
    expect(screen.getByRole('combobox', { name: 'Lọc theo loại văn bản' })).toBeInTheDocument()
    await user.keyboard('{Escape}')

    await user.click(screen.getByRole('button', { name: 'Xem dạng lưới' }))

    //  CÙNG một thanh công cụ, không phải một bản rút gọn/khác cấu trúc.
    expect(screen.getByPlaceholderText(/Tìm tên, số hiệu/)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Bộ lọc' }))
    expect(screen.getByRole('combobox', { name: 'Lọc theo loại văn bản' })).toBeInTheDocument()
  })

  it('KHÔNG còn ô Select "Sắp xếp theo" — sắp xếp nay bấm thẳng cột/nhãn (đặc tả A, phản hồi 24/09/2026)', () => {
    renderTable()
    expect(screen.queryByRole('combobox', { name: 'Sắp xếp theo' })).not.toBeInTheDocument()
  })
})
