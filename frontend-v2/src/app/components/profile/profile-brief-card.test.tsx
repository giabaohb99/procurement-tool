import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { BotMemory, BriefList } from '@/modules/system/api/bot-memory-api'
import { ProfileBriefCard } from './profile-brief-card'
import { ProfileMemoryTab } from './profile-memory-tab'

/**
 * Bản tin bot tự gửi (ai-CR-140).
 *
 * Chỗ dễ lủng: bản tin sáng NGẦM (người nối Google chưa tự đặt) có `id` 0 — bật / tắt phải đi đường `/daily`, đi đường
 * theo id thì backend trả 404 và công tắc nảy về. Đề xuất chủ động chỉ thành bản tin khi người dùng BẤM, và đúng thứ của
 * đề xuất (mặt nạ thứ hai = 1 … chủ nhật = 64).
 */

const apiGet = vi.fn()
const apiPost = vi.fn()
const apiPut = vi.fn()
const apiPatch = vi.fn()
const apiDelete = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: (...args: unknown[]) => apiPost(...args),
  apiPut: (...args: unknown[]) => apiPut(...args),
  apiPatch: (...args: unknown[]) => apiPatch(...args),
  apiDelete: (...args: unknown[]) => apiDelete(...args),
}))

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))
vi.mock('@/shared/ui/confirm-dialog', () => ({ confirm: () => Promise.resolve(true) }))

const BRIEFS: BriefList = {
  items: [
    { id: 0, kind: 1, enabled: true, hour: 7, minute: 30, days: 127, topic: '', sub_code: '', implicit: true,
      label: 'Bản tin sáng', when: '07:30 · mọi ngày' },
    { id: 5, kind: 2, enabled: true, hour: 8, minute: 0, days: 1, topic: 'công nợ quá hạn của DEGO', sub_code: '',
      implicit: false, label: 'Bản tin chủ đề', when: '08:00 · thứ hai' },
  ],
}

function wrap(node: React.ReactNode) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(<QueryClientProvider client={queryClient}>{node}</QueryClientProvider>)
}

describe('ProfileBriefCard', () => {
  beforeEach(() => {
    for (const f of [apiGet, apiPost, apiPut, apiPatch, apiDelete]) f.mockReset()
    apiGet.mockResolvedValue(BRIEFS)
  })

  it('turns the implicit morning brief off through the daily endpoint, not by id', async () => {
    apiPut.mockResolvedValue(BRIEFS)
    wrap(<ProfileBriefCard />)
    await userEvent.click(await screen.findByRole('switch', { name: 'Tắt: Bản tin sáng' }))
    await waitFor(() => expect(apiPut).toHaveBeenCalledWith('/api/agent-hub/me/briefs/daily', { enabled: false }))
    expect(apiPatch).not.toHaveBeenCalled()
  })

  it('toggles and removes a topic brief by its own id', async () => {
    apiPatch.mockResolvedValue(BRIEFS)
    apiDelete.mockResolvedValue({ items: BRIEFS.items.slice(0, 1) })
    wrap(<ProfileBriefCard />)
    await userEvent.click(await screen.findByRole('switch', { name: 'Tắt: công nợ quá hạn của DEGO' }))
    await waitFor(() => expect(apiPatch).toHaveBeenCalledWith('/api/agent-hub/me/briefs/5', { enabled: false }))
    await userEvent.click(screen.getByRole('button', { name: 'Bỏ bản tin: công nợ quá hạn của DEGO' }))
    await waitFor(() => expect(apiDelete).toHaveBeenCalledWith('/api/agent-hub/me/briefs/5'))
  })

  it('turns a proactive suggestion into a topic brief only when clicked, on the suggested weekday', async () => {
    const mem: BotMemory = {
      sections: [], chars: 0, max: 8000, watching: [], notes: [], auto_enabled: true,
      habits: [],
      suggestions: [{ sub: 'tra_cuu.cong_no', label: 'Công nợ, thanh toán', weekday: 0, weeks: 3,
                      text: 'Thứ hai nào cũng hỏi «Công nợ, thanh toán» (3 tuần)' }],
    }
    apiGet.mockImplementation((url: string) => Promise.resolve(url.endsWith('/me/briefs') ? BRIEFS : mem))
    apiPost.mockResolvedValue(BRIEFS)
    wrap(<ProfileMemoryTab />)
    const btn = await screen.findByRole('button', { name: 'Bật bản tin: Công nợ, thanh toán' })
    expect(apiPost).not.toHaveBeenCalled()
    await userEvent.click(btn)
    await waitFor(() =>
      expect(apiPost).toHaveBeenCalledWith('/api/agent-hub/me/briefs/topics', {
        question: 'Tóm tắt nhanh công nợ, thanh toán của tôi',
        hour: 7,
        minute: 30,
        days: 1,
        sub_code: 'tra_cuu.cong_no',
      }),
    )
  })
})
