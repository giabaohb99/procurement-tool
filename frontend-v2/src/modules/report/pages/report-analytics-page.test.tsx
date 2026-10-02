import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiGet, downloadFile } from '@/core/api'
import type * as CoreApiModule from '@/core/api'
import { TooltipProvider } from '@/shared/ui/tooltip'

import type { ReportAnalyticsResponse, ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

//  Mock ở TẦNG `@/core/api` (không mock axios) — đúng luật `testing.md`: hook
//  và hàm dựng tham số (`useReportFilters`, `useReportAnalytics`) chạy CODE THẬT,
//  chỉ biên mạng là giả. `extractErrorMessage` giữ NGUYÊN bản thật (M6 cần nó
//  đọc đúng hình dạng lỗi backend) — chỉ giả hai hàm gọi mạng.
vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApiModule>()
  return { ...actual, apiGet: vi.fn(), downloadFile: vi.fn() }
})

let canExport = false
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (_entity: string, action: string) => action === 'export' && canExport,
  }),
}))
//  Ô Công ty mượn danh mục Nhân sự — tắt hẳn ở đây (thiếu quyền `company.read`
//  qua mock ở trên) nên không cần giả thêm API danh sách công ty.

/** Hợp đồng JSON chuẩn (phase-01 §Architecture) — một mốc thiếu kỳ so sánh, một mốc đủ. */
function buildFixture(compare: 'previous' | 'year' | 'none'): ReportAnalyticsResponse {
  const compareValues = compare === 'none' ? null : { lines: 100, amount: 400_000_000 }
  return {
    period: {
      date_from: '2026-09-01',
      date_to: '2026-09-28',
      compare_from: compare === 'none' ? null : '2026-08-01',
      compare_to: compare === 'none' ? null : '2026-08-28',
      compare,
      granularity: 'day',
      preset: 'this_month',
    },
    meta: {
      metrics: [
        {
          key: 'lines',
          label: 'Dòng hàng',
          kind: 'int',
          good: null,
          helper: false,
          snapshot: false,
        },
        {
          key: 'amount',
          label: 'Giá trị',
          kind: 'money',
          good: null,
          helper: false,
          snapshot: false,
        },
      ],
      dimensions: [
        { key: 'department', label: 'Bộ phận' },
        { key: 'item_group', label: 'Nhóm hàng' },
      ],
      group_by: 'department',
    },
    totals: { current: { lines: 120, amount: 500_000_000 }, compare: compareValues },
    trend: [
      {
        key: '2026-09-01',
        label: '01/09',
        current: { lines: 10, amount: 40_000_000 },
        compare: null,
      },
      {
        key: '2026-09-02',
        label: '02/09',
        current: { lines: 12, amount: 42_000_000 },
        compare: compare === 'none' ? null : { lines: 8, amount: 35_000_000 },
      },
    ],
    groups: [
      {
        key: 'kd',
        label: 'Kinh doanh',
        current: { lines: 70, amount: 300_000_000 },
        compare: compareValues,
      },
      {
        key: 'kt',
        label: 'Kế toán',
        current: { lines: 50, amount: 200_000_000 },
        compare: compareValues,
      },
    ],
    breakdowns: { by_supplier: [{ key: 's1', label: 'NCC A', value: 10 }] },
    notes: [],
  }
}

const TEST_CONFIG: ReportPageConfig = {
  endpoint: '/api/reports/test/summary',
  exportEndpoint: '/api/reports/test/summary/export',
  entity: 'report',
  title: 'Báo cáo thử',
  description: 'Mô tả báo cáo thử.',
  slug: 'test',
  kpis: ['lines', 'amount'],
  chartMetric: 'lines',
  defaultGroupBy: 'department',
  breakdowns: [{ key: 'by_supplier', title: 'Top nhà cung cấp' }],
}

beforeEach(() => {
  canExport = false
  vi.mocked(apiGet).mockReset()
  vi.mocked(downloadFile).mockReset().mockResolvedValue(undefined)
  vi.mocked(apiGet).mockImplementation(async (_url, config) => {
    const params = (config as { params?: Record<string, string> })?.params ?? {}
    const compare = (params.compare as 'previous' | 'year' | 'none') || 'previous'
    return buildFixture(compare)
  })
})

