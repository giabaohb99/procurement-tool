import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useSearchParams } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { SurveyReportPage } from './survey-report-page'
import type { ListParams } from '@/shared/types/api'
import type { SurveyReportLine, SurveyReportResult } from '../types/survey-report'

//  Quyền: ô chọn Nhóm hàng gọi một endpoint có `require("item_group","read")`
//  riêng, nên bài kiểm phải bật/tắt được quyền đó.
let granted: string[] = []

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string) => granted.includes(entity),
    canAccess: () => true,
  }),
}))

//  Chặn ở tầng HOOK: điều cần khẳng định là trang gửi ĐÚNG TÊN tham số lọc
//  xuống backend — chỗ đã từng gửi sai suốt một thời gian dài mà không ai biết.
let result: SurveyReportResult | undefined
const seenParams: ListParams[] = []

vi.mock('../hooks/use-purchase-documents', () => ({
  useSurveyReport: (params: ListParams) => {
    seenParams.push(params)
    return { data: result, isLoading: false, isError: false }
  },
}))

let itemGroups: { items: { id: number; name: string }[] } | undefined

vi.mock('../hooks/use-purchase-request-support', () => ({
  usePurchaseRequestItemGroups: (enabled: boolean) => ({
    data: enabled ? itemGroups : undefined,
  }),
}))

const listSurveyReportLines = vi.fn()

vi.mock('../api/purchase-document-api', () => ({
  purchaseDocumentApi: {
    listSurveyReportLines: (params: ListParams) => listSurveyReportLines(params),
  },
}))

/**
 * Một dòng báo cáo ĐẦY ĐỦ khóa.
 *
 * Backend trả đủ bộ khóa cho cả dòng NCC lẫn dòng SP (loại nào không có thì rỗng
 * hoặc `null`), nên bài kiểm cũng phải dựng đủ — dựng thiếu là kiểm một hình thù
 * dữ liệu không tồn tại ở chạy thật.
 */
function line(over: Partial<SurveyReportLine> = {}): SurveyReportLine {
  return {
    survey_id: 1,
    survey_code: 'KSNCC0001',
    kind: 'supplier',
    line_id: 1,
    content: 'Thùng carton 3 lớp',
    date: '2026-08-12',
    line_approve: 'Đã duyệt',
    line_approve_note: '',
    survey_status: 'approved',

    survey_type: 'combined',
    sr_code: 'YCBG0001',
    pr_code: '',
    item_group: 'Bao bì',
    nspt: 'Nguyễn Văn A',
    item_code: 'XOT0009',
    item_name: 'Thùng carton 3 lớp 40x30x20',
    uom: 'Cái',
    main_content: 'Khảo sát giá bao bì quý 3',
    requirement_detail: '',
    received_date: '2026-08-10',
    result_due_date: '2026-08-20',
    request_qty: 1000,
    proposed_rate: null,

    contact_date: '2026-08-12',
    reply_date: '',
    result_date: '',

    supplier_code: 'NCCKS004',
    supplier_name: 'Công ty Phương Nam',
    tax_code: '1801234567',
    contact_person: 'Trần Thị B',
    contact_phone: '0909123456',
    supply_group: 'Bao bì giấy',
    source_of_information: '',
    production_time: '',
    nvkd_eval: '',
    invoice_policy: '',
    reliability: '',
    delivery_policy: '',
    defect_return: '',

    internal_code: '',
    invoice_name: '',
    spec: '',
    active_ingredient: '',
    origin: '',
    quote_unit: '',
    volume_range: '',
    shipping_policy: '',
    delivery_time: '',
    delivery_place: '',
    sample_ready: '',
    sample_date: '',
    lab_result: '',
    moq: null,
    price_by_volume: null,
    last_purchase_price: null,
    max_purchase_price: null,
    vat: null,
    amount: null,
    shipping_cost: null,
    extra_shipping_cost: null,
    sample_qty: null,

    debt_policy: '',
    nspt_note: '',
    note: '',
    ...over,
  }
}

