import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ReleaseEntry, ReleaseNotesResult, ReleaseVersion } from '@/shared/release/release-api'
import { filterReleases, runningVersionText } from '@/shared/release/release-format'
import { WhatsNewPage } from './whats-new-page'

/**
 * Có gì mới (bao-CR-722).
 *
 * Chỗ dễ lủng:
 * - Image không truyền BUILD_COMMIT thì dòng phiên bản ghi "không rõ", không in chuỗi rỗng.
 * - Lọc phân hệ: bỏ cả đợt không có mục khớp, trong đợt chỉ giữ mục khớp.
 * - Mở trang là ghi "đã xem" đúng phiên bản đang chạy — nhưng KHÔNG ghi khi đã xem rồi.
 */

const apiGet = vi.fn()
const apiPut = vi.fn()
let seenVersion = ''

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPut: (...args: unknown[]) => apiPut(...args),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
}))
vi.mock('@/core/auth/use-auth', () => ({
  useAuth: () => ({ user: { id: 1, preferences: { release_seen_version: seenVersion } } }),
}))

const VERSION: ReleaseVersion = {
  version: '2026.11.04',
  release_date: '2026-11-04',
  release_title: 'Đợt tháng 11',
  commit: 'abc1234',
  built_at: '2026-11-04T01:30:00',
  environment: 'prod',
}
const RELEASES: ReleaseEntry[] = [
  {
    version: '2026.11.04',
    date: '2026-11-04',
    title: 'Đợt tháng 11',
    notes: [
      { module: 'Nghỉ phép', kind: 'them', kind_label: 'Thêm', cr: 'duoc-CR-715', text: 'Phiếu nghỉ bù.' },
      { module: 'Quản trị', kind: 'them', kind_label: 'Thêm', cr: 'bao-CR-721', text: 'Màn Nhật ký email.' },
    ],
    remarks: ['Có tám thay đổi cấu trúc dữ liệu.'],
  },
  {
    version: '2026.10.31',
    date: '2026-10-31',
    title: 'Đợt cuối tháng 10',
    notes: [{ module: 'Thu mua', kind: 'sua', kind_label: 'Sửa', cr: 'bao-CR-705', text: 'Thêm cột Phòng xử lý.' }],
    remarks: [],
  },
]
const NOTES: ReleaseNotesResult = {
  releases: RELEASES,
  modules: ['Thu mua', 'Nghỉ phép', 'Quản trị'],
  kinds: [{ code: 'them', label: 'Thêm' }],
  version: VERSION,
}

function dung() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <WhatsNewPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  apiGet.mockReset()
  apiPut.mockReset()
  seenVersion = ''
  apiGet.mockImplementation((url: string) => {
    if (url.startsWith('/api/system/version')) return Promise.resolve(VERSION)
    if (url.startsWith('/api/system/release-notes')) return Promise.resolve(NOTES)
    if (url.startsWith('/api/me/preferences')) return Promise.resolve({ release_seen_version: seenVersion })
    return Promise.reject(new Error(`không mock: ${url}`))
  })
  apiPut.mockResolvedValue({ release_seen_version: '2026.11.04' })
})

describe('runningVersionText', () => {
  it('đủ dữ liệu thì ghi phiên bản, commit, giờ build, môi trường', () => {
    expect(runningVersionText(VERSION, '')).toMatch(/^Phiên bản 2026\.11\.04 · máy chủ abc1234 · build lúc .+ · prod$/)
  })
  it('thiếu commit / giờ build thì ghi không rõ, không in chuỗi rỗng', () => {
    const text = runningVersionText({ ...VERSION, commit: '', built_at: '', environment: '' }, '')
    expect(text).toBe('Phiên bản 2026.11.04 · máy chủ không rõ · giờ build không rõ')
  })
  it('commit giao diện khác máy chủ thì nêu cả hai', () => {
    expect(runningVersionText(VERSION, 'fff9999')).toContain('giao diện fff9999')
    expect(runningVersionText(VERSION, 'abc1234')).not.toContain('giao diện')
  })
})

describe('filterReleases', () => {
  it('bỏ đợt không có mục khớp, trong đợt chỉ giữ mục khớp', () => {
    const out = filterReleases(RELEASES, 'Quản trị')
    expect(out).toHaveLength(1)
    expect(out[0].notes.map((n) => n.cr)).toEqual(['bao-CR-721'])
    expect(filterReleases(RELEASES, '')).toBe(RELEASES)
  })
})

describe('WhatsNewPage', () => {
  it('in các đợt mới nhất trước, nhãn loại, lưu ý; mở trang thì ghi đã xem bản đang chạy', async () => {
    dung()
    expect(await screen.findByText('Bản 2026.11.04')).toBeInTheDocument()
    expect(screen.getByText('Bản 2026.10.31')).toBeInTheDocument()
    expect(screen.getByText('Mới nhất')).toBeInTheDocument()
    expect(screen.getAllByText('Thêm').length).toBe(2)
    expect(screen.getByText('Có tám thay đổi cấu trúc dữ liệu.')).toBeInTheDocument()
    await waitFor(() => expect(apiPut).toHaveBeenCalledTimes(1))
    expect(apiPut.mock.calls[0][1]).toEqual({ values: { release_seen_version: '2026.11.04' } })
  })

  it('đã xem bản đang chạy rồi thì không ghi lại', async () => {
    seenVersion = '2026.11.04'
    dung()
    expect(await screen.findByText('Bản 2026.11.04')).toBeInTheDocument()
    await new Promise((r) => setTimeout(r, 50))
    expect(apiPut).not.toHaveBeenCalled()
  })
})
