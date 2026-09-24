import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { ListParams } from '@/shared/types/api'
import { SurveyProgressPage } from './survey-progress-page'
import type { SurveyProgressItem } from '../types/survey-progress-types'

//  Chặn ở tầng HOOK dữ liệu chứ không ở `@/core/api`: màn này phải bắt được BỘ
//  THAM SỐ nó gửi đi (`received_date_from` / `result_due_date_from` / …), mà
//  tham số đó chỉ hiện nguyên vẹn ở đầu vào của hook.
const listCalls: ListParams[] = []

vi.mock('../hooks/use-purchase-documents', () => ({
  useSurveyProgress: (params: ListParams) => {
    listCalls.push(params)
    return { data: { total: rows.length, items: rows, show_supplier: true }, isLoading: false, isError: false }
  },
}))

//  Nút Xuất Excel nhận bộ lọc qua ĐỐI SỐ THỨ BA của `downloadFile`, nên phải bắt
//  cả ba: trước bao-CR-447 nó tự dựng chuỗi truy vấn riêng và bỏ quên bộ lọc điều
//  kiện, xuất ra một tập khác cái đang xem.
const downloads: { url: string; params?: ListParams }[] = []
vi.mock('@/core/api/download-file', () => ({
  downloadFile: (url: string, _filename: string, params?: ListParams) => {
    downloads.push({ url, params })
    return Promise.resolve()
  },
}))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAccess: () => true }),
}))

//  Ô Công ty đọc danh mục pháp nhân của phân hệ Nhân sự — chặn luôn để test không
//  chạm mạng.
vi.mock('@/modules/hr/hooks/use-companies', () => ({
  useCompanies: () => ({
    data: {
      total: 2,
      items: [
        { id: 7, name: 'Công ty Dego Cần Thơ' },
        { id: 9, name: 'Công ty Dego Hà Nội' },
      ],
    },
  }),
}))

const rows: SurveyProgressItem[] = [
  {
    sr_id: 1,
    code: 'YCBG-0001',
    company_id: 7,
    received_date: '2026-08-03',
    result_due_date: '2026-08-10',
    result_date: '2026-09-01',
    item_group: 'Bao bì',
    progress_state: 'Đã trả kết quả',
    requirement_detail: 'Thùng carton 5 lớp, in 4 màu, kích thước 400x300x250mm, chịu tải 20kg',
    opt_supplier_name: 'Công ty TNHH Thương mại Dịch vụ Xuất nhập khẩu Phương Nam',
    opt_product_name: 'Thùng carton 5 lớp in offset',
    //  Giá của phương án đã chốt — ở khổ hẹp nó đi cùng tên NCC thành MỘT mẩu
    //  chữ, nên phải khác 0 thì mới kiểm được cả cụm.
    opt_price: 9200,
  } as SurveyProgressItem,
]

