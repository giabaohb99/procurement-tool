import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { useEffect } from 'react'
import type { UseFormReturn } from 'react-hook-form'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { DocumentRecordFormValues } from '../schemas/document-record-schema'
import { DocumentCreatePage } from './document-create-page'
import { DOCUMENT_CONTENT_MODE } from '../types/document-record'

/**
 * LỖI ĐÃ XẢY RA (rà soát mã 23/09/2026, mục H5): chốt chặn bấm đúp đặt trong
 * `onClick` của nút — nhưng nút cuối là `type="submit"`, `onClick` không gọi
 * `preventDefault()` nên form VẪN nộp ở lần bấm thứ hai, ra HAI lệnh tạo văn
 * bản. Test này bấm hai lần LIỀN TAY (không `await` giữa hai lần — đúng nhịp
 * "trước khi `disabled={save.isPending}` kịp render") và đòi `save.mutate`
 * chỉ chạy đúng MỘT lần.
 *
 * Mọi hook/khối con không liên quan tới luồng nộp form đều mock TRỌN VẸN —
 * test này chỉ quan tâm hành vi của chính `DocumentCreatePage` (điều hướng ba
 * bước + chốt chặn bấm đúp), không phải các ô nhập thật của từng khối con.
 */

const { mutateAsyncMock, mutateMock } = vi.hoisted(() => ({
  mutateAsyncMock: vi.fn(async () => ({
    id: 1,
    current_version_id: 10,
    attachment_view_window_enabled: true,
  })),
  mutateMock: vi.fn(),
}))

vi.mock('@/core/auth/use-auth', () => ({
  useAuth: () => ({ user: { id: 1, company_id: 1, department_id: 1, employee_id: 1 } }),
}))

vi.mock('../hooks/use-documents', () => ({
  useDiscardDraft: () => ({ mutateAsync: vi.fn() }),
  useDocumentPrerequisites: () => ({ data: undefined }),
  useSaveDocument: () => ({ mutate: mutateMock, mutateAsync: mutateAsyncMock, isPending: false }),
}))

vi.mock('../hooks/use-document-books', () => ({
  useDocumentBooks: () => ({ items: [] }),
}))

vi.mock('../hooks/use-document-types', () => ({
  useActiveDocumentTypes: () => [],
}))

vi.mock('../hooks/use-document-templates', () => ({
  useDocumentTemplate: () => ({ data: undefined, isFetching: false }),
}))

vi.mock('../hooks/use-document-approval-preview', () => ({
  useDocumentApprovalPreview: () => ({ data: undefined, isLoading: false }),
}))

//  Điền sẵn bộ trường bắt buộc của bước 1 lúc mount — test này không kiểm tra
//  UI thật của các ô chọn (đã có `folder-picker.test.tsx`, v.v. riêng), chỉ
//  cần vượt qua `form.trigger`/schema để tới được bước cuối.
vi.mock('../components/document-main-info-fields', () => ({
  MAIN_INFO_FIELDS: ['doc_type_id', 'company_id', 'department_id', 'title', 'owner_employee_id'],
  DocumentMainInfoFields: ({ form }: { form: UseFormReturn<DocumentRecordFormValues> }) => {
    useEffect(() => {
      form.setValue('doc_type_id', 1)
      form.setValue('company_id', 1)
      form.setValue('department_id', 1)
      form.setValue('owner_employee_id', 1)
      form.setValue('title', 'Văn bản kiểm thử bấm đúp')
      // eslint-disable-next-line react-hooks/exhaustive-deps -- chỉ điền một lần lúc mount
    }, [])
    return null
  },
}))

