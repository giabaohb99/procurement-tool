import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { BotMemory } from '@/modules/system/api/bot-memory-api'
import { ProfileMemoryTab } from './profile-memory-tab'

/**
 * Tab «Bot nhớ gì về tôi» (ai-CR-138, phase 13.4).
 *
 * Chỗ dễ lủng: sửa / xóa phải gửi NGUYÊN VĂN dòng cũ (kể cả đuôi «(tự rút)» + hạn) làm khóa — gửi bản đã bóc đuôi thì
 * backend không tìm thấy dòng và trả 409; gửi số thứ tự thì hai tab sửa cùng lúc là sửa nhầm dòng. Lưu hỏng thì ô nhập
 * phải giữ nguyên chữ người dùng đã gõ. Bấm đúp không được ra hai lượt gọi.
 */

const apiGet = vi.fn()
const apiPost = vi.fn()
const apiDelete = vi.fn()
const apiPatch = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: (...args: unknown[]) => apiPost(...args),
  apiPut: vi.fn(),
  apiPatch: (...args: unknown[]) => apiPatch(...args),
  apiDelete: (...args: unknown[]) => apiDelete(...args),
}))

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

const confirmMock = vi.fn(() => Promise.resolve(true))
vi.mock('@/shared/ui/confirm-dialog', () => ({ confirm: () => confirmMock() }))

const AUTO = 'Muốn trả lời ngắn gọn (tự rút) (đến 06/02/2027)'

function memory(over: Partial<BotMemory> = {}): BotMemory {
  return {
    sections: [
      { key: 'ban_than', label: 'Bản thân', lines: [{ text: 'Ở Cần Thơ', fact: 'Ở Cần Thơ', auto: false, until: null }] },
      { key: 'so_thich', label: 'Sở thích', lines: [] },
      {
        key: 'cach_lam_viec',
        label: 'Cách làm việc',
        lines: [{ text: AUTO, fact: 'Muốn trả lời ngắn gọn', auto: true, until: '2027-02-06' }],
      },
      { key: 'da_chot', label: 'Đã chốt', lines: [] },
    ],
    chars: 120,
    max: 8000,
    watching: [
      {
        id: 9,
        fact: 'Thích bảng hơn đoạn văn',
        section: 'so_thich',
        hits: 1,
        days: 1,
        need_hits: 3,
        need_days: 2,
        confidence: 0.17,
        last_seen_at: null,
      },
    ],
    notes: [],
    habits: [{ type: 'phap_nhan', label: 'pháp nhân', value: 'DEGO', count: 8, total: 10 }],
    suggestions: [],
    auto_enabled: true,
    ...over,
  }
}

/** Tab gọi hai cửa: trí nhớ và bản tin (ai-CR-140). */
const BRIEFS = {
  items: [
    { id: 0, kind: 1, enabled: false, hour: 7, minute: 30, days: 127, topic: '', sub_code: '', implicit: true,
      label: 'Bản tin sáng', when: '07:30 · mọi ngày' },
  ],
}

function mockGet(mem: BotMemory) {
  apiGet.mockImplementation((url: string) => Promise.resolve(url.endsWith('/me/briefs') ? BRIEFS : mem))
}

function renderTab() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <ProfileMemoryTab />
    </QueryClientProvider>,
  )
}

describe('ProfileMemoryTab', () => {
  beforeEach(() => {
    apiGet.mockReset()
    apiPost.mockReset()
    apiPatch.mockReset()
    apiDelete.mockReset()
    confirmMock.mockClear()
  })

  it('reads only the self-service endpoint and marks auto-extracted lines', async () => {
    mockGet(memory())
    renderTab()
    expect(await screen.findByText('Muốn trả lời ngắn gọn')).toBeInTheDocument()
    expect(apiGet).toHaveBeenCalledWith('/api/agent-hub/me/memory')
    expect(screen.getByText('tự rút')).toBeInTheDocument()
    expect(screen.getByText('1/3 lần · 1/2 ngày')).toBeInTheDocument()
    expect(screen.getByText('DEGO')).toBeInTheDocument()
    //  Đuôi kỹ thuật không lộ ra chữ hiển thị.
    expect(screen.queryByText(AUTO)).not.toBeInTheDocument()
  })

  it('edits by sending the exact old line text as the key', async () => {
    mockGet(memory())
    apiPatch.mockResolvedValue(memory())
    renderTab()
    await userEvent.click(await screen.findByRole('button', { name: 'Sửa: Muốn trả lời ngắn gọn' }))
    const box = screen.getByRole('textbox', { name: 'Sửa dòng nhớ' })
    await userEvent.clear(box)
    await userEvent.type(box, 'Trả lời ngắn, có số{Enter}')
    await waitFor(() =>
      expect(apiPatch).toHaveBeenCalledWith('/api/agent-hub/me/memory/lines', {
        section: 'cach_lam_viec',
        old: AUTO,
        text: 'Trả lời ngắn, có số',
      }),
    )
  })

  it('keeps the typed text when saving a new line fails', async () => {
    mockGet(memory())
    apiPost.mockRejectedValue(new Error('em không ghi mật khẩu'))
    renderTab()
    const box = await screen.findByRole('textbox', { name: 'Thêm dòng vào Sở thích' })
    await userEvent.type(box, 'Mật khẩu wifi là abc{Enter}')
    await waitFor(() => expect(apiPost).toHaveBeenCalledTimes(1))
    expect(box).toHaveValue('Mật khẩu wifi là abc')
  })

  it('does not fire twice on a double click', async () => {
    mockGet(memory())
    let release: (v: BotMemory) => void = () => {}
    apiDelete.mockImplementation(() => new Promise<BotMemory>((r) => (release = r)))
    renderTab()
    const drop = await screen.findByRole('button', { name: 'Bỏ để ý: Thích bảng hơn đoạn văn' })
    await userEvent.dblClick(drop)
    release(memory({ watching: [] }))
    await waitFor(() => expect(apiDelete).toHaveBeenCalledTimes(1))
    expect(apiDelete).toHaveBeenCalledWith('/api/agent-hub/me/memory/watching/9')
  })

  it('deletes a line and wipes everything only after confirmation', async () => {
    mockGet(memory())
    apiPost.mockResolvedValue(memory())
    apiDelete.mockResolvedValue(memory({ sections: memory().sections.map((s) => ({ ...s, lines: [] })) }))
    renderTab()
    await userEvent.click(await screen.findByRole('button', { name: 'Xóa: Ở Cần Thơ' }))
    await waitFor(() =>
      expect(apiPost).toHaveBeenCalledWith('/api/agent-hub/me/memory/lines/delete', { section: 'ban_than', old: 'Ở Cần Thơ' }),
    )
    confirmMock.mockResolvedValueOnce(false)
    await userEvent.click(screen.getByRole('button', { name: /Xóa toàn bộ trí nhớ/ }))
    expect(apiDelete).not.toHaveBeenCalled()
    await userEvent.click(screen.getByRole('button', { name: /Xóa toàn bộ trí nhớ/ }))
    await waitFor(() => expect(apiDelete).toHaveBeenCalledWith('/api/agent-hub/me/memory'))
  })

  it('says plainly when the bot remembers nothing', async () => {
    mockGet(
      memory({ sections: memory().sections.map((s) => ({ ...s, lines: [] })), watching: [], habits: [] }),
    )
    renderTab()
    expect(await screen.findByText('Bot chưa nhớ gì về bạn.')).toBeInTheDocument()
    expect(screen.getByText('Chưa có điều nào đang chờ đủ lần nhắc.')).toBeInTheDocument()
  })
})
