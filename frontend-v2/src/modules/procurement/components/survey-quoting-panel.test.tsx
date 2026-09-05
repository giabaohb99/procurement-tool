import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ListParams } from '@/shared/types/api'
import { SurveyQuotingPanel } from './survey-quoting-panel'
import type { SurveyProgressItem } from '../types/survey-progress-types'

//  Chặn ở tầng HOOK dữ liệu chứ không ở `@/core/api`: panel này phải bắt được BỘ
//  THAM SỐ nó gửi đi (`phase` / `received_date_from` / …), mà tham số đó chỉ hiện
//  nguyên vẹn ở đầu vào của hook.
const listCalls: ListParams[] = []

vi.mock('../hooks/use-purchase-documents', () => ({
  useSurveyProgress: (params: ListParams) => {
    listCalls.push(params)
    return {
      data: { total: rows.length, items: rows, show_supplier: true },
      isLoading: false,
      isError: false,
    }
  },
}))

//  Nút Xuất Excel dựng chuỗi truy vấn RIÊNG, không dùng lại `params` của bảng —
//  nên phải bắt luôn đường dẫn nó gọi.
const downloads: string[] = []
vi.mock('@/core/api/download-file', () => ({
  downloadFile: (url: string) => {
    downloads.push(url)
    return Promise.resolve()
  },
}))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAccess: () => true }),
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
  } as SurveyProgressItem,
]

//  P6-6: panel sống bên trong trang Tiến độ mua hàng gộp — URL thật của nó là
//  `/procurement/purchase-progress?step=quoting&…`.
function build(url = '/procurement/purchase-progress?step=quoting') {
  //  `DataTable` gọi `useQueryClient` cho nút Tải lại — vẫn phải có provider dù
  //  mọi hook dữ liệu của panel này đã bị chặn.
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <SurveyQuotingPanel />
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

describe('SurveyQuotingPanel — bước Đang so giá (P6-6)', () => {
  it('always asks the server for the quoting phase — lines already turned into PR/PO stay out', () => {
    build()

    expect(lastCall().phase).toBe('quoting')
  })

  it('exports through the survey-progress endpoint with the same quoting phase', async () => {
    const user = userEvent.setup()
    build()

    await user.click(screen.getByRole('button', { name: /Xuất Excel/ }))

    expect(downloads[0]).toContain('/api/survey-progress/export/xlsx')
    expect(downloads[0]).toContain('phase=quoting')
  })
})

describe('SurveyQuotingPanel — khoảng ngày', () => {
  it('sends the range as received dates by default — same mốc as the month filter', () => {
    build('/procurement/purchase-progress?step=quoting&date_from=2026-08-01&date_to=2026-08-31')

    expect(lastCall()).toMatchObject({
      received_date_from: '2026-08-01',
      received_date_to: '2026-08-31',
    })
    expect(lastCall().result_due_date_from).toBeUndefined()
    expect(lastCall().result_date_from).toBeUndefined()
  })

  it('switches to the hạn trả KQ dates when the user picks that mốc', () => {
    build(
      '/procurement/purchase-progress?step=quoting&date_field=result_due&date_from=2026-08-01&date_to=2026-08-31',
    )

    expect(lastCall()).toMatchObject({
      result_due_date_from: '2026-08-01',
      result_due_date_to: '2026-08-31',
    })
    expect(lastCall().received_date_from).toBeUndefined()
  })

  it('switches to the ngày trả KQ dates when the user picks that mốc', () => {
    //  Ba mốc của cùng một dòng lệch nhau cả tháng: tiếp nhận 03/08, hạn 10/08,
    //  trả thật 01/09. Hỏi nhầm mốc là ra tập khác hẳn.
    build(
      '/procurement/purchase-progress?step=quoting&date_field=result&date_from=2026-09-01&date_to=2026-09-30',
    )

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
    build('/procurement/purchase-progress?step=quoting&date_field=khong-co&date_from=2026-08-01')

    expect(lastCall().received_date_from).toBe('2026-08-01')
  })

  it('accepts a half-open range — "từ 01/08 tới nay" is a real question', () => {
    build('/procurement/purchase-progress?step=quoting&date_from=2026-08-01')

    expect(lastCall().received_date_from).toBe('2026-08-01')
    expect(lastCall().received_date_to).toBeUndefined()
  })

  it('sends no date param at all when the range is empty', () => {
    //  Chuỗi rỗng gửi lên là backend so `col >= ""` — loại sạch dòng chưa có
    //  ngày, bảng rỗng ngay lúc mở màn.
    build('/procurement/purchase-progress?step=quoting&date_from=&date_to=')

    expect(lastCall().received_date_from).toBeUndefined()
    expect(lastCall().received_date_to).toBeUndefined()
  })

  it('keeps the other filters while a range is active', () => {
    build(
      '/procurement/purchase-progress?step=quoting&state=Đã trả kết quả&late=1&date_from=2026-08-01',
    )

    expect(lastCall()).toMatchObject({
      state: 'Đã trả kết quả',
      late: '1',
      received_date_from: '2026-08-01',
    })
  })

  it('exports the SAME range the table is showing', async () => {
    const user = userEvent.setup()
    build(
      '/procurement/purchase-progress?step=quoting&date_field=result&date_from=2026-09-01&date_to=2026-09-30',
    )

    await user.click(screen.getByRole('button', { name: /Xuất Excel/ }))

    // Xuất ra một tập khác cái đang xem là lỗi ngầm — không ai đối chiếu nổi.
    expect(downloads[0]).toContain('result_date_from=2026-09-01')
    expect(downloads[0]).toContain('result_date_to=2026-09-30')
    expect(downloads[0]).not.toContain('received_date_from')
  })

  it('shows both controls on the toolbar', () => {
    build()

    expect(screen.getByText('Theo ngày tiếp nhận')).toBeInTheDocument()
    expect(screen.getByText('Từ ngày – tới ngày')).toBeInTheDocument()
  })
})

describe('SurveyQuotingPanel — cột chữ đọc đủ', () => {
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
