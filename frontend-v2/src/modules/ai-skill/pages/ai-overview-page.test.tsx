import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import type { AiOverview } from '../types/ai-skill'
import { AiOverviewPage } from './ai-overview-page'

/**
 * Tổng quan (G1). Đường `ai-overview` đòi `agent_group.read`: thiếu quyền thì trang phải tự nói rõ và KHÔNG gọi để ăn
 * 403. Bảng "Skill được đọc nhiều" chỉ có `skill_id` — phải tra ra tên, tra không được thì in "Skill #id" chứ không
 * để dòng trống. Máy chủ ERP không trả lời thì `skills = null` — thẻ số in "—", không in 0 như thể kho rỗng.
 */

const apiGet = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiPut: vi.fn(),
  apiDelete: vi.fn(),
  httpClient: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}))
//  recharts cần đo kích thước — jsdom không có, thay bằng khung rỗng.
vi.mock('@/shared/ui/column-chart', () => ({ ColumnChart: () => <div data-testid="chart" /> }))

function overview(over: Partial<AiOverview> = {}): AiOverview {
  return {
    generated_at: '2026-10-17T10:00:00', skills: { skill_sets: 3, skills: 12 }, connected_users: 8, connected_days: 30,
    calls_7d: 50, calls_prev_7d: 40, calls_change_pct: 25, denied_7d: 2, error_7d: 1,
    daily: [{ day: '2026-10-17', total: 9, ok: 8, denied: 1, error: 0 }],
    top_tools: [{ key: 'purchase_report', calls: 20 }],
    top_users: [{ key: 5, calls: 30, label: 'Nguyễn An' }],
    top_skills: [{ skill_id: 1, calls: 10 }, { skill_id: 99, calls: 2 }],
    keys_by_state: [{ state: 2, label: 'Đang dùng', count: 6 }],
    expiring_keys: [], expiring_days: 7, ...over,
  }
}

function grant(groupRead: boolean) {
  useAuthStore.setState({
    user: { id: 1, permissions: { ai_skill: { read: true }, ...(groupRead ? { agent_group: { read: true } } : {}) } } as never,
  })
}

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <AiOverviewPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  apiGet.mockReset()
})

describe('AiOverviewPage', () => {
  it('explains the missing right and never calls the overview without agent_group.read', () => {
    grant(false)
    renderPage()
    expect(screen.getByText('Tổng quan dành cho người quản lý trợ lý AI')).toBeInTheDocument()
    expect(apiGet).not.toHaveBeenCalled()
  })

  it('shows the numbers, the change against last week and resolves top skill names with a fallback', async () => {
    grant(true)
    apiGet.mockImplementation((url: string) => {
      if (url === '/api/agent-hub/ai-overview') return Promise.resolve(overview())
      if (url === '/api/ai-skills/skills/1') return Promise.resolve({ id: 1, slug: 'quy-trinh-mua', title: 'Quy trình mua' })
      return Promise.reject(new Error('404'))
    })
    renderPage()
    expect(await screen.findByText('+25% so với 7 ngày trước')).toBeInTheDocument()
    expect(screen.getByText('2 từ chối · 1 lỗi')).toBeInTheDocument()
    expect(await screen.findByText('Quy trình mua')).toBeInTheDocument()
    expect(screen.getByText('Skill #99')).toBeInTheDocument()
    expect(screen.getByText('Nguyễn An')).toBeInTheDocument()
  })

  it('prints a dash, not zero, when the ERP side did not answer the skill counts', async () => {
    grant(true)
    apiGet.mockImplementation((url: string) =>
      url === '/api/agent-hub/ai-overview' ? Promise.resolve(overview({ skills: null, top_skills: [] })) : Promise.resolve(null),
    )
    renderPage()
    expect(await screen.findByText('ERP chưa trả lời')).toBeInTheDocument()
    expect(screen.getAllByText('—').length).toBeGreaterThanOrEqual(2)
  })
})

/**
 * kh-AI2-4 — khối "Sức khỏe dịch vụ AI" (`service_health`). `null` = không đọc được Redis: in "Không đọc được", không
 * in 0 (0 nghĩa là KHÔNG CÓ lỗi, ngược hẳn ý). `counting_5xx = false` (dịch vụ AI chạy nhúng trong ERP) thì máy chủ
 * không đếm 5xx — ô đó không được in số, và câu `note` phải hiện để người đọc biết vì sao.
 */
describe('AiOverviewPage — sức khỏe dịch vụ AI (kh-AI2-4)', () => {
  const NOTE = 'Lỗi 5xx đếm ở dịch vụ AI chạy tách, 24 giờ gần nhất; hàng đợi là số việc nền đang chờ máy chạy.'

  function withHealth(health: AiOverview['service_health']) {
    grant(true)
    apiGet.mockImplementation((url: string) =>
      url === '/api/agent-hub/ai-overview' ? Promise.resolve(overview({ service_health: health })) : Promise.resolve(null),
    )
    renderPage()
  }

  it('shows the 5xx count and both queue lengths, zero included', async () => {
    withHealth({ errors_5xx_24h: 3, queues: { celery: 0, agent_code: 12 }, counting_5xx: true, note: NOTE })
    const block = await screen.findByRole('region', { name: 'Sức khỏe dịch vụ AI' })
    expect(within(block).getByText('3')).toBeInTheDocument()
    expect(within(block).getByText('0')).toBeInTheDocument()
    expect(within(block).getByText('12')).toBeInTheDocument()
    expect(within(block).queryByText('Không đọc được')).not.toBeInTheDocument()
  })

  it('says "Không đọc được" for every null value instead of printing 0', async () => {
    withHealth({ errors_5xx_24h: null, queues: { celery: null, agent_code: null }, counting_5xx: true, note: NOTE })
    const block = await screen.findByRole('region', { name: 'Sức khỏe dịch vụ AI' })
    expect(within(block).getAllByText('Không đọc được')).toHaveLength(3)
    expect(within(block).queryByText('0')).not.toBeInTheDocument()
  })

  it('does not print a 5xx number and shows the note when 5xx are not counted here', async () => {
    withHealth({ errors_5xx_24h: 0, queues: { celery: 1, agent_code: 2 }, counting_5xx: false, note: NOTE })
    const block = await screen.findByRole('region', { name: 'Sức khỏe dịch vụ AI' })
    expect(within(block).getByText(NOTE)).toBeInTheDocument()
    expect(within(block).queryByText('0')).not.toBeInTheDocument()
    expect(within(block).getByText('1')).toBeInTheDocument()
  })

  it('hides the block against an older server that does not send service_health', async () => {
    withHealth(undefined)
    await screen.findByText('2 từ chối · 1 lỗi')
    expect(screen.queryByRole('region', { name: 'Sức khỏe dịch vụ AI' })).not.toBeInTheDocument()
  })

  it('treats a missing queues object as unreadable, not as a crash', async () => {
    withHealth({ errors_5xx_24h: 1, counting_5xx: true, note: NOTE } as unknown as AiOverview['service_health'])
    const block = await screen.findByRole('region', { name: 'Sức khỏe dịch vụ AI' })
    expect(within(block).getAllByText('Không đọc được')).toHaveLength(2)
  })
})
