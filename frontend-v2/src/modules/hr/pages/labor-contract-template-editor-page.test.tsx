// duoc-CR-606 — trang soạn mẫu hợp đồng trên web. Trình soạn tiptap thay bằng bản giả gọn (jsdom
// không dựng nổi cả bộ khung trang/thước); hàm đổi mm ↔ px vẫn là hàm THẬT. API chặn ở `@/core/api`.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'
import type * as RteModule from '@/shared/ui/rich-text-editor'

import { LaborContractTemplateEditorPage } from './labor-contract-template-editor-page'

const insertContent = vi.fn()
const fakeEditor = {
  chain: () => ({ focus: () => ({ insertContent: (c: unknown) => ({ run: () => insertContent(c) }) }) }),
}
const editorProps = vi.hoisted(() => ({ current: null as null | Record<string, unknown> }))

vi.mock('@/shared/ui/rich-text-editor', async (importOriginal) => {
  const actual = await importOriginal<typeof RteModule>()
  const { useEffect } = await import('react')
  function FakeEditor(props: Record<string, unknown>) {
    editorProps.current = props
    const ready = props.onEditorReady as (e: unknown) => void
    useEffect(() => ready(fakeEditor), [ready])
    return (
      <textarea
        aria-label="Nội dung mẫu"
        readOnly={props.editable === false}
        defaultValue={props.defaultContent as string}
        onChange={(e) => (props.onChange as (h: string) => void)(e.target.value)}
      />
    )
  }
  return { ...actual, RichTextEditor: FakeEditor }
})

const confirmMock = vi.fn(async (_options: unknown) => true)
vi.mock('@/shared/ui/confirm-dialog', () => ({ confirm: (o: unknown) => confirmMock(o) }))

let canWrite = true
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (_e: string, action: string) => action !== 'write' || canWrite }),
}))

const putCalls: { url: string; body: unknown }[] = []
let putError: unknown = null
vi.mock('@/core/api', async (importOriginal) => ({
  ...(await importOriginal<typeof CoreApi>()),
  apiGet: async (url: string) => {
    if (url.endsWith('/placeholders')) {
      return [
        { key: 'ho_ten', label: 'Họ và tên', group: 'Người lao động', example: 'Nguyễn Văn A' },
        { key: 'luong_co_ban', label: 'Lương cơ bản', group: 'Lương', example: '15.000.000' },
      ]
    }
    if (url.endsWith('/content')) return { html: '<p>Bên B: {{ ho_ten }}</p>', margin_left_mm: 25, margin_right_mm: 15 }
    return { id: 7, name: 'Mẫu 12 tháng', company_name: 'Công ty A', company_code: 'CTA', contract_type: 2,
      original_filename: 'mau.docx' }
  },
  apiPut: async (url: string, body: unknown) => {
    putCalls.push({ url, body })
    if (putError) throw putError
    return { id: 7 }
  },
}))

/** Nút «Lưu» khóa tới khi nội dung tải xong — đợi trình soạn hiện rồi mới bấm. */
async function clickSaveWhenReady() {
  await screen.findByLabelText('Nội dung mẫu')
  fireEvent.click(screen.getByRole('button', { name: 'Lưu' }))
}

function build(path = '/hr/labor-contract-templates/7/edit') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/hr/labor-contract-templates/:id/edit" element={<LaborContractTemplateEditorPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  canWrite = true
  putCalls.length = 0
  putError = null
  insertContent.mockReset()
  //  `mockReset` chứ không `mockClear`: giá trị «Hủy» xếp hàng bằng `mockResolvedValueOnce` mà không
  //  dùng tới sẽ dồn sang bài sau và làm bài đó «bấm Hủy» ngầm.
  confirmMock.mockReset()
  confirmMock.mockImplementation(async (_options: unknown) => true)
  editorProps.current = null
})

describe('LaborContractTemplateEditorPage', () => {
  it('opens the template content with its own page margins converted to pixels', async () => {
    build()
    expect(await screen.findByRole('heading', { name: 'Soạn mẫu «Mẫu 12 tháng»' })).toBeInTheDocument()
    expect(await screen.findByLabelText('Nội dung mẫu')).toHaveValue('<p>Bên B: {{ ho_ten }}</p>')
    const { mmToPx } = await import('@/shared/ui/rich-text-editor')
    expect(editorProps.current?.defaultMargins).toEqual({ left: mmToPx(25), right: mmToPx(15) })
  })

  //  Biến chèn dạng CHỮ THUẦN: chèn qua HTML có thể bị cắt mảnh → sinh hợp đồng còn nguyên `{{ … }}`.
  it('inserts the clicked variable as plain text at the cursor', async () => {
    build()
    fireEvent.click(await screen.findByRole('button', { name: 'Chèn biến Họ và tên' }))
    expect(insertContent).toHaveBeenCalledWith({ type: 'text', text: '{{ ho_ten }}' })
  })

  it('warns about Word formatting once, then saves the edited html with the original margins', async () => {
    build()
    fireEvent.change(await screen.findByLabelText('Nội dung mẫu'), { target: { value: '<p>Mới {{ ho_ten }}</p>' } })
    fireEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(putCalls).toHaveLength(1))
    expect(putCalls[0]).toEqual({
      url: '/api/labor-contract-templates/7/content',
      body: { html: '<p>Mới {{ ho_ten }}</p>', margin_left_mm: 25, margin_right_mm: 15 },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(putCalls).toHaveLength(2))
    expect(confirmMock).toHaveBeenCalledTimes(1)
  })

  it('does not save when the user cancels the formatting warning', async () => {
    confirmMock.mockResolvedValueOnce(false)
    build()
    await clickSaveWhenReady()
    await waitFor(() => expect(confirmMock).toHaveBeenCalled())
    expect(putCalls).toHaveLength(0)
  })

  it('saves margins dragged on the ruler, rounded to whole millimetres', async () => {
    build()
    await screen.findByLabelText('Nội dung mẫu')
    const { pxToMm } = await import('@/shared/ui/rich-text-editor')
    ;(editorProps.current?.onMarginsChange as (m: { left: number; right: number }) => void)({ left: 121, right: 37 })
    fireEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(putCalls).toHaveLength(1))
    expect(putCalls[0].body).toMatchObject({
      margin_left_mm: Math.round(pxToMm(121)),
      margin_right_mm: Math.round(pxToMm(37)),
    })
    expect(Number.isInteger((putCalls[0].body as { margin_left_mm: number }).margin_left_mm)).toBe(true)
  })

  it('lists unknown variables from a 422 right on the page', async () => {
    putError = { response: { data: { error: { message: 'Mẫu có biến lạ', details: { unknown: ['ten_la'] } } } } }
    build()
    await clickSaveWhenReady()
    expect(await screen.findByRole('alert')).toHaveTextContent('{{ ten_la }}')
  })

  it('read-only users can view but get no save button and no variable panel', async () => {
    canWrite = false
    build()
    expect(await screen.findByLabelText('Nội dung mẫu')).toHaveAttribute('readonly')
    expect(screen.queryByRole('button', { name: 'Lưu' })).toBeNull()
    expect(screen.queryByText('Chèn biến')).toBeNull()
  })

  it.each(['abc', '0', '-3', '1.5'])('says the link is wrong for id %s instead of calling the API', (id) => {
    build(`/hr/labor-contract-templates/${id}/edit`)
    expect(screen.getByText('Đường dẫn không đúng mẫu nào.')).toBeInTheDocument()
  })
})
