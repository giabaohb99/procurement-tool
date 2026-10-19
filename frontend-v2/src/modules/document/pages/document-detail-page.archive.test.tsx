import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import fixture from './__fixtures__/archive-document-26.json'
import { DocumentDetailPage } from './document-detail-page'

/**
 * duoc-CR-640 — render THẬT trang chi tiết với dữ liệu thật của một bản lưu trữ HĐLĐ (văn bản chỉ gồm tệp, bản nháp,
 * 1 tệp) để biết người GHI thấy gì và người chỉ ĐỌC thấy gì.
 */
const state = vi.hoisted(() => ({ write: true, isArchive: true, patch: [] as unknown[] }))

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<Record<string, unknown>>()
  const data = (url: string) => {
    const fx = fixture as Record<string, unknown>
    if (url.endsWith('/permissions')) return { ...(fx.permissions as object), write: state.write, is_archive: state.isArchive }
    if (/\/versions\/\d+$/.test(url)) return fx.version
    if (url.endsWith('/versions')) return fx.versions
    if (url.endsWith('/attachments')) return fx.files
    if (/\/api\/documents\/\d+$/.test(url)) return fx.record
    return []
  }
  return {
    ...actual,
    apiGet: vi.fn(async (url: string) => data(url)),
    apiPatch: vi.fn(async (url: string, body: unknown) => {
      state.patch.push({ url, body })
      return (fixture as Record<string, unknown>).record
    }),
  }
})
vi.mock('../components/document-file-viewer-layout', () => ({
  DocumentFileViewerLayout: () => <div data-testid="viewer" />,
}))
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAny: () => true }),
}))
vi.mock('@/core/auth/use-auth', () => ({
  useAuth: () => ({ user: { id: 1, employee_id: 1, company_id: 1, department_id: 1, signature: '' } }),
}))

function renderPage(search = '') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/document/documents/26${search}`]}>
        <Routes>
          <Route path="/document/documents/:id" element={<DocumentDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('DocumentDetailPage — bản lưu trữ HĐLĐ chỉ gồm tệp', () => {
  beforeEach(() => {
    state.write = true
    state.isArchive = true
    state.patch = []
  })

  async function ready() {
    renderPage()
    await waitFor(() => expect(screen.getByRole('tab', { name: /Thông tin/ })).toBeInTheDocument())
    await waitFor(() => expect(screen.queryByRole('tab', { name: /Quan hệ/ })).not.toBeInTheDocument())
  }

  it('người GHI: tab chỉ có Văn bản / Thông tin / Phiên bản; thấy «Tải thêm tệp», «Xóa tệp» dù đã có tệp', async () => {
    await ready()
    expect(screen.queryByRole('tab', { name: /Phê duyệt/ })).not.toBeInTheDocument()
    expect(await screen.findByRole('button', { name: /Tải thêm tệp/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Xóa tệp/ })).toBeInTheDocument()
  })

  it('người GHI: «Lệnh khác» có «Chuyển sang soạn thảo», không có lệnh duyệt / ban hành / bãi bỏ / sao chép', async () => {
    await ready()
    fireEvent.click(screen.getByRole('button', { name: 'Lệnh khác' }))
    const names = screen.getAllByRole('button').map((b) => b.textContent?.trim() ?? '')
    expect(names).toContain('Chuyển sang soạn thảo')
    for (const blocked of [/Gửi duyệt/, /Ban hành/, /Bãi bỏ/, /Sao chép/, /Tạo bản trích/, /Duyệt/]) {
      expect(names.some((n) => blocked.test(n))).toBe(false)
    }
  })

  it('người GHI: tab «Thông tin» có form sửa + «Lưu thông tin», không có thẻ chia sẻ / phạm vi / chữ ký', async () => {
    await ready()
    fireEvent.mouseDown(screen.getByRole('tab', { name: /Thông tin/ }), { button: 0 })
    expect(await screen.findByRole('button', { name: /Lưu thông tin/ })).toBeInTheDocument()
    expect(screen.queryByText(/Quyền truy cập/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Phạm vi áp dụng/i)).not.toBeInTheDocument()
  })

  it('người chỉ ĐỌC: không «Tải thêm tệp», «Xóa tệp», «Lưu thông tin», «Chuyển sang soạn thảo»', async () => {
    state.write = false
    await ready()
    expect(screen.queryByRole('button', { name: /Tải thêm tệp|Xóa tệp/ })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Lệnh khác' }))
    expect(screen.queryByRole('button', { name: /Chuyển sang soạn thảo/ })).not.toBeInTheDocument()
    fireEvent.mouseDown(screen.getByRole('tab', { name: /Thông tin/ }), { button: 0 })
    await waitFor(() => expect(screen.queryByRole('button', { name: /Lưu thông tin/ })).not.toBeInTheDocument())
  })

  it('văn bản thường chỉ-tệp (không phải bản lưu trữ), có tệp + quyền ghi: vẫn có «Tải thêm tệp»', async () => {
    state.isArchive = false
    renderPage()
    expect(await screen.findByRole('button', { name: /Tải thêm tệp/ })).toBeInTheDocument()
  })

  it('người GHI: tiêu đề / tóm tắt / ngày bị khóa, ghi chú & nơi lưu sửa được; «Lưu thông tin» chỉ gửi trường sửa được (owner = 0 vẫn lưu được)', async () => {
    await ready()
    fireEvent.mouseDown(screen.getByRole('tab', { name: /Thông tin/ }), { button: 0 })
    const save = await screen.findByRole('button', { name: /Lưu thông tin/ })
    const title = screen.getByPlaceholderText('Nhập tên văn bản') as HTMLInputElement
    expect(title.closest('fieldset[data-sync-owned]')).not.toBeNull()
    fireEvent.click(save)
    await waitFor(() => expect(state.patch.length).toBe(1))
    const body = (state.patch[0] as { body: Record<string, unknown> }).body
    for (const owned of ['title', 'summary', 'keywords', 'effective_date', 'expire_date', 'doc_type_id',
      'book_id', 'company_id', 'department_id', 'owner_employee_id']) {
      expect(body).not.toHaveProperty(owned)
    }
    expect(body).toHaveProperty('storage_location')
  })

  it('người GHI: tab Phiên bản không có «Mở phiên bản mới»', async () => {
    await ready()
    fireEvent.mouseDown(screen.getByRole('tab', { name: /Phiên bản/ }), { button: 0 })
    await waitFor(() => expect(screen.queryByRole('button', { name: /Mở phiên bản mới|Phiên bản mới/ })).not.toBeInTheDocument())
  })
})
