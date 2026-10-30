import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { RouterProvider, createMemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import type { SkillDetail } from '../types/ai-skill'
import { SkillEditorPage } from './skill-editor-page'

/**
 * Trang soạn skill (G4). Chỗ dễ lủng:
 * - Xuất bản đọc bản NHÁP đã lưu ở máy chủ — bấm Xuất bản khi còn sửa chưa lưu mà không lưu trước thì AI nhận bản cũ
 *   hơn cái người soạn đang thấy, không ai biết.
 * - Ctrl+S phải lưu nháp, không mở hộp "Lưu trang" của trình duyệt.
 * - Người chỉ có quyền đọc không lưu / xuất bản được.
 */

const apiGet = vi.fn()
const apiPatch = vi.fn()
const apiPost = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPatch: (...args: unknown[]) => apiPatch(...args),
  apiPost: (...args: unknown[]) => apiPost(...args),
  apiPut: vi.fn(),
  apiDelete: vi.fn(),
  httpClient: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}))
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))
vi.mock('@/shared/audit', () => ({ AuditTimeline: () => null }))

function skill(over: Partial<SkillDetail> = {}): SkillDetail {
  return {
    id: 5, skill_set_id: 2, slug: 'quy-trinh-mua', title: 'Quy trình mua', summary: 'Dùng khi hỏi cách mua hàng.',
    status: 2, status_label: 'Đang dùng', current_version_id: 9, version_no: 3, published_at: '2026-10-17T08:00:00',
    has_unpublished_changes: false, draft_updated_at: null, sort_order: 0, draft_body_md: '# Cũ', files: [], ...over,
  }
}

function grant(actions: string[]) {
  const ai_skill = Object.fromEntries(actions.map((a) => [a, true]))
  useAuthStore.setState({ user: { id: 1, permissions: { ai_skill } } as never })
}

function renderEditor() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  const router = createMemoryRouter([{ path: '/ai-skill/skills/:id', element: <SkillEditorPage /> }], {
    initialEntries: ['/ai-skill/skills/5'],
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  apiGet.mockReset()
  apiPatch.mockReset()
  apiPost.mockReset()
  apiGet.mockImplementation((url: string) =>
    url === '/api/ai-skills/skills/5' ? Promise.resolve(skill()) : Promise.resolve({ items: [] }),
  )
  apiPatch.mockImplementation((_url: string, body: { body_md?: string }) =>
    Promise.resolve(skill({ draft_body_md: body.body_md ?? '' })),
  )
  apiPost.mockResolvedValue({ version_id: 10, version_no: 4 })
})

describe('SkillEditorPage', () => {
  it('saves the unsaved draft before publishing, so the AI never gets an older body than the screen shows', async () => {
    grant(['read', 'write', 'approve'])
    renderEditor()
    const body = await screen.findByLabelText('Nội dung skill')
    await userEvent.clear(body)
    await userEvent.type(body, '# Mới')
    await userEvent.click(screen.getByRole('button', { name: /Xuất bản/ }))
    await userEvent.type(screen.getByLabelText('Ghi chú thay đổi'), 'Sửa tiêu đề')
    const dialogButtons = screen.getAllByRole('button', { name: 'Xuất bản' })
    await userEvent.click(dialogButtons[dialogButtons.length - 1])
    await waitFor(() => expect(apiPost).toHaveBeenCalledWith('/api/ai-skills/skills/5/publish', { change_note: 'Sửa tiêu đề' }))
    expect(apiPatch).toHaveBeenCalledWith('/api/ai-skills/skills/5', expect.objectContaining({ body_md: '# Mới' }))
    expect(apiPatch.mock.invocationCallOrder[0]).toBeLessThan(apiPost.mock.invocationCallOrder[0])
  })

  it('publishes without an extra save when nothing changed', async () => {
    grant(['read', 'write', 'approve'])
    renderEditor()
    await screen.findByLabelText('Nội dung skill')
    await userEvent.click(screen.getByRole('button', { name: /Xuất bản/ }))
    const dialogButtons = screen.getAllByRole('button', { name: 'Xuất bản' })
    await userEvent.click(dialogButtons[dialogButtons.length - 1])
    await waitFor(() => expect(apiPost).toHaveBeenCalled())
    expect(apiPatch).not.toHaveBeenCalled()
  })

  it('saves the draft on Ctrl+S and blocks the browser save dialog', async () => {
    grant(['read', 'write'])
    renderEditor()
    const body = await screen.findByLabelText('Nội dung skill')
    await userEvent.type(body, ' thêm')
    const event = new KeyboardEvent('keydown', { key: 's', ctrlKey: true, cancelable: true, bubbles: true })
    window.dispatchEvent(event)
    expect(event.defaultPrevented).toBe(true)
    await waitFor(() => expect(apiPatch).toHaveBeenCalledWith('/api/ai-skills/skills/5', expect.objectContaining({ body_md: '# Cũ thêm' })))
  })

  it('does not save twice when the save button is double-clicked', async () => {
    grant(['read', 'write'])
    let release: () => void = () => undefined
    apiPatch.mockImplementation(() => new Promise((resolve) => { release = () => resolve(skill({ draft_body_md: '# Cũ x' })) }))
    renderEditor()
    const body = await screen.findByLabelText('Nội dung skill')
    await userEvent.type(body, ' x')
    const save = screen.getByRole('button', { name: /Lưu nháp/ })
    fireEvent.click(save)
    fireEvent.click(save)
    release()
    await waitFor(() => expect(apiPatch).toHaveBeenCalledTimes(1))
  })

  it('shows a read-only editor without save or publish to a reader', async () => {
    grant(['read'])
    renderEditor()
    const body = await screen.findByLabelText('Nội dung skill')
    expect(body).toHaveAttribute('readonly')
    expect(screen.queryByRole('button', { name: /Lưu nháp/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Xuất bản/ })).not.toBeInTheDocument()
  })

  it('counts the summary for the AI against the 500 character cap', async () => {
    grant(['read', 'write'])
    renderEditor()
    const summary = await screen.findByLabelText(/Tóm tắt cho AI/)
    await userEvent.clear(summary)
    fireEvent.change(summary, { target: { value: 'x'.repeat(600) } })
    expect(summary).toHaveValue('x'.repeat(500))
    expect(screen.getByText('500/500')).toBeInTheDocument()
  })
})
