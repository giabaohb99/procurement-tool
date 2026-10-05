// Hộp «Nạp danh mục» thuốc BVTV: luôn giải thích trước hai chế độ nạp lại (thay cả danh mục /
// chỉ cập nhật), và sau khi nạp xong phải HIỆN NGUYÊN câu `message` của backend một khi backend
// đã biết phân biệt `mode` — không tự ghép lại câu cũ (review M… — tự ghép câu bỏ qua thông tin
// backend vừa thêm). Backend CŨ chưa trả `mode` thì vẫn phải ghép câu như trước, không được vỡ.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'

import { CustomsPesticideImportDialog } from './customs-pesticide-import-dialog'

const toastSuccess = vi.fn()
vi.mock('sonner', () => ({ toast: { success: (m: string) => toastSuccess(m), error: vi.fn() } }))

//  Hộp thoại chỉ gọi `httpClient.post` (xem `importCustomsPesticides`) — thay nguyên `httpClient`
//  bằng một bản tối giản, khỏi phụ thuộc cách axios gắn method lên instance thật.
//  `@/core/api` bị nạp SỚM qua chuỗi `core/auth/auth-store.ts` (trước khi `vi.mock` hoisted chạy
//  xong phần còn lại của tệp) nên biến tham chiếu trong factory PHẢI qua `vi.hoisted`, không thì
//  ăn `ReferenceError: Cannot access 'httpPost' before initialization`.
const { httpPost } = vi.hoisted(() => ({ httpPost: vi.fn() }))
vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return { ...actual, httpClient: { post: httpPost } }
})

function build(onClose = vi.fn()) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  const result = render(
    <QueryClientProvider client={queryClient}>
      <CustomsPesticideImportDialog
        currentTotal={5}
        manualCount={1}
        lastLoadedAt={null}
        onClose={onClose}
      />
    </QueryClientProvider>,
  )
  return { ...result, onClose }
}

async function pickFileAndSubmit() {
  const user = userEvent.setup()
  //  `Dialog` (Radix) portal nội dung ra NGOÀI `container` của `render()`, thẳng vào
  //  `document.body` — phải tìm input ở đó, không phải trong `container`.
  const input = document.body.querySelector('input[type="file"]') as HTMLInputElement
  await user.upload(input, new File(['x'], 'thuoc-bvtv.xlsx'))
  await user.click(screen.getByRole('button', { name: 'Nạp danh mục' }))
}

beforeEach(() => {
  httpPost.mockReset()
  toastSuccess.mockReset()
})

describe('CustomsPesticideImportDialog', () => {
  it('explains both reload modes before any file is picked', () => {
    build()
    //  Chữ đậm nằm NGUYÊN trong một thẻ <b> (không bị cắt bởi text thường xung quanh) nên khớp
    //  được bằng `getByText` thường — xem JSX của hộp thoại.
    expect(screen.getByText('thay cả danh mục')).toBeInTheDocument()
    expect(screen.getByText('cập nhật')).toBeInTheDocument()
  })

  it('shows the backend message verbatim once it tells mode apart (merge: page export file)', async () => {
    httpPost.mockResolvedValue({
      data: {
        success: true,
        message: 'Đã cập nhật 3 thuốc theo tệp, giữ nguyên phần còn lại',
        data: {
          pesticides: 3,
          uses: 1,
          kept_manual: 0,
          dropped: 0,
          retag: { total: 0, tagged: 0, technical: 0 },
          mode: 'merge',
        },
      },
    })
    build()

    await pickFileAndSubmit()

    await waitFor(() =>
      expect(toastSuccess).toHaveBeenCalledWith('Đã cập nhật 3 thuốc theo tệp, giữ nguyên phần còn lại'),
    )
  })

  it('shows the backend message verbatim for mode: replace too, not just merge', async () => {
    httpPost.mockResolvedValue({
      data: {
        success: true,
        message: 'Đã thay toàn bộ danh mục bằng 500 thuốc',
        data: {
          pesticides: 500,
          uses: 120,
          kept_manual: 2,
          dropped: 3,
          retag: { total: 0, tagged: 0, technical: 0 },
          mode: 'replace',
        },
      },
    })
    build()

    await pickFileAndSubmit()

    await waitFor(() =>
      expect(toastSuccess).toHaveBeenCalledWith('Đã thay toàn bộ danh mục bằng 500 thuốc'),
    )
  })

  it('still composes its own message when the backend has not learned to tell mode apart yet', async () => {
    httpPost.mockResolvedValue({
      data: {
        success: true,
        message: 'Đã nạp 5 thuốc BVTV',
        //  Backend CŨ: không có `mode` — hộp phải tự ghép câu như trước, không vỡ.
        data: {
          pesticides: 5,
          uses: 2,
          kept_manual: 1,
          dropped: 0,
          retag: { total: 0, tagged: 0, technical: 0 },
        },
      },
    })
    build()

    await pickFileAndSubmit()

    await waitFor(() =>
      expect(toastSuccess).toHaveBeenCalledWith(
        'Đã nạp 5 thuốc, 2 dòng phạm vi sử dụng, giữ 1 thuốc tự thêm',
      ),
    )
  })

  it('ignores a server message with mode when message itself is missing, falling back safely', async () => {
    //  Hacker/lỗi backend: `mode` có nhưng `message` rỗng — đừng toast chuỗi rỗng, phải rơi
    //  xuống câu tự ghép để người dùng còn biết việc nạp có thành công.
    httpPost.mockResolvedValue({
      data: {
        success: true,
        message: '',
        data: {
          pesticides: 7,
          uses: 0,
          kept_manual: 0,
          dropped: 0,
          retag: { total: 0, tagged: 0, technical: 0 },
          mode: 'replace',
        },
      },
    })
    build()

    await pickFileAndSubmit()

    await waitFor(() =>
      expect(toastSuccess).toHaveBeenCalledWith('Đã nạp 7 thuốc, 0 dòng phạm vi sử dụng'),
    )
  })
})
