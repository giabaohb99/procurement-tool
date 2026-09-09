import { BarList } from '@/shared/ui/bar-list'
import { ChartCard } from '@/shared/ui/chart'
import { DonutChart } from '@/shared/ui/donut-chart'
import { HorizontalBarChart } from '@/shared/ui/horizontal-bar-chart'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { AccountCoverageCard } from '../components/account-coverage-card'
import { HrOverviewStats } from '../components/hr-overview-stats'
import { LeaveGlanceCard } from '../components/leave-glance-card'
import { ProfileGapsCard } from '../components/profile-gaps-card'
import { RoomGlanceCard } from '../components/room-glance-card'
import { useHrLeaveGlance } from '../hooks/use-hr-leave-glance'
import { useHrOverview } from '../hooks/use-hr-overview'
import { useHrRoomGlance } from '../hooks/use-hr-room-glance'

/** Câu hiện thay biểu đồ khi người xem không có `employee.read`. */
const NO_EMPLOYEE_PERMISSION = 'Bạn không có quyền xem hồ sơ nhân sự.'

/**
 * Tổng quan Nhân sự: số liệu · việc phải làm · cơ cấu.
 *
 * Dựng đúng khuôn trang Tổng quan Văn thư và Tài chính (`PageContainer` +
 * `PageHeader` + `StatCard` + `ChartCard`), không qua `ModuleDashboard`:
 * khung đó xếp sẵn thẻ theo lưới của nó, còn trang này cần các ô span riêng để
 * lấp kín cả hai mốc màn hình (xem chú thích ở lưới bên dưới). `ModuleDashboard`
 * nay chỉ còn phục vụ mấy phân hệ chưa có nội dung.
 *
 * Không lặp lại thẻ lối tắt vào từng màn hình — menu trái đã có sẵn các mục đó.
 */
export function HrDashboardPage() {
  const overview = useHrOverview()
  const leave = useHrLeaveGlance()
  const room = useHrRoomGlance()
  //  Chốt "bây giờ" MỘT LẦN cho cả lượt vẽ rồi truyền xuống: để mỗi dòng tự gọi
  //  `new Date()` thì hai cuộc họp sát nhau có thể rơi vào hai phía của cùng
  //  một mốc kết thúc, và dấu «Đang họp» hiện ở hai dòng liền.
  const now = new Date()

  return (
    <PageContainer>
      <PageHeader
        title="Nhân sự"
        description="Đội hình đang có, việc nghỉ phép trong tuần và những hồ sơ còn thiếu thông tin."
      />

      <HrOverviewStats overview={overview} leave={leave} />

      {/*
        HAI BỐ CỤC, một cây DOM. Các ô span được chọn để CẢ HAI mốc đều lấp kín
        lưới — đảo thứ tự cho đẹp ở một mốc thì mốc kia thừa ra một ô trống.

        - **13 inch** (`lg`, 3 cột):
              [ theo phòng ban        ×2 ][ hồ sơ cần bổ sung ]
              [ nghỉ phép ][ lịch họp ][ cơ cấu ]
              [ tài khoản ][ theo pháp nhân          ×2 ]
        - **15 inch trở lên** (`2xl`, từ 1536px — 4 cột):
              [ theo phòng ban   ×2 ][ hồ sơ cần bổ sung ×2 ]
              [ nghỉ phép        ×2 ][ lịch họp          ×2 ]
              [ cơ cấu ][ tài khoản ][ theo pháp nhân    ×2 ]

        ⚠️ Tổng span mỗi mốc phải chia hết cho số cột (lg: 9 = 3×3 · 2xl: 12 =
        3×4). Thêm một thẻ mà không tính lại hai tổng đó là lưới thủng một ô,
        và ô thủng nhìn hệt như một thẻ tải hỏng.

        Bốn thẻ DANH SÁCH rộng ×2 ở `2xl` (hồ sơ · nghỉ phép · lịch họp): mỗi
        dòng của chúng là chữ (tên người · phòng · khoảng ngày giờ · câu hậu
        quả), hẹp một cột thì dòng nào cũng gãy làm đôi. Hai thẻ CON SỐ (cơ cấu ·
        tài khoản) thì ngược lại, rộng ra chỉ để thêm khoảng trắng.

        Thẻ trong cùng một hàng CAO BẰNG NHAU — `ChartCard` khai `h-full`, và
        `height: 100%` của một ô lưới đo theo chiều cao HÀNG chứ không theo nội
        dung, nên `items-start` ở đây không gỡ được (đã đo: 3 thẻ hàng hai đều
        351px). Đó là chủ ý của `ChartCard`; thẻ nào ít nội dung thì tự đẩy dòng
        chân xuống đáy bằng `mt-auto`.
      */}
      <div className="grid gap-4 lg:grid-cols-3 2xl:grid-cols-4">
        <ChartCard
          className="lg:col-span-2"
          title="Nhân sự theo phòng ban"
          description="Số nhân sự đang làm việc của từng phòng."
          loading={overview.isLoading}
          isEmpty={!overview.canReadEmployees || overview.byDepartment.length === 0}
          emptyLabel={
            overview.canReadEmployees ? undefined : NO_EMPLOYEE_PERMISSION
          }
        >
          <HorizontalBarChart data={overview.byDepartment} unit="nhân sự" />
        </ChartCard>

        <ProfileGapsCard
          className="2xl:col-span-2"
          gaps={overview.gaps}
          loading={overview.isLoading}
          canRead={overview.canReadEmployees}
        />

        <LeaveGlanceCard className="2xl:col-span-2" glance={leave} />

        <RoomGlanceCard className="2xl:col-span-2" glance={room} now={now} />

        <ChartCard
          title="Cơ cấu trạng thái"
          description="Toàn bộ hồ sơ nhân sự, kể cả đã nghỉ."
          loading={overview.isLoading}
          isEmpty={!overview.canReadEmployees || overview.byStatus.length === 0}
          emptyLabel={
            overview.canReadEmployees ? undefined : NO_EMPLOYEE_PERMISSION
          }
        >
          <DonutChart data={overview.byStatus} centerLabel="hồ sơ" unit="nhân sự" />
        </ChartCard>

        <AccountCoverageCard
          data={overview.accounts}
          loading={overview.isLoading || overview.isLoadingAccounts}
          canRead={overview.canReadAccounts}
        />

        <ChartCard
          className="lg:col-span-2 2xl:col-span-2"
          title="Nhân sự theo pháp nhân"
          description="Số nhân sự đang làm việc của từng công ty."
          loading={overview.isLoading}
          isEmpty={!overview.canReadEmployees || overview.byCompany.length === 0}
          emptyLabel={
            overview.canReadEmployees ? undefined : NO_EMPLOYEE_PERMISSION
          }
        >
          {/*  `BarList` chứ không `HorizontalBarChart` như thẻ phòng ban: TÊN
               PHÁP NHÂN DÀI. Trục Y của biểu đồ cắt nhãn ở 26 ký tự, nên hai
               công ty "CÔNG TY TNHH XUẤT NHẬP KHẨU …" ra hai dòng chữ giống hệt
               nhau — người đọc không biết dòng nào là dòng nào. `BarList` để
               nhãn nằm TRÊN thanh, rộng hết bề ngang thẻ. Dày dòng hơn nữa nên
               thẻ thấp xuống ~200px, bớt khoảng trắng cho hai thẻ cùng hàng. */}
          <BarList emptyLabel="Chưa có nhân sự nào." items={overview.byCompany} />
        </ChartCard>
      </div>
    </PageContainer>
  )
}