function renderPage(url = '/report/test', config: ReportPageConfig = TEST_CONFIG) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[url]}>
        <TooltipProvider>
          <ReportAnalyticsPage config={config} />
        </TooltipProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

//  "Dòng hàng"/"Giá trị" xuất hiện Ở CẢ nhãn thẻ KPI LẪN tiêu đề cột của bảng
//  nhóm bên dưới — dùng `findByText('500 tr đ')` (giá trị TIỀN dạng rút gọn,
//  chỉ thẻ KPI mới hiện kiểu này) làm mốc "đã tải xong" không mập mờ.
const KPI_LOADED_MARK = '500 tr đ'

describe('ReportAnalyticsPage — KPI cards from meta', () => {
  it('renders one KPI card per configured metric, labelled and formatted from `meta`', async () => {
    renderPage()
    expect(await screen.findByText(KPI_LOADED_MARK)).toBeInTheDocument()
    expect(screen.getAllByText('Dòng hàng').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Giá trị').length).toBeGreaterThan(0)
    //  Chỉ số nguyên (`kind: 'int'`) của tổng — thẻ KPI VÀ dòng Tổng của bảng
    //  cùng hiện "120" nên chỉ kiểm có mặt, không đòi duy nhất.
    expect(screen.getAllByText('120').length).toBeGreaterThan(0)
  })
})

describe('ReportAnalyticsPage — Tổng row pinned first', () => {
  it('keeps the Tổng row as the first data row of the grouped table', async () => {
    renderPage()
    await screen.findByText(KPI_LOADED_MARK)
    const rows = screen.getAllByRole('row')
    // rows[0] = header; rows[1] = first data row.
    expect(rows[1]).toHaveTextContent('Tổng')
  })
})

//  Kiểu Haravan: MỘT cột/chỉ số — ±% nằm dưới giá trị TRONG cùng ô, không phải
//  cột riêng (xem `ReportGroupedTable`/`MetricValueCell`).
describe('ReportAnalyticsPage — the ±% line inside each metric cell follows compare mode', () => {
  it('shows the change line when compare is active (120 vs kỳ trước 100 → +20%)', async () => {
    renderPage('/report/test?compare=previous')
    await screen.findByText(KPI_LOADED_MARK)
    //  Thẻ KPI (`ReportKpiRow`) VÀ ô bảng dòng Tổng (`ReportGroupedTable`) đều
    //  hiện "+20%" — hai nơi độc lập, cùng công thức, đúng ý muốn không phải
    //  đòi duy nhất một chỗ.
    expect(screen.getAllByText('+20%').length).toBeGreaterThan(0)
    //  Vẫn đúng MỘT cột "Dòng hàng" — không có cột phụ "Dòng hàng kỳ trước"/"±%".
    expect(screen.queryByText('Dòng hàng ±%')).not.toBeInTheDocument()
  })

  it('hides the change line entirely when compare=none', async () => {
    renderPage('/report/test?compare=none')
    await screen.findByText(KPI_LOADED_MARK)
    expect(screen.queryByText('+20%')).not.toBeInTheDocument()
  })
})

describe('ReportAnalyticsPage — clicking a KPI card switches the trend chart metric', () => {
  it('starts on config.chartMetric, switches after a click', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('Xu hướng Dòng hàng')

    //  Chuỗi đầu tiên trong DOM là thẻ KPI (`ReportKpiRow` đứng trước
    //  `ReportGroupedTable`) — chuỗi thứ hai là tiêu đề cột của bảng.
    await user.click(screen.getAllByText('Giá trị')[0])
    expect(await screen.findByText('Xu hướng Giá trị')).toBeInTheDocument()
  })
})

describe('ReportAnalyticsPage — "Xem theo" writes group_by to the URL and refetches', () => {
  it('changing the dimension select triggers a new call with the new group_by param', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByText(KPI_LOADED_MARK)

    await user.click(screen.getByRole('combobox', { name: 'Xem theo' }))
    //  Nhãn "Xem theo" nay đứng NGOÀI ô chọn (`ReportGroupBySelect`), mục
    //  trong danh sách chỉ còn tên chiều.
    await user.click(screen.getByRole('option', { name: 'Nhóm hàng' }))

    await waitFor(() => {
      const lastCall = vi.mocked(apiGet).mock.calls.at(-1)
      const params = (lastCall?.[1] as { params?: Record<string, string> })?.params
      expect(params?.group_by).toBe('item_group')
    })
  })
})