vi.mock('../components/document-access-fields', () => ({ DocumentAccessFields: () => null }))
vi.mock('../components/document-approver-preview-line', () => ({
  DocumentApproverPreviewLine: () => null,
}))
vi.mock('../components/document-clone-plan-fields', () => ({ DocumentClonePlanFields: () => null }))
vi.mock('../components/document-extra-info-fields', () => ({ DocumentExtraInfoFields: () => null }))
vi.mock('../components/document-leave-fields', () => ({ DocumentLeaveFields: () => null }))
vi.mock('../components/document-pending-attachments', () => ({
  DocumentPendingAttachments: () => null,
}))
vi.mock('../components/document-scope-fields', () => ({ DocumentScopeFields: () => null }))

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <DocumentCreatePage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

//  «Tạo, không soạn thảo» hỏi lại khi chưa đính tệp — cho qua luôn trong test.
vi.mock('@/shared/ui/confirm-dialog', () => ({ confirm: vi.fn(async () => true) }))

async function goToLastStep() {
  fireEvent.click(await screen.findByRole('button', { name: 'Tiếp tục' }))
  await waitFor(() => expect(mutateAsyncMock).toHaveBeenCalledTimes(1))
  fireEvent.click(screen.getByRole('button', { name: 'Tiếp tục' }))
  await waitFor(() =>
    expect(screen.getByRole('button', { name: 'Tạo và soạn thảo' })).toBeInTheDocument(),
  )
}

//  24/09/2026: màn chi tiết bỏ tab «Tệp», tab «Văn bản» đọc `content_mode` để
//  chọn trình soạn thảo / trình xem tệp. Nút cuối là lượt SỬA bản nháp đã sinh
//  ở bước 1 — thiếu trường này ở đó là văn bản chỉ gồm tệp mở ra trang trắng.
describe('DocumentCreatePage — lưu CÁCH TẠO (content_mode)', () => {
  beforeEach(() => {
    mutateMock.mockClear()
    mutateAsyncMock.mockClear()
  })

  it('«Tạo và soạn thảo» sends content_mode = compose', async () => {
    renderPage()
    await goToLastStep()
    fireEvent.click(screen.getByRole('button', { name: 'Tạo và soạn thảo' }))
    await waitFor(() => expect(mutateMock).toHaveBeenCalledTimes(1))
    expect(mutateMock.mock.calls[0][0].values.content_mode).toBe(DOCUMENT_CONTENT_MODE.compose)
  })

  it('«Tạo, không soạn thảo» sends content_mode = files and empty content', async () => {
    renderPage()
    await goToLastStep()
    fireEvent.click(screen.getByRole('button', { name: 'Tạo, không soạn thảo' }))
    await waitFor(() => expect(mutateMock).toHaveBeenCalledTimes(1))
    const payload = mutateMock.mock.calls[0][0].values
    expect(payload.content_mode).toBe(DOCUMENT_CONTENT_MODE.files)
    expect(payload.content_html).toBe('')
  })
})

describe('DocumentCreatePage — chặn bấm đúp nút Tạo', () => {
  it('bấm đúp «Tạo và soạn thảo» liền tay chỉ gọi MỘT lệnh tạo văn bản', async () => {
    renderPage()

    //  Bước 1 → 2: sinh bản nháp trên máy chủ (mock `mutateAsync`).
    fireEvent.click(await screen.findByRole('button', { name: 'Tiếp tục' }))
    await waitFor(() => expect(mutateAsyncMock).toHaveBeenCalledTimes(1))

    //  Bước 2 → 3: không có ô bắt buộc, chỉ cần đợi nút bước cuối xuất hiện.
    fireEvent.click(screen.getByRole('button', { name: 'Tiếp tục' }))
    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Tạo và soạn thảo' })).toBeInTheDocument(),
    )

    const submitButton = screen.getByRole('button', { name: 'Tạo và soạn thảo' })
    //  KHÔNG `await` giữa hai lần bấm — mô phỏng đúng nhịp bấm đúp thật, cả
    //  hai sự kiện click/submit bắn trước khi `disabled={save.isPending}`
    //  (state React) kịp render lại.
    fireEvent.click(submitButton)
    fireEvent.click(submitButton)

    await waitFor(() => expect(mutateMock).toHaveBeenCalledTimes(1))
  })
})
