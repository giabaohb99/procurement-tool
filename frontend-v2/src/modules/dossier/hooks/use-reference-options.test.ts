import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { createElement, type ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useReferenceLabel, useReferenceOptions } from './use-reference-options'

const apiGet = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
}))

let queryClient: QueryClient

function wrapper({ children }: { children: ReactNode }) {
  return createElement(QueryClientProvider, { client: queryClient }, children)
}

beforeEach(() => {
  queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  apiGet.mockReset()
  apiGet.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 200 })
})

/** Tham số của lượt gọi API thứ `n` (0-based). */
const callParams = (n = 0) => apiGet.mock.calls[n][1].params as Record<string, unknown>

describe('useReferenceOptions — danh mục lớn (tra phía server)', () => {
  it('gửi từ khóa lên server bằng đúng tên tham số của danh mục đó', async () => {
    const { result } = renderHook(() => useReferenceOptions('employee', 'Nguyễn Văn'), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(apiGet).toHaveBeenCalledWith('/api/employees', expect.anything())
    //  `full_name`, KHÔNG phải `name` — `apply_filters` bỏ qua tham số lạ trong
    //  im lặng nên gõ sai tên thì ô tìm trả nguyên danh sách, không lỗi nào.
    expect(callParams()).toEqual({ page_size: 200, full_name: 'Nguyễn Văn' })
  })

  it('từ khóa RỖNG thì không gửi tham số lọc, chỉ lấy trang đầu', async () => {
    const { result } = renderHook(() => useReferenceOptions('product', ''), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(callParams()).toEqual({ page_size: 200 })
  })

  it('đổi từ khóa là gọi lại — trang đầu không đủ để lọc tại chỗ', async () => {
    const { rerender, result } = renderHook(({ q }) => useReferenceOptions('product', q), {
      wrapper,
      initialProps: { q: '' },
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    rerender({ q: 'ống' })
    await waitFor(() => expect(apiGet).toHaveBeenCalledTimes(2))
    expect(callParams(1)).toEqual({ page_size: 200, name: 'ống' })
  })
})

describe('useReferenceOptions — danh mục nhỏ (nạp hết rồi lọc tại chỗ)', () => {
  it('KHÔNG gọi lại khi người dùng gõ', async () => {
    //  ⚠️ `/api/departments` bỏ qua `?name=` (đã thử tay: trả đủ 18 dòng), nên
    //  gọi lại theo từng phím là tốn request mà kết quả y hệt. Khóa danh sách
    //  phải BỎ từ khóa ra ngoài, không thì mỗi phím một khóa mới và TanStack
    //  Query coi đó là một truy vấn khác.
    const { rerender, result } = renderHook(({ q }) => useReferenceOptions('department', q), {
      wrapper,
      initialProps: { q: '' },
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    rerender({ q: 'Kho' })
    rerender({ q: 'Kho vận' })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(apiGet).toHaveBeenCalledTimes(1)
    expect(callParams()).toEqual({ page_size: 200 })
  })
})

describe('useReferenceOptions — dựng nhãn', () => {
  it('đổi dòng thành {value, label} theo cột nhãn của danh mục', async () => {
    apiGet.mockResolvedValue({
      items: [
        { id: 42, full_name: 'Nguyễn Văn A', name: 'KHÔNG DÙNG CỘT NÀY' },
        { id: 7, full_name: 'Trần Thị B' },
      ],
    })
    const { result } = renderHook(() => useReferenceOptions('employee', ''), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    //  `value` là CHUỖI: `SearchSelect` so sánh bằng `===` trên chuỗi, còn hồ sơ
    //  lưu số. Trả về số là ô chọn không khớp mục nào và hiện trống trơn.
    expect(result.current.data).toEqual([
      { value: '42', label: 'Nguyễn Văn A' },
      { value: '7', label: 'Trần Thị B' },
    ])
  })

  it('dòng thiếu cột nhãn thì lấy id làm nhãn, không ra "undefined"', async () => {
    //  Nhãn rỗng thì dòng đó trong danh sách là một khoảng trắng bấm được —
    //  người dùng không biết mình đang chọn gì.
    apiGet.mockResolvedValue({ items: [{ id: 9 }, { id: 10, name: null }] })
    const { result } = renderHook(() => useReferenceOptions('supplier', ''), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual([
      { value: '9', label: '9' },
      { value: '10', label: '10' },
    ])
  })
})

describe('useReferenceOptions — khóa danh mục lạ', () => {
  it('không gọi API với khóa không có trong bảng', async () => {
    const { result } = renderHook(() => useReferenceOptions('users', 'x'), { wrapper })
    await waitFor(() => expect(result.current.fetchStatus).toBe('idle'))
    expect(apiGet).not.toHaveBeenCalled()
  })

  it('không gọi API với khóa rỗng (chưa chọn danh mục)', async () => {
    const { result } = renderHook(() => useReferenceOptions('', ''), { wrapper })
    await waitFor(() => expect(result.current.fetchStatus).toBe('idle'))
    expect(apiGet).not.toHaveBeenCalled()
  })

  it('không gọi API với khóa thừa kế của Object', async () => {
    //  Xem `dossier-reference-sources.test.ts`: `__proto__` từng lọt qua và kéo
    //  theo `apiGet(undefined)`.
    const { result } = renderHook(() => useReferenceOptions('__proto__', ''), { wrapper })
    await waitFor(() => expect(result.current.fetchStatus).toBe('idle'))
    expect(apiGet).not.toHaveBeenCalled()
  })
})

describe('useReferenceLabel — tra nhãn của mục ĐANG CHỌN', () => {
  it('hỏi đích danh theo id', async () => {
    apiGet.mockResolvedValue({ id: 3646, name: 'Ống thép mạ kẽm D60' })
    const { result } = renderHook(() => useReferenceLabel('product', 3646), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    //  ⚠️ Đây là cái giá của việc lưu ID: mục thứ 3646 không nằm trong trang đầu
    //  200 dòng, nên không hỏi riêng thì mở hồ sơ ra ô chọn hiện TRỐNG TRƠN.
    expect(apiGet).toHaveBeenCalledWith('/api/products/3646')
    expect(result.current.data).toBe('Ống thép mạ kẽm D60')
  })

  it('id 0 và id âm thì không hỏi gì', async () => {
    for (const id of [0, -1]) {
      apiGet.mockClear()
      const { result } = renderHook(() => useReferenceLabel('product', id), { wrapper })
      await waitFor(() => expect(result.current.fetchStatus).toBe('idle'))
      expect(apiGet, String(id)).not.toHaveBeenCalled()
    }
  })

  it('id trỏ vào dòng đã xóa thì hỏng gọn, KHÔNG thử lại', async () => {
    //  Thử lại ba lần chỉ làm người dùng chờ lâu hơn để nhận cùng một 404.
    apiGet.mockRejectedValue(new Error('404'))
    const { result } = renderHook(() => useReferenceLabel('product', 999999), { wrapper })
    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(apiGet).toHaveBeenCalledTimes(1)
  })
})