describe('ReportAnalyticsPage — Xuất Excel gated by can(entity, "export")', () => {
  it('hides the export button without the permission', async () => {
    canExport = false
    renderPage()
    await screen.findByText(KPI_LOADED_MARK)
    expect(screen.queryByRole('button', { name: /Xuất Excel/ })).not.toBeInTheDocument()
  })

  it('shows it with the permission and downloads exactly once even on a rapid double click', async () => {
    canExport = true
    const user = userEvent.setup()
    renderPage()
    await screen.findByText(KPI_LOADED_MARK)

    //  bao-CR-561: giữ lượt tải ĐANG CHẠY cho tới khi cả hai cú bấm đã vào. Bản cũ cho mock xong
    //  ngay lập tức nên cú bấm thứ hai đôi khi tới SAU khi lượt đầu đã xong — hai lần tải hợp lệ,
    //  bài kiểm đỏ ngẫu nhiên (2/3 lần khi gom erp-v2 lên prod 02/10/2026), không phải lỗi chốt chặn.
    let finishDownload: () => void = () => {}
    vi.mocked(downloadFile).mockImplementation(
      () => new Promise<void>((resolve) => { finishDownload = resolve }),
    )
    const button = screen.getByRole('button', { name: /Xuất Excel/ })
    //  Bấm đúp trong cùng một nhịp — đúng bẫy `useSingleFlight` phải chặn
    //  (`disabled={isPending}` một mình không chặn được, xem use-single-flight.ts).
    await Promise.all([user.click(button), user.click(button)])
    finishDownload()

    await waitFor(() => expect(downloadFile).toHaveBeenCalledTimes(1))
    expect(downloadFile).toHaveBeenCalledWith(
      '/api/reports/test/summary/export',
      expect.stringMatching(/^bao-cao-test-.*\.xlsx$/),
      expect.objectContaining({ preset: 'this_month' }),
    )
  })
})

describe('ReportAnalyticsPage — legacy ?year= link still opens the right period', () => {
  it('translates ?year=2025 into preset=custom with the full calendar year on the API call', async () => {
    renderPage('/report/test?year=2025')
    await screen.findByText(KPI_LOADED_MARK)

    await waitFor(() => {
      const lastCall = vi.mocked(apiGet).mock.calls.at(-1)
      const params = (lastCall?.[1] as { params?: Record<string, string> })?.params
      expect(params).toMatchObject({
        preset: 'custom',
        date_from: '2025-01-01',
        date_to: '2025-12-31',
      })
    })
  })
})

//  Backend đánh dấu chỉ số PHỤ (vd `deliveries_done` chỉ để làm mẫu số của
//  `on_time_rate`) bằng `meta.metrics[].helper` — thay cho `config.hiddenMetrics`
//  cũ đã bỏ. Nó không được đứng thành thẻ KPI LẪN cột bảng.
describe('ReportAnalyticsPage — meta.metrics[].helper keeps a metric out of KPI cards and the grouped table', () => {
  it('drops the helper metric everywhere while other metrics stay', async () => {
    vi.mocked(apiGet).mockImplementation(async () => {
      const base = buildFixture('previous')
      return {
        ...base,
        meta: {
          ...base.meta,
          metrics: [
            ...base.meta.metrics,
            {
              key: 'helper',
              label: 'Mẫu số phụ',
              kind: 'int',
              good: null,
              helper: true,
              snapshot: false,
            },
          ],
        },
      }
    })

    renderPage('/report/test')
    await screen.findByText(KPI_LOADED_MARK)

    expect(screen.queryByText('Mẫu số phụ')).not.toBeInTheDocument()
    //  Cột thường (không phải helper) vẫn phải còn nguyên trong bảng.
    expect(screen.getAllByText('Dòng hàng').length).toBeGreaterThan(0)
  })
})

