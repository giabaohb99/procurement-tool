// Mục «Thuốc BVTV»: mặc định lọc «Còn hiệu lực», nút nạp gác theo quyền, câu bảng rỗng đúng
// ngữ cảnh, bấm dòng mở TRANG chi tiết (duoc-CR-492) và lùi về vẫn giữ bộ lọc. Chặn ở tầng
// `@/core/api` (luật testing.md).
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'

import { CustomsPesticideDetailPage } from '../../pages/customs-pesticide-detail-page'
import { CustomsPesticideTab } from './customs-pesticide-tab'

const calls: { url: string; params?: Record<string, unknown> }[] = []
const writes: { method: string; url: string; body?: unknown }[] = []
let granted = new Set(['create', 'write', 'delete'])

//  Lịch sử thao tác của trang chi tiết gọi API nhật ký riêng — không phải thứ bài này kiểm.
vi.mock('@/shared/audit', () => ({ AuditTimeline: () => null }))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    //  Chỉ khóa SỬA danh mục (`customs_pesticide`) là thay đổi theo từng bài; khóa khác cứ mở.
    can: (entity: string, action: string) => entity !== 'customs_pesticide' || granted.has(action),
    canAccess: () => true,
  }),
}))
let catalogTotal = 3
let bannedRules = 3
let items: unknown[] = []

const ROW = {
  id: 11,
  source_id: 2815,
  trade_name: 'Bipyrhone 20EC',
  active_ingredient: 'Bifenazate 277g/l',
  concentration: '277g/l',
  pest_group: 'Thuốc trừ sâu',
  sector: 'THUỐC SỬ DỤNG TRONG NÔNG NGHIỆP',
  registrant: 'Công ty TNHH Ngân Anh',
  registration_no: '514/CNĐKT-BVTV',
  registered_on: '2023-09-25',
  expires_on: '2028-09-25',
  status: 1,
  status_label: 'Còn hiệu lực',
  toxicity: '',
  resistance: '',
  source_url: '',
  use_count: 1,
  summary: 'Thuốc trừ sâu Bipyrhone 20EC hoạt chất Bifenazate 277g/l, sử dụng trên cà rốt, phòng trừ đốm vòng.',
  is_manual: false,
  banned: [] as unknown[],
}

const BANNED = {
  id: 7,
  name: 'Chlorpyrifos ethyl',
  cas_no: '2921-88-2',
  banned_year: 2019,
  legal_basis: 'TT 75/2025/TT-BNNMT',
}

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return {
    ...actual,
    apiGet: async (url: string, config?: { params?: Record<string, unknown> }) => {
      calls.push({ url, params: config?.params })
      if (url.endsWith('/pesticides/options')) {
        return {
          total: catalogTotal,
          last_loaded_at: null,
          statuses: [
            { value: 1, label: 'Còn hiệu lực', count: 2 },
            { value: 2, label: 'Hết hiệu lực', count: 1 },
          ],
          pest_groups: [],
          sectors: [],
          banned_rules: bannedRules,
          banned_count: 0,
        }
      }
      if (url.endsWith('/pesticides')) return { total: items.length, items }
      if (url.startsWith('/api/attachments')) return []
      if (url.endsWith('/pesticides/11')) {
        return {
          ...((items[0] as typeof ROW | undefined) ?? ROW),
          uses: [
            {
              id: 1,
              crop: 'cà rốt',
              pest: 'đốm vòng',
              dosage: '0.4 lít/ha',
              pre_harvest_interval: '7 ngày',
              usage: 'Phun',
            },
          ],
        }
      }
      throw new Error(`Không mock đường ${url}`)
    },
    apiPost: async (url: string, body?: unknown) => {
      writes.push({ method: 'POST', url, body })
      return { ...ROW, id: 11, is_manual: true, uses: [] }
    },
    apiPatch: async (url: string, body?: unknown) => {
      writes.push({ method: 'PATCH', url, body })
      return { ...ROW, uses: [] }
    },
    apiDelete: async (url: string) => {
      writes.push({ method: 'DELETE', url })
      return null
    },
  }
})

/** Hiện đường + query hiện tại để khẳng định bộ lọc nằm trên URL và quay về đúng chỗ. */
function WhereAmI() {
  const location = useLocation()
  return <output data-testid="where">{`${location.pathname}${location.search}`}</output>
}

