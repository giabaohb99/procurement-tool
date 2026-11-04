import { useCallback, useRef } from 'react'
import { List, Users } from 'lucide-react'

import { useScrolled } from '@/shared/hooks/use-scrolled'
import { useSetUrlParams, useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Tabs, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { LeaveBalanceMatrixTable } from '../components/leave-balance-matrix-table'
import { LeaveBalancePageActions } from '../components/leave-balance-page-actions'
import { LeaveBalanceRowsTable } from '../components/leave-balance-rows-table'
import { LIST_TABS_STICKY } from '../utils/list-sticky'

/**
 * Hai thẻ của màn (duoc-CR-717): "Theo dòng quỹ" (mặc định, KHÔNG ghi URL) và "Theo nhân sự"
 * (`?view=people`, ma trận người × loại nghỉ). Nhớ ở URL để gửi link / tải lại vẫn đúng thẻ.
 */
const VIEW_ROWS = 'rows'
const VIEW_PEOPLE = 'people'

/**
 * QUỸ PHÉP NĂM — màn của phòng Nhân sự.
 *
 * Màn chỉ còn là KHUNG: tiêu đề + cụm nút (`LeaveBalancePageActions` — Cấp quỹ / Kết sổ / Đối chiếu), dải hai
 * thẻ, và thân của thẻ đang mở (`LeaveBalanceRowsTable` · `LeaveBalanceMatrixTable`). Tách ra ở review L6
 * của duoc-CR-717 (tệp cũ 444 dòng). **Điều chỉnh tay** nằm ở TRANG CHI TIẾT (`/hr/leave-balances/:id`),
 * không phải popup từ dòng — xem docstring của `leave-balance-detail-page.tsx`.
 *
 * Ô tìm `?q=` và ô năm `?year=` dùng CHUNG hai thẻ nên MỘT chủ ở đây rồi truyền xuống (review L9): hai
 * `useUrlSearchParam` cùng ghi một tham số thì mỗi bên giữ một state cục bộ, gõ ở bên này bên kia không biết.
 */
export function LeaveBalancePage() {
  const currentYear = new Date().getFullYear()
  const search = useUrlSearchParam()
  const [year, setYear] = useUrlParamState('year', String(currentYear))
  const [view] = useUrlParamState('view', VIEW_ROWS)
  const peopleView = view === VIEW_PEOPLE
  const setUrlParams = useSetUrlParams()
  //  Đổi thẻ trong MỘT lượt ghi URL: giữ ô tìm + năm (chung hai thẻ), bỏ ô lọc riêng của thẻ cũ —
  //  để lại `leave_type_id` thì thẻ "Theo nhân sự" báo "đang lọc" mà không có ô nào để gỡ.
  const switchView = useCallback(
    (next: string) =>
      setUrlParams({
        view: next === VIEW_PEOPLE ? VIEW_PEOPLE : null,
        leave_type_id: null,
        department_id: null,
        employee_status: null,
      }),
    [setUrlParams],
  )

  //  Dải ghim đầu trang đổ bóng khi có nội dung trôi bên dưới — xem
  //  `list-sticky.ts`. Đo ở khối bọc vì nó nằm cùng khung cuộn với hai dải.
  const stickyRef = useRef<HTMLDivElement>(null)
  const scrolled = useScrolled(stickyRef)

  return (
    //  ⚠️ `fill` chỉ bật từ `md`: ở khổ hẹp bảng biến thành danh sách thẻ dài,
    //  mà `fill` nhét nó vào một khe vài trăm pixel và biến thành cuộn LỒNG —
    //  vuốt trúng mép ngoài khe thì trang không nhúc nhích. Cùng bài học với
    //  `leave-request-list-page`.
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Quỹ phép năm"
        //  Dòng mô tả ẩn trên máy hẹp: câu giới thiệu, đọc một lần rồi thôi,
        //  nhưng chiếm hai dòng ở đầu MỌI lần mở màn.
        description={
          <span className="max-md:hidden">Cấp phát, theo dõi và điều chỉnh số ngày phép của từng nhân sự.</span>
        }
        actions={<LeaveBalancePageActions year={year} />}
      />

      {/*  `group` + `data-scrolled` là đường dẫn tín hiệu "trang đã cuộn" xuống
           tới dải ghim nằm sâu bên trong (thanh công cụ do `DataTable` vẽ, tầng
           trang không với tới được bằng prop). Bóng đổ của dải đó đọc thuộc tính
           này — xem `list-sticky.ts`. */}
      <div ref={stickyRef} data-scrolled={scrolled ? '' : undefined} className="group flex min-h-0 flex-1 flex-col">
        <div className={LIST_TABS_STICKY}>
          <Tabs value={peopleView ? VIEW_PEOPLE : VIEW_ROWS} onValueChange={switchView}>
            <TabsList className="mb-3 w-full shrink-0 max-md:mb-0 md:w-fit">
              <TabsTrigger value={VIEW_ROWS} className="min-w-0">
                <List className="size-4" />
                Theo dòng quỹ
              </TabsTrigger>
              <TabsTrigger value={VIEW_PEOPLE} className="min-w-0">
                <Users className="size-4" />
                Theo nhân sự
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        <Card className="flex min-h-0 w-full min-w-0 flex-1 flex-col p-3 md:p-4">
          {peopleView ? (
            <LeaveBalanceMatrixTable year={year} onYearChange={setYear} search={search} />
          ) : (
            <LeaveBalanceRowsTable year={year} onYearChange={setYear} search={search} />
          )}
        </Card>
      </div>
    </PageContainer>
  )
}