/**
 * Ghi lại chuỗi tham số của URL sau MỖI lần vẽ.
 *
 * Cần cả URL chứ không chỉ tham số gửi xuống backend: có những tham số thừa
 * không đổi kết quả gọi API nhưng vẫn bám vào đường dẫn người dùng gửi cho nhau.
 */
const seenQueries: string[] = []

function QuerySpy() {
  const [params] = useSearchParams()
  seenQueries.push(params.toString())
  return null
}

function build(url = '/procurement/survey-report') {
  //  `DataTable` gọi `useQueryClient` cho nút Tải lại — vẫn phải có provider dù
  //  mọi hook dữ liệu của màn này đã bị chặn.
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <SurveyReportPage />
        <QuerySpy />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

/** Chuỗi tham số URL của lần vẽ GẦN NHẤT. */
function lastQuery() {
  return seenQueries[seenQueries.length - 1]
}

/**
 * Bấm sắp xếp ở tiêu đề một cột. Lệnh nằm ở cái NHÃN CHỮ bên trong ô — bấm vào
 * `<th>` thì sự kiện đi lên trên, không chạm tới chỗ nhận lệnh nằm bên dưới.
 */
async function clickHeader(name: string) {
  //  Dò theo NHÃN CHỮ khớp trọn vẹn, không dò theo tên trợ năng của cả ô: bảng
  //  nay có cả "Ngày", "Ngày liên hệ", "Ngày công nợ" nên tìm lỏng là trúng ba
  //  cột một lúc, mà tên trợ năng của ô còn dính phần tay kéo giãn cột.
  const headers = await screen.findAllByRole('columnheader')
  const [target] = headers.flatMap((header) => within(header).queryAllByText(name))
  if (!target) throw new Error(`Không thấy tiêu đề cột "${name}"`)
  await userEvent.click(target)
}

/** Tham số của lượt gọi hook GẦN NHẤT — tức bộ lọc đang thực sự có hiệu lực. */
function lastParams() {
  return seenParams[seenParams.length - 1]
}

/**
 * Mở hộp **Bộ lọc** rồi trả về phạm vi tra cứu BÊN TRONG nó.
 *
 * Phải khoanh vùng: "Nhóm hàng" và "Mã hàng" vừa là nhãn trong hộp vừa là tiêu
 * đề cột của bảng, tra ở cấp màn hình thì trúng hai chỗ.
 */
const createObjectURL = vi.fn((_blob: Blob) => 'blob:test')

/** Nội dung tệp CSV vừa tải xuống — lấy từ chính `Blob` đưa cho `createObjectURL`. */
async function exportedCsv() {
  const blob = createObjectURL.mock.calls[0]?.[0]
  if (!blob) throw new Error('Chưa có tệp nào được tải xuống')
  //  Bỏ BOM ở đầu tệp (kèm cho Excel đọc đúng tiếng Việt) trước khi so chuỗi.
  return (await blob.text()).replace(/^\uFEFF/, '')
}

/**
 * Tách tệp CSV thành mảng ô. Hàm xuất bọc NGOẶC KÉP mọi ô nên cắt theo `","` là
 * đủ — không cần bộ phân tích đầy đủ, và cũng chính vì vậy đừng dùng lại chỗ khác.
 */
function splitCsv(csv: string) {
  return csv.split('\n').map((row) => row.replace(/^"|"$/g, '').split('","'))
}

async function openFilterBox() {
  await userEvent.click(await screen.findByRole('button', { name: /Bộ lọc/ }))
  return within(await screen.findByRole('dialog'))
}

beforeEach(() => {
  granted = []
  seenParams.length = 0
  seenQueries.length = 0
  //  Bảng nhớ bố cục cột trong localStorage; không dọn thì bài trước ẩn cột nào
  //  bài sau vẫn ẩn.
  localStorage.clear()
  itemGroups = { items: [{ id: 3, name: 'Bao bì' }] }
  listSurveyReportLines.mockReset()
  result = {
    total: 1,
    items: [line()],
    summary: { 'Chờ duyệt': 2, 'Đã duyệt': 5117, 'Không duyệt': 79, 'Thiếu thông tin': 0 },
  }
})

describe('SurveyReportPage — tên tham số gửi xuống backend', () => {
  it('sends the date range as date_from / date_to', async () => {
    //  Lỗi đã phải vá: trang từng gửi `from_date` / `to_date`. FastAPI lặng lẽ
    //  bỏ qua tham số lạ nên lọc theo ngày KHÔNG chạy mà cũng chẳng báo lỗi gì.
    //  Đừng đổi hai tên này nếu không sửa luôn `survey/controller.py`.
    build('/procurement/survey-report?date_from=2026-08-01&date_to=2026-08-31')

    await waitFor(() => {
      expect(lastParams()).toMatchObject({ date_from: '2026-08-01', date_to: '2026-08-31' })
    })
    expect(lastParams()).not.toHaveProperty('from_date')
    expect(lastParams()).not.toHaveProperty('to_date')
  })

  it('passes every extra filter through, including main_content', async () => {
    build(
      '/procurement/survey-report?item_group=Bao%20b%C3%AC&supplier=NCCKS004' +
        '&item_code=XOT0009&nspt=Nguy%E1%BB%85n&main_content=qu%C3%BD%203',
    )

    await waitFor(() => {
      expect(lastParams()).toMatchObject({
        item_group: 'Bao bì',
        supplier: 'NCCKS004',
        item_code: 'XOT0009',
        nspt: 'Nguyễn',
        main_content: 'quý 3',
      })
    })
  })

  it('omits a filter that is present but empty in the URL', async () => {
    //  `?supplier=` là chuỗi rỗng, không phải "lọc theo NCC rỗng".
    build('/procurement/survey-report?supplier=&item_code=')

    await waitFor(() => expect(lastParams()).toBeDefined())
    expect(lastParams()).not.toHaveProperty('supplier')
    expect(lastParams()).not.toHaveProperty('item_code')
  })

  it('leaves sorting out entirely until a column is picked', async () => {
    build()

    await waitFor(() => expect(lastParams()).toBeDefined())
    expect(lastParams()).not.toHaveProperty('sort_by')
    expect(lastParams()).not.toHaveProperty('sort_dir')
  })

  it('defaults the direction to asc when the URL carries a column but no direction', async () => {
    build('/procurement/survey-report?sort_by=date')

    await waitFor(() => {
      expect(lastParams()).toMatchObject({ sort_by: 'date', sort_dir: 'asc' })
    })
  })
})

describe('SurveyReportPage — dải chip kết quả duyệt', () => {
  it('adds the four counts up for the "Tất cả" chip', async () => {
    build()

    const chip = await screen.findByRole('button', { name: /Tất cả/ })
    //  2 + 5117 + 79 + 0. Định dạng theo tiếng Việt nên dấu chấm ngăn nghìn.
    expect(within(chip).getByText('5.198')).toBeInTheDocument()
  })

  it('shows a zero count instead of hiding the status', async () => {
    //  "Thiếu thông tin: 0" vẫn phải hiện — biến mất thì người đọc tưởng hệ
    //  thống không có trạng thái đó.
    build()

    const chip = await screen.findByRole('button', { name: /Thiếu thông tin/ })
    expect(within(chip).getByText('0')).toBeInTheDocument()
  })

  it('filters by a status when its chip is clicked', async () => {
    build()

    await userEvent.click(await screen.findByRole('button', { name: /Không duyệt/ }))

    await waitFor(() => expect(lastParams()).toMatchObject({ line_approve: 'Không duyệt' }))
  })

  it('clears the filter when the active chip is clicked again', async () => {
    build('/procurement/survey-report?line_approve=%C4%90%C3%A3%20duy%E1%BB%87t')

    const chip = await screen.findByRole('button', { name: /Đã duyệt/ })
    expect(chip).toHaveAttribute('aria-pressed', 'true')

    await userEvent.click(chip)

    await waitFor(() => expect(lastParams()).not.toHaveProperty('line_approve'))
  })

  it('keeps every count visible while one status is active', async () => {
    //  Backend cố tình tính `summary` TRƯỚC khi lọc trạng thái. Nếu có ngày nào
    //  đó tính sau, dải chip sẽ chỉ còn một số khác 0 và mất hết tác dụng.
    build('/procurement/survey-report?line_approve=%C4%90%C3%A3%20duy%E1%BB%87t')

    expect(
      within(await screen.findByRole('button', { name: /Không duyệt/ })).getByText('79'),
    ).toBeInTheDocument()
  })

  it('renders no chip strip at all when the backend sent no summary', async () => {
    result = { total: 0, items: [], summary: undefined as unknown as SurveyReportResult['summary'] }
    build()

    expect(screen.queryByRole('button', { name: /Tất cả/ })).not.toBeInTheDocument()
    expect(screen.getByText('Không tìm thấy dòng khảo sát nào.')).toBeInTheDocument()
  })
})

describe('SurveyReportPage — cột mã phiếu', () => {
  it('prints the survey code the same way on every line of one survey', async () => {
    //  Bản trước làm mờ dòng nối tiếp của cùng một phiếu và gắn nhãn đếm
    //  "N dòng". Khách nhìn vào không đoán được nghĩa nên đã yêu cầu bỏ hẳn:
    //  dòng nào cũng in mã phiếu y hệt nhau.
    result = {
      total: 3,
      items: [
        line({ line_id: 1 }),
        line({ line_id: 2 }),
        line({ survey_id: 2, survey_code: 'KSNCC0002', line_id: 3 }),
      ],
      summary: { 'Chờ duyệt': 0, 'Đã duyệt': 3, 'Không duyệt': 0, 'Thiếu thông tin': 0 },
    }
    build()

    const links = await screen.findAllByRole('link', { name: 'KSNCC0001' })
    expect(links).toHaveLength(2)
    const [first, second] = links
    expect(first.className).toBe(second.className)
    expect(screen.queryByText('2 dòng')).not.toBeInTheDocument()
    expect(screen.queryByText('1 dòng')).not.toBeInTheDocument()
  })

  it('links every line to its own survey', async () => {
    result = {
      total: 2,
      items: [line({ line_id: 1 }), line({ survey_id: 7, survey_code: 'KSNCC0007', line_id: 2 })],
      summary: { 'Chờ duyệt': 0, 'Đã duyệt': 2, 'Không duyệt': 0, 'Thiếu thông tin': 0 },
    }
    build()

    expect(await screen.findByRole('link', { name: 'KSNCC0001' })).toHaveAttribute(
      'href',
      '/procurement/surveys/1',
    )
    expect(screen.getByRole('link', { name: 'KSNCC0007' })).toHaveAttribute(
      'href',
      '/procurement/surveys/7',
    )
  })
})

describe('SurveyReportPage — ba nhịp sắp xếp', () => {
  it('sorts ascending on the first click of a column header', async () => {
    build()
    await clickHeader('Ngày')

    await waitFor(() => expect(lastParams()).toMatchObject({ sort_by: 'date', sort_dir: 'asc' }))
  })

  it('flips to descending on the second click', async () => {
    build()
    await clickHeader('Ngày')
    await clickHeader('Ngày')

    await waitFor(() => expect(lastParams()).toMatchObject({ sort_by: 'date', sort_dir: 'desc' }))
  })

  it('gives a way back: the third click stops sorting altogether', async () => {
    //  Khách hỏi đúng chỗ này: bản cũ chỉ đảo qua lại tăng/giảm nên bấm nhầm một
    //  phát là kẹt, muốn về thứ tự gốc chỉ còn cách tải lại trang.
    build()
    await clickHeader('Ngày')
    await clickHeader('Ngày')
    await clickHeader('Ngày')

    await waitFor(() => expect(lastParams()).not.toHaveProperty('sort_by'))
    expect(lastParams()).not.toHaveProperty('sort_dir')
  })

  it('leaves no orphan sort_dir behind in the URL after stopping', async () => {
    //  Xóa mỗi `sort_by` thì đường dẫn còn dính `?sort_dir=asc` chẳng của cột nào
    //  — gửi cho nhau đọc như đang sắp xếp dở.
    build()
    await clickHeader('Ngày')
    await clickHeader('Ngày')
    await clickHeader('Ngày')

    await waitFor(() => expect(lastQuery()).not.toContain('sort_by'))
    expect(lastQuery()).not.toContain('sort_dir')
  })

  it('restarts at ascending when a different column is picked', async () => {
    build('/procurement/survey-report?sort_by=date&sort_dir=desc')
    await clickHeader('NSPT')

    await waitFor(() => expect(lastParams()).toMatchObject({ sort_by: 'nspt', sort_dir: 'asc' }))
  })
})

describe('SurveyReportPage — hộp bộ lọc phụ', () => {
  it('counts the active extra filters on the trigger', async () => {
    build('/procurement/survey-report?supplier=NCCKS004&nspt=Nguy%E1%BB%85n')

    const trigger = await screen.findByRole('button', { name: /Bộ lọc/ })
    expect(within(trigger).getByText('2')).toBeInTheDocument()
  })

  it('does not count the date range as an extra filter', async () => {
    //  Khoảng ngày có ô riêng ngoài thanh công cụ; đếm vào đây thì con số trên
    //  nút không khớp với số ô đang có chữ bên trong.
    build('/procurement/survey-report?date_from=2026-08-01&date_to=2026-08-31')

    const trigger = await screen.findByRole('button', { name: /Bộ lọc/ })
    expect(within(trigger).queryByText('2')).not.toBeInTheDocument()
  })

  it('applies the drafted text only when Áp dụng is pressed', async () => {
    build()
    const box = await openFilterBox()
    await userEvent.type(box.getByLabelText('Mã hàng'), 'XOT')

    //  Gõ tới đâu bắn API tới đó là mỗi ký tự một lượt quét cả nghìn dòng.
    expect(lastParams()).not.toHaveProperty('item_code')

    await userEvent.click(box.getByRole('button', { name: 'Áp dụng' }))

    await waitFor(() => expect(lastParams()).toMatchObject({ item_code: 'XOT' }))
  })

  it('wipes every extra filter with Xóa lọc but keeps the date range', async () => {
    build('/procurement/survey-report?supplier=NCCKS004&nspt=Nguy%E1%BB%85n&date_from=2026-08-01')
    const box = await openFilterBox()
    await userEvent.click(box.getByRole('button', { name: /Xóa lọc/ }))

    await waitFor(() => expect(lastParams()).not.toHaveProperty('supplier'))
    expect(lastParams()).not.toHaveProperty('nspt')
    expect(lastParams()).toMatchObject({ date_from: '2026-08-01' })
  })

  it('hides the item-group select from a user without item_group.read', async () => {
    granted = []
    build()
    const box = await openFilterBox()

    expect(box.getByLabelText('Mã hàng')).toBeInTheDocument()
    expect(box.queryByText('Nhóm hàng')).not.toBeInTheDocument()
  })

  it('shows the item-group select to a user who holds the permission', async () => {
    granted = ['item_group']
    build()
    const box = await openFilterBox()

    expect(box.getByText('Nhóm hàng')).toBeInTheDocument()
  })
})

describe('SurveyReportPage — bộ cột đầy đủ', () => {
  it('brings the survey header fields down onto every line', async () => {
    //  Khách kêu "ít cột quá, thiếu thông tin nhiều": báo cáo chỉ trả 14 trường
    //  trong khi phiếu + hai bảng dòng có gần 70. Tên VTBB, ĐVT, SL dự kiến là
    //  ba cột nằm ngay trên đầu phiếu mà bảng không hề bày ra.
    result = { ...result!, items: [line({ item_name: 'Thùng carton 3 lớp 40x30x20', uom: 'Cái' })] }
    build()

    const headers = await screen.findAllByRole('columnheader')
    expect(headers.flatMap((header) => within(header).queryAllByText('Tên VTBB'))).toHaveLength(1)
    expect(screen.getByText('Thùng carton 3 lớp 40x30x20')).toBeInTheDocument()
    expect(screen.getByText('Cái')).toBeInTheDocument()
  })

  it('formats the money of a product line instead of dumping the raw number', async () => {
    result = {
      ...result!,
      items: [
        line({
          kind: 'product',
          content: 'Thùng carton 3 lớp',
          price_by_volume: 12345.6789,
          vat: 8,
          amount: 13333333,
          request_qty: 250,
        }),
      ],
    }
    build()

    //  Đơn giá giữ 4 số lẻ, thành tiền làm tròn tới đồng — hai thang khác nhau,
    //  đổ chung một hàm định dạng là lẻ đồng rò ra cột danh sách.
    expect(await screen.findByText('12.345,6789')).toBeInTheDocument()
    expect(screen.getByText('13.333.333')).toBeInTheDocument()
    expect(screen.getByText('8%')).toBeInTheDocument()
    expect(screen.getByText('250')).toBeInTheDocument()
  })
})

describe('SurveyReportPage — xuất CSV', () => {
  beforeEach(() => {
    //  jsdom không có hai hàm này; chỉ cần chúng tồn tại để nhánh tải xuống chạy.
    URL.createObjectURL = createObjectURL
    URL.revokeObjectURL = vi.fn()
    createObjectURL.mockClear()
  })

  it('writes every column into the file, blank where the other kind has no such field', async () => {
    //  Bản trước khai cột hai chỗ tách rời (bảng một danh sách, hàm xuất một
    //  danh sách chép tay) nên thêm cột mà quên tệp xuất chỉ là chuyện sớm muộn.
    result = { ...result!, total: 2 }
    listSurveyReportLines.mockResolvedValue({
      total: 2,
      items: [line(), line({ kind: 'product', line_id: 2, price_by_volume: 12345.6789 })],
      summary: {},
    })
    build()

    await userEvent.click(await screen.findByRole('button', { name: /Xuất CSV/ }))
    await waitFor(() => expect(createObjectURL).toHaveBeenCalledTimes(1))

    const [header, supplierRow, productRow] = splitCsv(await exportedCsv())
    //  Mọi dòng phải có ĐÚNG số ô của hàng tiêu đề, kể cả dòng NCC không có cột
    //  giá nào: lệch một ô là cả tệp lệch cột từ đó trở đi.
    expect(supplierRow).toHaveLength(header.length)
    expect(productRow).toHaveLength(header.length)

    const price = header.indexOf('Đơn giá')
    expect(price).toBeGreaterThan(-1)
    //  Dòng NCC không có khái niệm đơn giá -> để TRẮNG. In `0` là dựng một bức
    //  tường số không đọc được, lại còn lẫn với giá 0 thật.
    expect(supplierRow[price]).toBe('')
    expect(productRow[price]).toBe('12.345,6789')
    expect(supplierRow[header.indexOf('Mã số thuế')]).toBe('1801234567')
  })

  it('fetches the whole filtered set instead of the page on screen', async () => {
    //  Lỗi đã phải vá: bản cũ dựng CSV từ đúng trang đang xem, nên bấm Xuất trên
    //  báo cáo 5.198 dòng chỉ ra một tệp 20 dòng mà không cảnh báo gì.
    result = { ...result!, total: 5198 }
    listSurveyReportLines.mockResolvedValue({ total: 5198, items: [line()], summary: {} })
    build('/procurement/survey-report?supplier=NCCKS004')

    await userEvent.click(await screen.findByRole('button', { name: /Xuất CSV/ }))

    await waitFor(() => expect(listSurveyReportLines).toHaveBeenCalledTimes(1))
    expect(listSurveyReportLines).toHaveBeenCalledWith(
      expect.objectContaining({ supplier: 'NCCKS004', page: 1, page_size: 5198 }),
    )
  })

  it('disables the button when there is nothing to export', async () => {
    result = { total: 0, items: [], summary: result!.summary }
    build()

    expect(await screen.findByRole('button', { name: /Xuất CSV/ })).toBeDisabled()
    expect(listSurveyReportLines).not.toHaveBeenCalled()
  })
})
