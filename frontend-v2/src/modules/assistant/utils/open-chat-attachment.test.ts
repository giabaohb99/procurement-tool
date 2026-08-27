import { afterEach, describe, expect, it, vi } from 'vitest'

import { fetchBlobUrl } from '@/core/api'
import { openChatAttachment } from './open-chat-attachment'

vi.mock('@/core/api', () => ({ fetchBlobUrl: vi.fn() }))
vi.mock('sonner', () => ({ toast: { error: vi.fn() } }))

const fetchMock = vi.mocked(fetchBlobUrl)

afterEach(() => {
  vi.restoreAllMocks()
  fetchMock.mockReset()
})

describe('openChatAttachment', () => {
  it('mở tab TRƯỚC khi fetch rồi mới trỏ sang blob — sau await là dính chặn popup', async () => {
    const win = { location: { href: '' }, close: vi.fn() }
    const openSpy = vi
      .spyOn(window, 'open')
      .mockReturnValue(win as unknown as Window)
    fetchMock.mockResolvedValue('blob:abc')

    await openChatAttachment(7)

    //  Thứ tự là điểm mấu chốt: window.open phải chạy trong ngữ cảnh cú bấm,
    //  tức TRƯỚC lượt gọi mạng.
    expect(openSpy.mock.invocationCallOrder[0]).toBeLessThan(
      fetchMock.mock.invocationCallOrder[0],
    )
    expect(fetchMock).toHaveBeenCalledWith('/api/assistant/uploads/7')
    expect(win.location.href).toBe('blob:abc')
  })

  it('tải hỏng thì ĐÓNG tab trắng đã mở, không bỏ lại tab rỗng', async () => {
    const win = { location: { href: '' }, close: vi.fn() }
    vi.spyOn(window, 'open').mockReturnValue(win as unknown as Window)
    fetchMock.mockRejectedValue(new Error('404'))

    await openChatAttachment(7)

    expect(win.close).toHaveBeenCalled()
    expect(win.location.href).toBe('')
  })
})
