import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { DossierReferenceValue } from './dossier-reference-value'

const apiGet = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
}))

let queryClient: QueryClient

/** Dựng kèm `<label htmlFor>` đúng như hàng khai trường riêng ngoài đời. */
function renderValue(props: Partial<Parameters<typeof DossierReferenceValue>[0]> = {}) {
  const onChange = props.onChange ?? vi.fn()
  render(
    <QueryClientProvider client={queryClient}>
      <label htmlFor="cf-val-0">Giá trị</label>
      <DossierReferenceValue
        id="cf-val-0"
        source="employee"
        value=""
        {...props}
        onChange={onChange}
      />
    </QueryClientProvider>,
  )
  return { onChange }
}

/** Lượt gọi DANH SÁCH (bỏ qua lượt tra nhãn theo id). */
const listCalls = () =>
  apiGet.mock.calls.filter((call) => typeof call[1] === 'object' && call[1] !== null)

beforeEach(() => {
  queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  apiGet.mockReset()
  apiGet.mockResolvedValue({ items: [{ id: 42, full_name: 'Nguyễn Văn A' }] })
})

describe('DossierReferenceValue — chưa chọn danh mục', () => {
  it('nói ra việc phải làm trước thay vì bày một ô chọn rỗng', async () => {
    renderValue({ source: '' })
    expect(screen.getByText('Chọn danh mục ở dòng dưới trước')).toBeInTheDocument()
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
    expect(apiGet).not.toHaveBeenCalled()
  })

  it('khóa danh mục lạ cũng rơi vào nhánh đó, KHÔNG làm trắng biểu mẫu', async () => {
    //  ⚠️ LỖI ĐÃ TRÁNH: `__proto__` từng tra ra `Object.prototype` — truthy mà
    //  `label` là `undefined`, nên `config.label.toLowerCase()` ném `TypeError`
    //  ngay lúc vẽ và cả biểu mẫu trắng xóa. Dữ liệu cũ hay hỏng theo kiểu này.
    for (const source of ['users', '__proto__', 'constructor']) {
      queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
      const { unmount } = render(
        <QueryClientProvider client={queryClient}>
          <DossierReferenceValue id="x" source={source} value="" onChange={vi.fn()} />
        </QueryClientProvider>,
      )
      expect(screen.getByText('Chọn danh mục ở dòng dưới trước'), source).toBeInTheDocument()
      unmount()
    }
    expect(apiGet).not.toHaveBeenCalled()
  })
})

describe('DossierReferenceValue — nhãn của mục đang chọn', () => {
  it('hiện nhãn mục đã chọn dù nó KHÔNG có trong trang đầu', async () => {
    //  ⚠️ Đây là bài quan trọng nhất của cả tệp. Sản phẩm thứ 3646 không nằm
    //  trong 200 dòng đầu, nên `SearchSelect` không khớp mục nào. Không bù nhãn
    //  vào thì ô hiện trống trơn — nhìn y hệt ô chưa ai nhập — người dùng chọn
    //  đè một mục khác và giá trị thật mất, không báo gì.
    apiGet.mockImplementation((url: string) =>
      url === '/api/products/3646'
        ? Promise.resolve({ id: 3646, name: 'Ống thép mạ kẽm D60' })
        : Promise.resolve({ items: [{ id: 1, name: 'Xi măng' }] }),
    )
    renderValue({ source: 'product', value: '3646' })

    const combobox = await screen.findByRole('combobox', { name: 'Giá trị' })
    await waitFor(() => expect(combobox).toHaveValue('Ống thép mạ kẽm D60'))
  })

  it('mục đã có trong danh sách thì không bày thành HAI dòng', async () => {
    apiGet.mockImplementation((url: string) =>
      url === '/api/employees/42'
        ? Promise.resolve({ id: 42, full_name: 'Nguyễn Văn A' })
        : Promise.resolve({ items: [{ id: 42, full_name: 'Nguyễn Văn A' }] }),
    )
    renderValue({ value: '42' })

    const combobox = await screen.findByRole('combobox', { name: 'Giá trị' })
    await waitFor(() => expect(combobox).toHaveValue('Nguyễn Văn A'))

    await userEvent.click(combobox)
    await waitFor(() =>
      expect(screen.getAllByRole('button', { name: /Nguyễn Văn A/ })).toHaveLength(1),
    )
  })

  it('id trỏ vào dòng ĐÃ XÓA thì vẫn hiện id, không hiện ô trống', async () => {
    //  Tra nhãn trả 404. Ô phải còn dấu vết của giá trị đang lưu, không thì
    //  người dùng tưởng chưa ai nhập rồi chọn đè lên — mất luôn manh mối để
    //  biết hồ sơ này từng trỏ tới đâu.
    apiGet.mockImplementation((url: string) =>
      url.includes('/999999')
        ? Promise.reject(new Error('404'))
        : Promise.resolve({ items: [{ id: 1, full_name: 'Trần Thị B' }] }),
    )
    renderValue({ value: '999999' })

    const combobox = await screen.findByRole('combobox', { name: 'Giá trị' })
    await waitFor(() => expect(combobox).toHaveValue('999999'))
  })
})

describe('DossierReferenceValue — gõ để tìm', () => {
  it('gõ cả cụm từ chỉ bắn MỘT lượt tìm, không phải mỗi ký tự một lượt', async () => {
    //  ⚠️ Hoãn 350ms. Gỡ ra thì người gõ nhanh bắn cả chục request cho một từ
    //  khóa, và với danh mục 6803 dòng thì đó là chục lượt quét bảng.
    renderValue({ source: 'product' })
    const combobox = await screen.findByRole('combobox', { name: 'Giá trị' })
    await waitFor(() => expect(listCalls()).toHaveLength(1)) // lượt nạp trang đầu

    await userEvent.type(combobox, 'ống thép')

    await waitFor(() => expect(listCalls()).toHaveLength(2), { timeout: 3000 })
    expect(listCalls()[1][1].params).toEqual({ page_size: 200, name: 'ống thép' })
  })

  it('bấm chọn một mục thì trả về ID, không trả về tên', async () => {
    //  Cả thiết kế này đứng trên đó: hồ sơ lưu ID nên đổi tên trong danh mục là
    //  mọi hồ sơ đổi theo.
    const { onChange } = renderValue()
    const combobox = await screen.findByRole('combobox', { name: 'Giá trị' })

    await userEvent.click(combobox)
    await userEvent.click(await screen.findByRole('button', { name: /Nguyễn Văn A/ }))

    expect(onChange).toHaveBeenCalledWith('42')
  })
})