//  snapshot: giá trị chỉ có ở Tổng (vd công nợ) — không có mặt trong
//  `trend[]`/`groups[]`. Dòng nhóm phải ra "—", dòng Tổng vẫn hiện số thật.
describe('ReportAnalyticsPage — meta.metrics[].snapshot shows the value only on the Tổng row', () => {
  it('renders — on group rows and the real number on Tổng', async () => {
    vi.mocked(apiGet).mockImplementation(async () => {
      const base = buildFixture('none')
      return {
        ...base,
        meta: {
          ...base.meta,
          metrics: [
            ...base.meta.metrics,
            {
              key: 'debt',
              label: 'Công nợ quá hạn',
              kind: 'money',
              good: 'down',
              helper: false,
              snapshot: true,
            },
          ],
        },
        //  `groups[].current` KHÔNG có khóa `debt` — đúng hợp đồng backend cho
        //  snapshot, `base.groups` (fixture gốc) vốn đã không có khóa đó.
        totals: { current: { ...base.totals.current, debt: 133_100_000 }, compare: null },
      }
    })

    renderPage('/report/test', { ...TEST_CONFIG, kpis: ['lines', 'amount', 'debt'] })
    await screen.findByText(KPI_LOADED_MARK)

    const rows = screen.getAllByRole('row')
    // rows[0] = header, rows[1] = Tổng.
    expect(rows[1]).toHaveTextContent('133.100.000 đ')
    expect(rows[2]).toHaveTextContent('—')
  })
})

describe('ReportAnalyticsPage — M6 dead-end guard on 403/422', () => {
  it('shows the backend message plus a reset button on 403, resetting only group_by', async () => {
    vi.mocked(apiGet).mockImplementation(async (_url, config) => {
      const params = (config as { params?: Record<string, string> })?.params ?? {}
      if (params.group_by === 'supplier') {
        const err = new Error('Request failed with status code 403') as Error & {
          response?: { status: number; data: { success: false; error: { message: string } } }
        }
        err.response = {
          status: 403,
          data: { success: false, error: { message: 'Bạn không có quyền xem theo Nhà cung cấp.' } },
        }
        throw err
      }
      return buildFixture('previous')
    })

    const user = userEvent.setup()
    renderPage('/report/test?group_by=supplier')

    expect(await screen.findByText('Bạn không có quyền xem theo Nhà cung cấp.')).toBeInTheDocument()
    //  Không dead-end: KPI/biểu đồ/bảng (rỗng) không đứng cạnh câu lỗi.
    expect(screen.queryByRole('table')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Đặt lại bộ lọc' }))

    await waitFor(() => {
      const lastCall = vi.mocked(apiGet).mock.calls.at(-1)
      const params = (lastCall?.[1] as { params?: Record<string, string> })?.params
      expect(params?.group_by).toBe('department')
    })
  })

  it('also resets the period back to its default on 422 (bad date range)', async () => {
    vi.mocked(apiGet).mockImplementation(async (_url, config) => {
      const params = (config as { params?: Record<string, string> })?.params ?? {}
      if (params.date_from === '2001-01-01') {
        const err = new Error('Request failed with status code 422') as Error & {
          response?: { status: number; data: { success: false; error: { message: string } } }
        }
        err.response = {
          status: 422,
          data: { success: false, error: { message: 'Khoảng ngày không hợp lệ.' } },
        }
        throw err
      }
      return buildFixture('previous')
    })

    const user = userEvent.setup()
    renderPage('/report/test?preset=custom&date_from=2001-01-01&date_to=2001-01-31')

    expect(await screen.findByText('Khoảng ngày không hợp lệ.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Đặt lại bộ lọc' }))

    await waitFor(() => {
      const lastCall = vi.mocked(apiGet).mock.calls.at(-1)
      const params = (lastCall?.[1] as { params?: Record<string, string> })?.params
      expect(params?.preset).toBe('this_month')
      expect(params?.date_from).toBeUndefined()
    })
  })
})

