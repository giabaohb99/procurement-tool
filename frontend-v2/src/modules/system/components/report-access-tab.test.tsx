import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { useReportAccessList } from '../hooks/use-report-access'
import type { ReportAccessGrant, ReportAccessItem } from '../types/report-access'
import { ReportAccessTab } from './report-access-tab'

//  `DataTable` tự đọc `useQueryClient` (nút Tải lại) — thiếu provider là nổ
//  ngay khi dựng, không liên quan gì tới logic của bài kiểm.
function renderTab(canWrite: boolean) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const utils = render(
    <QueryClientProvider client={queryClient}>
      <ReportAccessTab canWrite={canWrite} />
    </QueryClientProvider>,
  )
  //  Bọc lại `rerender` để bài kiểm render lại với CÙNG `queryClient` mà
  //  không phải tự chép khung `QueryClientProvider` ở từng nơi gọi.
  return {
    ...utils,
    rerenderWithCanWrite: (nextCanWrite: boolean) =>
      utils.rerender(
        <QueryClientProvider client={queryClient}>
          <ReportAccessTab canWrite={nextCanWrite} />
        </QueryClientProvider>,
      ),
  }
}

vi.mock('../hooks/use-report-access', () => ({ useReportAccessList: vi.fn() }))

//  Hộp thoại kéo theo `useAccessSubjectOptions` (bốn hook của `hr`) — mock
//  thẳng để bài kiểm của TAB không dính theo một thay đổi của hộp thoại.
//  Mock in ra cả số chủ thể đang gán — M1 cần phân biệt được object CÙ của
//  dòng cũ (bắt được tại lượt click) với object MỚI đọc lại từ `data` sau khi
//  tải lại danh sách.
vi.mock('./report-access-dialog', () => ({
  ReportAccessDialog: ({ report }: { report: ReportAccessItem | null }) =>
    report ? (
      <div data-testid="dialog-open">
        {report.label} — {report.grants.length} chủ thể
      </div>
    ) : null,
}))

function grant(overrides: Partial<ReportAccessGrant> = {}): ReportAccessGrant {
  return {
    id: 1,
    subject_kind: 1,
    subject_kind_label: 'Người',
    subject_id: 1,
    subject_name: 'Người A',
    effect: 1,
    reason: '',
    valid_from: null,
    valid_to: null,
    created_at: '2026-10-02T00:00:00Z',
    ...overrides,
  }
}

function item(overrides: Partial<ReportAccessItem> = {}): ReportAccessItem {
  return {
    key: 1,
    label: 'Báo cáo mua hàng',
    group: 'Thu mua',
    grants: [],
    ...overrides,
  }
}

function mockList(
  data: ReportAccessItem[] | undefined,
  extra: { isLoading?: boolean; isError?: boolean } = {},
) {
  vi.mocked(useReportAccessList).mockReturnValue({
    data,
    isLoading: false,
    isError: false,
    ...extra,
  } as unknown as ReturnType<typeof useReportAccessList>)
}

describe('ReportAccessTab', () => {
  it('báo cáo chưa gán CHO PHÉP nào thì nói rõ phạm vi phân hệ Báo cáo, không phải một ô trống im lặng', () => {
    mockList([item({ grants: [] })])
    renderTab(true)
    //  H1: câu phải nói rõ phạm vi là PHÂN HỆ BÁO CÁO — tránh hiểu lầm là
    //  khóa luôn cả màn bảng gốc ở phân hệ khác (vd Báo cáo mua hàng).
    expect(
      screen.getByText('Chưa gán — không ai xem được trong phân hệ Báo cáo'),
    ).toBeInTheDocument()
  })

  it('tách chủ thể CHO PHÉP khỏi chủ thể bị CẤM trên hai cột khác nhau', () => {
    mockList([
      item({
        grants: [
          grant({ id: 1, subject_name: 'Người Cho Phép', effect: 1 }),
          grant({ id: 2, subject_name: 'Người Bị Cấm', effect: 2 }),
        ],
      }),
    ])
    renderTab(true)

    expect(screen.getByText('Người Cho Phép')).toBeInTheDocument()
    expect(screen.getByText('Người Bị Cấm')).toBeInTheDocument()
    //  Có ít nhất một CHO PHÉP rồi thì câu "chưa gán" không còn đúng.
    expect(
      screen.queryByText('Chưa gán — không ai xem được trong phân hệ Báo cáo'),
    ).not.toBeInTheDocument()
  })

  it('tiêu đề tab nói rõ quyền ở đây chỉ gác trang báo cáo, không khóa màn bảng gốc của phân hệ', () => {
    mockList([item()])
    renderTab(true)
    expect(
      screen.getByText(/Quyền ở đây chỉ quyết định ai xem được trang báo cáo/),
    ).toBeInTheDocument()
  })

  it('không có role.write thì KHÔNG hiện nút Sửa — không chỉ khóa, mà ẩn hẳn', () => {
    mockList([item()])
    renderTab(false)
    expect(screen.queryByRole('button', { name: /Sửa quyền xem/ })).not.toBeInTheDocument()
  })

  it('có role.write thì bấm nút Sửa mở đúng báo cáo của dòng đó', async () => {
    const user = userEvent.setup()
    mockList([
      item({ key: 1, label: 'Báo cáo mua hàng' }),
      item({ key: 5, label: 'Báo cáo khảo sát' }),
    ])
    renderTab(true)

    await user.click(screen.getByRole('button', { name: 'Sửa quyền xem «Báo cáo khảo sát»' }))

    expect(screen.getByTestId('dialog-open')).toHaveTextContent('Báo cáo khảo sát')
  })

  it(
    'sau khi gán/thu hồi thành công và `data` nạp lại, hộp thoại hiện danh sách MỚI ' +
      '— không giữ object của DÒNG CŨ bắt tại lúc bấm Sửa (M1)',
    async () => {
      const user = userEvent.setup()
      mockList([item({ key: 1, label: 'Báo cáo mua hàng', grants: [grant({ id: 1 })] })])

      const { rerenderWithCanWrite } = renderTab(true)

      await user.click(screen.getByRole('button', { name: 'Sửa quyền xem «Báo cáo mua hàng»' }))
      expect(screen.getByTestId('dialog-open')).toHaveTextContent('1 chủ thể')

      //  Giả lập gán/thu hồi THÀNH CÔNG rồi `useReportAccessList` nạp lại: dòng
      //  CÙNG `key` giờ là một OBJECT MỚI với danh sách chủ thể khác — không
      //  phải object cũ bị sửa tại chỗ (React Query luôn trả mảng/object mới).
      mockList([item({ key: 1, label: 'Báo cáo mua hàng', grants: [] })])
      rerenderWithCanWrite(true)

      expect(screen.getByTestId('dialog-open')).toHaveTextContent('0 chủ thể')
    },
  )

  it('API lỗi thì hiện trạng thái lỗi rõ ràng, không phải trắng trang', () => {
    mockList(undefined, { isError: true })
    renderTab(true)
    expect(screen.getByText(/Không tải được danh sách/)).toBeInTheDocument()
  })

  it('danh sách rỗng thật (không phải chưa tải xong) thì nói rõ chưa có báo cáo nào', () => {
    mockList([])
    renderTab(true)
    expect(screen.getByText('Chưa có báo cáo nào.')).toBeInTheDocument()
  })
})