function build(url = '/procurement/survey-progress') {
  //  `DataTable` gọi `useQueryClient` cho nút Tải lại — vẫn phải có provider dù
  //  mọi hook dữ liệu của màn này đã bị chặn.
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <SurveyProgressPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function lastCall() {
  return listCalls[listCalls.length - 1]
}

beforeEach(() => {
  listCalls.length = 0
  downloads.length = 0
  localStorage.clear()
})

describe('SurveyProgressPage — khoảng ngày', () => {
  it('sends the range as received dates by default — same mốc as the month filter', () => {
    build('/procurement/survey-progress?date_from=2026-08-01&date_to=2026-08-31')

    expect(lastCall()).toMatchObject({
      received_date_from: '2026-08-01',
      received_date_to: '2026-08-31',
    })
    expect(lastCall().result_due_date_from).toBeUndefined()
    expect(lastCall().result_date_from).toBeUndefined()
  })

  it('switches to the hạn trả KQ dates when the user picks that mốc', () => {
    build('/procurement/survey-progress?date_field=result_due&date_from=2026-08-01&date_to=2026-08-31')

    expect(lastCall()).toMatchObject({
      result_due_date_from: '2026-08-01',
      result_due_date_to: '2026-08-31',
    })
    expect(lastCall().received_date_from).toBeUndefined()
  })

  it('switches to the ngày trả KQ dates when the user picks that mốc', () => {
    //  Ba mốc của cùng một dòng lệch nhau cả tháng: tiếp nhận 03/08, hạn 10/08,
    //  trả thật 01/09. Hỏi nhầm mốc là ra tập khác hẳn.
    build('/procurement/survey-progress?date_field=result&date_from=2026-09-01&date_to=2026-09-30')

    expect(lastCall()).toMatchObject({
      result_date_from: '2026-09-01',
      result_date_to: '2026-09-30',
    })
    expect(lastCall().received_date_from).toBeUndefined()
    expect(lastCall().result_due_date_from).toBeUndefined()
  })

  it('falls back to the first mốc when the URL names one that does not exist', () => {
    //  Đường dẫn cũ ai đó lưu lại, hoặc gõ tay sai. Không được ném lỗi, cũng
    //  không được lặng lẽ bỏ luôn khoảng ngày.
    build('/procurement/survey-progress?date_field=khong-co&date_from=2026-08-01')

    expect(lastCall().received_date_from).toBe('2026-08-01')
  })

  it('accepts a half-open range — "từ 01/08 tới nay" is a real question', () => {
    build('/procurement/survey-progress?date_from=2026-08-01')

    expect(lastCall().received_date_from).toBe('2026-08-01')
    expect(lastCall().received_date_to).toBeUndefined()
  })

  it('sends no date param at all when the range is empty', () => {
    //  Chuỗi rỗng gửi lên là backend so `col >= ""` — loại sạch dòng chưa có
    //  ngày, bảng rỗng ngay lúc mở màn.
    build('/procurement/survey-progress?date_from=&date_to=')

    expect(lastCall().received_date_from).toBeUndefined()
    expect(lastCall().received_date_to).toBeUndefined()
  })

  it('keeps the other filters while a range is active', () => {
    build('/procurement/survey-progress?state=Đã trả kết quả&late=1&date_from=2026-08-01')

    expect(lastCall()).toMatchObject({
      state: 'Đã trả kết quả',
      late: '1',
      received_date_from: '2026-08-01',
    })
  })

  it('joins several picked progress labels into one comma-joined param', () => {
    //  bao-CR-423: chọn nhiều nhãn trong cùng ô Tiến độ dòng = HOẶC. Nhãn không
    //  chứa dấu phẩy nên backend tách lại đúng.
    build('/procurement/survey-progress?state=Đã trả kết quả,Trễ hạn')

    expect(lastCall().state).toBe('Đã trả kết quả,Trễ hạn')
  })

  it('sends no state param when nothing is picked', () => {
    build('/procurement/survey-progress?state=')

    expect(lastCall().state).toBeUndefined()
  })

  it('exports the SAME range the table is showing', async () => {
    const user = userEvent.setup()
    build('/procurement/survey-progress?date_field=result&date_from=2026-09-01&date_to=2026-09-30')

    await user.click(screen.getByRole('button', { name: /Xuất Excel/ }))

    // Xuất ra một tập khác cái đang xem là lỗi ngầm — không ai đối chiếu nổi.
    expect(downloads[0].params).toMatchObject({
      result_date_from: '2026-09-01',
      result_date_to: '2026-09-30',
    })
    expect(downloads[0].params?.received_date_from).toBeUndefined()
  })

  it('shows both controls on the toolbar', () => {
    build()

    expect(screen.getByText('Theo ngày tiếp nhận')).toBeInTheDocument()
    expect(screen.getByText('Từ ngày – tới ngày')).toBeInTheDocument()
  })
})

/**
 * bao-CR-447 — ô CÔNG TY.
 *
 * Màn này từng không lọc được theo pháp nhân bằng đường nào cả: thanh công cụ
 * không có ô, còn ô Công ty trong *Bộ lọc điều kiện* gửi `company_id__is=` xuống
 * một whitelist cố tình KHÔNG có `company_id` (`_cond_map` gỡ nó ra) nên bị bỏ
 * LẶNG — chọn công ty, bấm Áp dụng, bảng vẫn nguyên cả tập.
 */
describe('SurveyProgressPage — ô Công ty', () => {
  it('bày ô Công ty trên thanh công cụ', () => {
    build()

    //  Hai bản: thanh công cụ khổ rộng + tờ lọc nhanh khổ hẹp.
    expect(screen.getAllByLabelText('Lọc theo công ty').length).toBeGreaterThan(0)
  })

  it('sends company_id as a comma-joined list — nhiều pháp nhân là HOẶC', () => {
    build('/procurement/survey-progress?company_id=7,9')

    expect(lastCall().company_id).toBe('7,9')
  })

  it('sends company_id even for a single pick', () => {
    build('/procurement/survey-progress?company_id=7')

    expect(lastCall().company_id).toBe('7')
  })

  it('sends no company_id when nothing is picked', () => {
    //  Gửi `company_id=""` xuống là backend so `== ""` rồi trả bảng rỗng.
    build('/procurement/survey-progress?company_id=')

    expect(lastCall().company_id).toBeUndefined()
  })

  it('exports the SAME companies the table is showing', async () => {
    const user = userEvent.setup()
    build('/procurement/survey-progress?company_id=7,9')

    await user.click(screen.getByRole('button', { name: /Xuất Excel/ }))

    expect(downloads[0].params).toMatchObject({ company_id: '7,9' })
  })
})

describe('SurveyProgressPage — Xuất Excel bám bộ lọc điều kiện', () => {
  it('carries the conditional filter into the export', async () => {
    //  Lỗi cũ: nút xuất tự dựng query string từ mấy ô lọc nhanh và BỎ QUÊN
    //  `queryParams` của bộ lọc điều kiện — đang lọc "Mục đích chứa …" mà bấm
    //  xuất thì ra cả bảng, người nhận tệp không có cách nào biết.
    const user = userEvent.setup()
    build('/procurement/survey-progress?purpose__contains=thùng carton')

    expect(lastCall().purpose__contains).toBe('thùng carton')

    await user.click(screen.getByRole('button', { name: /Xuất Excel/ }))

    expect(downloads[0].params).toMatchObject({ purpose__contains: 'thùng carton' })
  })

  it('never sends the paging params down the export', async () => {
    //  Tệp xuất phải là CẢ tập đang lọc, không phải trang đang xem.
    const user = userEvent.setup()
    build('/procurement/survey-progress?late=1')

    await user.click(screen.getByRole('button', { name: /Xuất Excel/ }))

    expect(downloads[0].params).toMatchObject({ late: '1' })
    expect(downloads[0].params?.page).toBeUndefined()
    expect(downloads[0].params?.page_size).toBeUndefined()
  })
})

describe('SurveyProgressPage — cột chữ đọc đủ', () => {
  //  Khách nêu 31/08/2026: "cho show full ra chứ đừng có …". Xuống dòng là hiệu
  //  ứng CSS, jsdom không đo được, nên đành khẳng định theo class — đây là chỗ
  //  DUY NHẤT trong bộ test này làm vậy, vì class CHÍNH LÀ hành vi.
  //
  //  Bắt hai lối hỏng cùng lúc: bỏ `wrap` ở cột (lớp bọc quay về `truncate`),
  //  và gắn lại `truncate` trong `cell` (class ô con thắng lớp bọc của bảng,
  //  `wrap` thành vô hiệu mà nhìn code vẫn tưởng đang bật).
  function cellOf(text: string) {
    const cell = screen.getByText(text).closest('td')
    if (!cell) throw new Error(`Không tìm thấy ô chứa "${text}"`)
    return cell
  }

  it('lets the long text columns wrap instead of cutting them with "…"', () => {
    build()

    const texts = [
      'YCBG-0001',
      'Thùng carton 5 lớp, in 4 màu, kích thước 400x300x250mm, chịu tải 20kg',
      'Công ty TNHH Thương mại Dịch vụ Xuất nhập khẩu Phương Nam',
      'Thùng carton 5 lớp in offset',
    ]
    for (const text of texts) {
      expect(cellOf(text).querySelector('.truncate')).toBeNull()
      expect(cellOf(text).querySelector('.whitespace-normal')).not.toBeNull()
    }
  })

  it('keeps the number and date columns on one line so the rows stay even', () => {
    build()

    // Cột ngày để nguyên `truncate`: cho xuống dòng thì hàng cao lệch nhau mà
    // chẳng đọc thêm được chữ nào.
    expect(cellOf('03/08/2026').querySelector('.truncate')).not.toBeNull()
  })
})

/**
 * Khổ điện thoại — bảng đổi sang THẺ, xem `SurveyProgressCard`.
 *
 * Bảng khai 45 cột, bề rộng tự nhiên ~5800px trong khung ~322px: phần nhìn thấy
 * được là *Mã YCBG* cộng một mẩu *Công ty*, còn tiến độ dòng, số ngày trễ và giá
 * đã chốt — cả ba lý do người ta mở màn này — đều nằm ngoài mép phải.
 *
 * `setup.ts` cố định `matchMedia` ở khổ desktop cho cả bộ test, nên khổ hẹp phải
 * nói rõ ra ngay tại đây.
 */
describe('SurveyProgressPage — khổ điện thoại', () => {
  beforeEach(() => {
    vi.stubGlobal('matchMedia', (query: string) => ({
      matches: true,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))
  })
  afterEach(() => vi.unstubAllGlobals())

  it('bày TIẾN ĐỘ và GIÁ ĐÃ CHỐT — hai cột nằm ngoài mép phải của bảng', () => {
    build()

    expect(screen.getByText('Đã trả kết quả')).toBeInTheDocument()
    //  NCC và đơn giá đứng cùng một mẩu chữ nên khẳng định theo cả cụm.
    expect(
      screen.getByText(/Công ty TNHH Thương mại Dịch vụ Xuất nhập khẩu Phương Nam — /),
    ).toBeInTheDocument()
  })

  it('KHÔNG còn bảng nào — thẻ thay hẳn chứ không nằm cạnh', () => {
    const { container } = build()

    expect(container.querySelector('table')).toBeNull()
  })

  it('cả thẻ là một nút mở YCBG — ở chế độ thẻ mã YCBG không còn là liên kết', () => {
    build()

    //  Không có nhịp này thì từ một dòng tiến độ KHÔNG có đường nào về chứng từ
    //  gốc: cột *Mã YCBG* là `<Link>`, mà cột thì không còn.
    const card = screen.getByRole('button', { name: /Thùng carton 5 lớp, in 4 màu/ })
    expect(card).toBeInTheDocument()
  })

  it('dùng câu gợi ý tìm kiếm RÚT GỌN — bản đầy đủ bị xén mất phần đuôi', () => {
    build()

    //  Chỉ HAI vế: ô tìm ở khổ hẹp chỉ còn ~134px sau khi chia hàng với nút
    //  *Bộ lọc* và *Tải lại*, ba vế (~139px) vẫn bị xén — xem ghi chú ở trang.
    expect(screen.getByPlaceholderText('Tìm YCBG, SP…')).toBeInTheDocument()
  })
})