describe('ReportAnalyticsPage — notes from the response render under the filters', () => {
  //  01/10/2026: lưu ý cách tính gấp sẵn thành một dòng (khối mở sẵn chắn ngay
  //  trên thẻ KPI bị chê xấu) — nhưng KHÔNG được mất câu nào khi mở ra.
  it('collapses notes into one line and shows every note once opened', async () => {
    vi.mocked(apiGet).mockImplementation(async () => ({
      ...buildFixture('previous'),
      notes: ['Số liệu công nợ là XẤP XỈ.', 'Bỏ dòng đã hủy.'],
    }))

    renderPage()
    await screen.findByText(KPI_LOADED_MARK)

    expect(screen.queryByText('Số liệu công nợ là XẤP XỈ.')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Cách tính số liệu \(2 lưu ý\)/ }))
    expect(screen.getByText('Số liệu công nợ là XẤP XỈ.')).toBeInTheDocument()
    expect(screen.getByText('Bỏ dòng đã hủy.')).toBeInTheDocument()
  })

  it('renders no notes toggle when the backend sends none', async () => {
    renderPage()
    await screen.findByText(KPI_LOADED_MARK)
    expect(screen.queryByRole('button', { name: /Cách tính số liệu/ })).not.toBeInTheDocument()
  })
})

describe('ReportAnalyticsPage — "Xem bảng chi tiết" carries the resolved period', () => {
  it('appends year (from date_to) plus date_from/date_to once the period is known', async () => {
    renderPage('/report/test', { ...TEST_CONFIG, sourcePath: '/procurement/test-table' })
    await screen.findByText(KPI_LOADED_MARK)

    const link = await screen.findByRole('link', { name: /Xem bảng chi tiết/ })
    expect(link).toHaveAttribute(
      'href',
      '/procurement/test-table?year=2026&date_from=2026-09-01&date_to=2026-09-28',
    )
  })
})

//  Người dùng chê (28/09/2026): kỳ trống mà trang vẫn vẽ nguyên bảng số 0 kèm
//  "−100%" ở mọi ô, cộng thêm mỗi khối Top tự báo rỗng một câu. Kỳ trống phải
//  ra ĐÚNG MỘT thông báo, hàng thẻ KPI vẫn giữ.
describe('ReportAnalyticsPage — an empty period shows one page-level empty state', () => {
  function emptyFixture(debt: number, preset = 'this_month'): ReportAnalyticsResponse {
    const base = buildFixture('previous')
    return {
      ...base,
      period: { ...base.period, date_from: '2026-09-28', date_to: '2026-09-28', preset },
      meta: {
        ...base.meta,
        metrics: [
          ...base.meta.metrics,
          {
            key: 'debt',
            label: 'Công nợ quá hạn',
            kind: 'money',
            good: 'down',
            helper: false,
            snapshot: true,
          },
        ],
      },
      //  Số dư công nợ (snapshot) vẫn còn — nhưng kỳ này KHÔNG phát sinh gì.
      totals: {
        current: { lines: 0, amount: 0, debt },
        compare: { lines: 100, amount: 400_000_000 },
      },
      groups: [
        {
          key: 'kd',
          label: 'Kinh doanh',
          current: { lines: 0, amount: 0 },
          compare: { lines: 100 },
        },
      ],
    }
  }

  it('replaces chart, Top lists and table with one message, and keeps the KPI cards', async () => {
    vi.mocked(apiGet).mockImplementation(async () => emptyFixture(133_100_000))
    renderPage()
    expect(await screen.findByText('Kỳ này chưa có dữ liệu')).toBeInTheDocument()
    expect(screen.getByText(/Không có phát sinh nào trong 28\/09\/2026\./)).toBeInTheDocument()
    expect(screen.queryAllByRole('row')).toHaveLength(0)
    expect(screen.queryByText('Top nhà cung cấp')).not.toBeInTheDocument()
    expect(screen.getAllByText('Dòng hàng').length).toBeGreaterThan(0)
  })

  it('"Xem cả năm nay" writes preset=this_year in one request', async () => {
    vi.mocked(apiGet).mockImplementation(async () => emptyFixture(0))
    const user = userEvent.setup()
    renderPage()
    await user.click(await screen.findByRole('button', { name: 'Xem cả năm nay' }))
    await waitFor(() => {
      const lastCall = vi.mocked(apiGet).mock.calls.at(-1)
      expect((lastCall?.[1] as { params: Record<string, string> }).params.preset).toBe('this_year')
    })
  })

  it('does not offer "Xem cả năm nay" when the empty period already is this year', async () => {
    vi.mocked(apiGet).mockImplementation(async () => emptyFixture(0, 'this_year'))
    renderPage()
    await screen.findByText('Kỳ này chưa có dữ liệu')
    expect(screen.queryByRole('button', { name: 'Xem cả năm nay' })).not.toBeInTheDocument()
  })
})