function build() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <Routes>
          <Route path="/" element={<CustomsPesticideTab />} />
          <Route path="/procurement/customs-prices/pesticides/:id" element={<CustomsPesticideDetailPage />} />
        </Routes>
        <WhereAmI />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  calls.length = 0
  catalogTotal = 3
  bannedRules = 3
  granted = new Set(['create', 'write', 'delete'])
  writes.length = 0
  items = []
  localStorage.clear()
})

describe('CustomsPesticideTab', () => {
  it('asks for active registrations only by default, starting at page 1', async () => {
    build()
    await waitFor(() => expect(calls.some((call) => call.url.endsWith('/pesticides'))).toBe(true))
    const list = calls.find((call) => call.url.endsWith('/pesticides'))
    expect(list?.params).toMatchObject({ status: '1', page: 1, page_size: 50 })
  })

  it('hides the import and add buttons without the customs_pesticide keys', async () => {
    granted = new Set()
    build()
    await screen.findByText(/khớp bộ lọc/)
    expect(screen.queryByRole('button', { name: /Nạp danh mục/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Thêm thuốc/ })).not.toBeInTheDocument()
  })

  it('tells an importer the catalog is empty instead of blaming the filter', async () => {
    catalogTotal = 0
    build()
    expect(
      await screen.findByText(/Chưa có danh mục thuốc BVTV\. Bấm «Nạp danh mục»/),
    ).toBeInTheDocument()
  })

  it('opens the usage scope of a drug when its row is clicked', async () => {
    items = [ROW]
    build()
    fireEvent.click(await screen.findByText('Bipyrhone 20EC'))
    expect(await screen.findByText('đốm vòng')).toBeInTheDocument()
    expect(screen.getByText('Phạm vi sử dụng (1)')).toBeInTheDocument()
    //  Ô nguồn không ghi phải NÓI ra, không để trống như lỗi màn hình.
    expect(screen.getAllByText('Nguồn không ghi').length).toBeGreaterThan(0)
  })

  it('offers «Xóa lọc» once a filter moves off the default and puts the default status back', async () => {
    build()
    const search = await screen.findByRole('textbox', { name: 'Tìm thuốc BVTV' })
    expect(screen.queryByRole('button', { name: /Xóa lọc/ })).not.toBeInTheDocument()
    fireEvent.change(search, { target: { value: 'atrazine' } })
    fireEvent.click(await screen.findByRole('button', { name: /Xóa lọc/ }))
    expect(search).toHaveValue('')
    await waitFor(() => {
      const last = calls.filter((call) => call.url.endsWith('/pesticides')).at(-1)
      expect(last?.params).toMatchObject({ status: '1' })
      expect(last?.params).not.toHaveProperty('q')
    })
  })

  it('warns how many drugs an import will replace, and keeps the button off until a file is picked', async () => {
    build()
    await screen.findByText(/khớp bộ lọc/)
    fireEvent.click(screen.getByRole('button', { name: /Nạp danh mục/ }))
    expect(await screen.findByText(/thay toàn bộ/)).toBeInTheDocument()
    const dialogButtons = screen.getAllByRole('button', { name: /Nạp danh mục/ })
    expect(dialogButtons[dialogButtons.length - 1]).toBeDisabled()
  })

  it('flags a drug whose active ingredient is on the banned list, in the row and in its detail', async () => {
    items = [{ ...ROW, banned: [BANNED] }]
    build()
    expect(await screen.findByText('Chlorpyrifos ethyl')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Bipyrhone 20EC'))
    const notice = await screen.findByRole('alert')
    expect(notice).toHaveTextContent('Có hoạt chất nằm trong danh sách cấm')
    expect(notice).toHaveTextContent('CẤM từ 2019')
    expect(notice).toHaveTextContent('CAS 2921-88-2')
    //  Khớp bằng tên giữa hai danh mục — phải nói là tham khảo, đừng để đọc thành kết luận pháp lý.
    expect(notice).toHaveTextContent(/tham khảo/)
  })

  it('shows no banned notice for a clean drug', async () => {
    items = [ROW]
    build()
    fireEvent.click(await screen.findByText('Bipyrhone 20EC'))
    await screen.findByText('đốm vòng')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('filters to banned drugs only and reads an empty result as a clean catalog', async () => {
    const user = userEvent.setup()
    build()
    await user.click(await screen.findByRole('combobox', { name: 'Lọc theo hoạt chất cấm' }))
    await user.click(await screen.findByRole('option', { name: 'Có hoạt chất cấm (0)' }))
    await waitFor(() => {
      const last = calls.filter((call) => call.url.endsWith('/pesticides')).at(-1)
      expect(last?.params).toMatchObject({ banned_only: 'true', status: '1', page: 1 })
    })
    //  Rỗng lúc này là KẾT QUẢ TỐT — không được bảo người dùng «thử bỏ lọc».
    expect(await screen.findByText(/Không thuốc nào trong bộ lọc đang chọn chứa hoạt chất cấm/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Xóa lọc/ }))
    await waitFor(() => {
      const last = calls.filter((call) => call.url.endsWith('/pesticides')).at(-1)
      expect(last?.params).not.toHaveProperty('banned_only')
    })
  })

  it('says there is no banned list yet instead of showing a reassuring (0)', async () => {
    bannedRules = 0
    const user = userEvent.setup()
    build()
    await user.click(await screen.findByRole('combobox', { name: 'Lọc theo hoạt chất cấm' }))
    expect(
      await screen.findByRole('option', { name: 'Có hoạt chất cấm (chưa có danh sách cấm)' }),
    ).toBeInTheDocument()
  })

  describe('thêm / sửa / xóa (customs_pesticide)', () => {
    it('refuses to save without a name and never calls the API', async () => {
      build()
      fireEvent.click(await screen.findByRole('button', { name: /Thêm thuốc/ }))
      fireEvent.click(await screen.findByRole('button', { name: 'Thêm thuốc' }))
      expect(await screen.findByText('Nhập tên thuốc.')).toBeInTheDocument()
      expect(writes).toEqual([])
    })

    //  Bẫy duoc-CR-317: Enter trong ô con của `<form>` lưu cả bản ghi khi người dùng chưa xong.
    it('does not save when Enter is pressed inside a field', async () => {
      build()
      fireEvent.click(await screen.findByRole('button', { name: /Thêm thuốc/ }))
      const name = await screen.findByLabelText(/Tên thuốc/)
      fireEvent.change(name, { target: { value: 'Mới 10EC' } })
      fireEvent.change(screen.getByLabelText(/Hoạt chất/), { target: { value: 'Abamectin 10g/l' } })
      fireEvent.keyDown(name, { key: 'Enter' })
      fireEvent.click(screen.getByRole('button', { name: /Thêm dòng/ }))
      fireEvent.keyDown(screen.getByLabelText('Cây trồng — dòng 1'), { key: 'Enter' })
      expect(writes).toEqual([])
    })

    it('posts a trimmed body once, drops blank usage rows, then opens the saved drug', async () => {
      build()
      fireEvent.click(await screen.findByRole('button', { name: /Thêm thuốc/ }))
      fireEvent.change(await screen.findByLabelText(/Tên thuốc/), { target: { value: '  Mới 10EC ' } })
      fireEvent.change(screen.getByLabelText(/Hoạt chất/), { target: { value: 'Abamectin 10g/l' } })
      fireEvent.click(screen.getByRole('button', { name: /Thêm dòng/ }))
      fireEvent.click(screen.getByRole('button', { name: /Thêm dòng/ }))
      fireEvent.change(screen.getByLabelText('Cây trồng — dòng 2'), { target: { value: 'lúa' } })
      const submit = screen.getByRole('button', { name: 'Thêm thuốc' })
      //  Bấm đúp: `disabled` chỉ đổi ở lượt vẽ sau, chốt `useRef` phải chặn lượt thứ hai.
      fireEvent.click(submit)
      fireEvent.click(submit)
      await waitFor(() => expect(writes).toHaveLength(1))
      const body = writes[0]?.body as { trade_name: string; uses: { crop: string }[]; expires_on: unknown }
      expect(writes[0]?.method).toBe('POST')
      expect(body.trade_name).toBe('Mới 10EC')
      expect(body.uses.map((use) => use.crop)).toEqual(['lúa'])
      expect(body.expires_on).toBeNull()
      expect(await screen.findByText('đốm vòng')).toBeInTheDocument()
    })

    it('warns that a source drug edit will be overwritten by the next import', async () => {
      items = [ROW]
      build()
      fireEvent.click(await screen.findByText('Bipyrhone 20EC'))
      fireEvent.click(await screen.findByRole('button', { name: 'Sửa' }))
      expect(await screen.findByText(/lần «Nạp danh mục» sau sẽ ghi đè/)).toBeInTheDocument()
      expect(screen.getByLabelText(/Tên thuốc/)).toHaveValue('Bipyrhone 20EC')
      fireEvent.click(screen.getByRole('button', { name: 'Lưu' }))
      await waitFor(() =>
        expect(writes[0]).toMatchObject({ method: 'PATCH', url: '/api/customs/pesticides/11' }),
      )
      expect((writes[0]?.body as { uses: unknown[] }).uses).toHaveLength(1)
    })

    it('shows edit and delete only with their own actions', async () => {
      items = [ROW]
      granted = new Set(['create'])
      build()
      fireEvent.click(await screen.findByText('Bipyrhone 20EC'))
      await screen.findByText('đốm vòng')
      expect(screen.queryByRole('button', { name: 'Sửa' })).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /Xóa/ })).not.toBeInTheDocument()
    })
  })

  //  duoc-CR-492: chi tiết là TRANG riêng — lùi về mà mất bộ lọc vừa gõ thì người dùng phải gõ lại
  //  sau mỗi lần xem một thuốc. Bộ lọc nằm trên URL, trang chi tiết lùi về đúng URL đó.
  it('keeps the filters when coming back from the detail page', async () => {
    items = [ROW]
    build()
    fireEvent.change(await screen.findByRole('textbox', { name: 'Tìm thuốc BVTV' }), {
      target: { value: 'bipy' },
    })
    await waitFor(() => expect(screen.getByTestId('where')).toHaveTextContent('pq=bipy'))
    fireEvent.click(await screen.findByText('Bipyrhone 20EC'))
    await waitFor(() =>
      expect(screen.getByTestId('where')).toHaveTextContent('/procurement/customs-prices/pesticides/11'),
    )
    fireEvent.click(await screen.findByRole('button', { name: 'Quay lại danh mục thuốc BVTV' }))
    await waitFor(() => expect(screen.getByTestId('where')).toHaveTextContent('/?pq=bipy'))
    expect(await screen.findByRole('textbox', { name: 'Tìm thuốc BVTV' })).toHaveValue('bipy')
  })

  it('titles the usage table so it is clear what it lists', async () => {
    items = [ROW]
    build()
    fireEvent.click(await screen.findByText('Bipyrhone 20EC'))
    expect(await screen.findByRole('heading', { name: 'Phạm vi sử dụng (1)' })).toBeInTheDocument()
    expect(screen.getByText(/thời gian cách ly/)).toBeInTheDocument()
    expect(screen.queryByText('Xem trên danh mục nguồn')).not.toBeInTheDocument()
  })

  //  duoc-CR-494: tệp của thuốc (nhãn, giấy chứng nhận đăng ký…) — ai xem được thuốc thì xem được
  //  tệp; nút tải lên chỉ cho người có khóa SỬA danh mục (`customs_pesticide` write/create).
  it('shows the attachments card on the detail page, upload only with the edit key', async () => {
    items = [ROW]
    const { unmount } = build()
    fireEvent.click(await screen.findByText('Bipyrhone 20EC'))
    expect(await screen.findByText('Chứng từ & Tài liệu đính kèm')).toBeInTheDocument()
    expect(await screen.findByRole('button', { name: /Upload chứng từ/ })).toBeInTheDocument()
    await waitFor(() =>
      expect(calls.some((c) => c.url.startsWith('/api/attachments') && c.params?.entity === 'customs_pesticide')).toBe(true),
    )
    unmount()
    granted = new Set()
    build()
    fireEvent.click(await screen.findByText('Bipyrhone 20EC'))
    expect(await screen.findByText('Chứng từ & Tài liệu đính kèm')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Upload chứng từ/ })).not.toBeInTheDocument()
  })

  //  duoc-CR-495 — câu mô tả của trang nguồn: đọc một câu là biết thuốc trị gì, trên cây gì.
  it('shows the source summary sentence on the detail page and pre-fills it when editing', async () => {
    items = [ROW]
    build()
    fireEvent.click(await screen.findByText('Bipyrhone 20EC'))
    expect(await screen.findByText(/sử dụng trên cà rốt, phòng trừ đốm vòng/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Sửa' }))
    expect(await screen.findByLabelText('Mô tả tóm tắt')).toHaveValue(ROW.summary)
  })
})
