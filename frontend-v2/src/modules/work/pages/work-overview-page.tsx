import { CircleCheck, FolderKanban, ListTodo, TriangleAlert, UserRoundCheck } from 'lucide-react'

import { WorkTaskShortlist } from '../components/work-task-shortlist'

import { ChartCard } from '@/shared/ui/chart'
import { DonutChart } from '@/shared/ui/donut-chart'
import { HorizontalBarChart } from '@/shared/ui/horizontal-bar-chart'
import { ModuleDashboard } from '@/shared/ui/module-dashboard'
import { StatCard } from '@/shared/ui/stat-card'
import { useWorkOverview } from '../hooks/use-work-overview'

/**
 * Màn mặc định của phân hệ Dự án — trang BÁO CÁO, cùng khuôn `ModuleDashboard`
 * với Nhân sự / Sản xuất / Quản trị.
 *
 * Trước đây chỗ này chỉ là một dòng "chọn một dự án ở cột bên trái": mở phân hệ
 * ra thấy trang trắng, không biết mình đang có bao nhiêu việc, việc nào trễ.
 *
 * Cố ý KHÔNG tự nhảy vào dự án đầu tiên: nhảy thì người dùng mở phân hệ ra đã
 * thấy việc của một đội nào đó mà không hiểu vì sao đang đứng ở đó.
 */
export function WorkOverviewPage() {
  const { data, isLoading, byProject, byPriority } = useWorkOverview()

  return (
    <ModuleDashboard
      title="Dự án"
      description="Dự án, bảng kanban, giao việc và theo dõi tiến độ."
      stats={
        <div className="space-y-4">
          {/*  ⚠️ HAI Ô MỘT HÀNG ở khổ hẹp (`grid-cols-2`), không phải một.
               Bản cũ để `sm:grid-cols-2` nên dưới 640px mỗi ô chiếm trọn bề
               ngang: năm ô xếp dọc thành **hơn 540px chỉ để bày năm con số**,
               tức phải vuốt hai lần mới thấy hết phần đầu trang, còn hai biểu
               đồ — thứ đáng xem nhất — thì nằm ngoài tầm mắt. Con số ngắn, ô
               không cần rộng. Cùng lưới với trang Tổng quan Nhân sự.

               Năm ô chia hai cột thì ô cuối đứng một mình nửa hàng; cố ý xếp
               «Đã hoàn thành» vào chỗ đó — nó là ô ÍT phải hành động nhất. */}
          <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-3 xl:grid-cols-5">
            <StatCard
              icon={FolderKanban}
              label="Dự án đang chạy"
              value={(data?.project_total ?? 0).toLocaleString('vi-VN')}
              loading={isLoading}
            />
            <StatCard
              icon={ListTodo}
              label="Việc chưa xong"
              value={(data?.task_open ?? 0).toLocaleString('vi-VN')}
              loading={isLoading}
            />
            <StatCard
              icon={TriangleAlert}
              label="Việc quá hạn"
              value={(data?.task_overdue ?? 0).toLocaleString('vi-VN')}
              loading={isLoading}
              //  Quá hạn là con số phải đập vào mắt; 0 thì để màu thường, tô đỏ
              //  một số 0 là báo động giả.
              hint={data?.task_overdue ? 'Cần xử lý ngay' : undefined}
              tone={data?.task_overdue ? 'danger' : undefined}
            />
            <StatCard
              icon={UserRoundCheck}
              label="Việc của tôi"
              value={(data?.task_mine ?? 0).toLocaleString('vi-VN')}
              loading={isLoading}
            />
            <StatCard
              icon={CircleCheck}
              label="Đã hoàn thành"
              value={(data?.task_done ?? 0).toLocaleString('vi-VN')}
              loading={isLoading}
            />
          </div>

          {/* MỖI HÀNG một lưới riêng để thẻ trong hàng cao bằng nhau. Biểu đồ
              cột cần bề ngang nên chiếm 2/3, vòng cơ cấu 1/3. */}
          <div className="grid gap-4 lg:grid-cols-3">
            <ChartCard
              className="lg:col-span-2"
              title="Việc chưa xong theo dự án"
              description="Tám dự án nhiều việc nhất; dự án đã lưu trữ không tính."
              loading={isLoading}
              isEmpty={byProject.length === 0}
            >
              <HorizontalBarChart data={byProject} unit="việc" />
            </ChartCard>

            <ChartCard
              title="Cơ cấu mức ưu tiên"
              description="Việc chưa xong, theo mức ưu tiên đang đặt."
              loading={isLoading}
              isEmpty={byPriority.length === 0}
            >
              <DonutChart data={byPriority} centerLabel="việc" unit="việc" />
            </ChartCard>
          </div>

          {/*  ⚠️ Hai khối này là phần BÙ cho dải thẻ đếm ở trên. Thẻ nói «22
               việc quá hạn» rồi dừng — người đọc biết mình có vấn đề nhưng
               không có chỗ nào bấm vào để xem vấn đề nằm ở đâu. Hai biểu đồ
               cũng vậy: chúng nói *bao nhiêu* và *ở đâu*, không nói *việc nào*.

               Quá hạn đứng TRƯỚC việc của tôi: nó là thứ cả đội đang chờ, còn
               việc của tôi thì tôi vốn đã biết. */}
          <div className="grid gap-4 lg:grid-cols-2">
            <WorkTaskShortlist
              icon={TriangleAlert}
              overdue
              title="Việc quá hạn"
              description="Hạn cũ nhất lên đầu — việc trễ lâu nhất là việc đáng hỏi nhất."
              tasks={data?.overdue_tasks ?? []}
              total={data?.task_overdue ?? 0}
              loading={isLoading}
              emptyMessage="Không có việc nào quá hạn."
            />

            <WorkTaskShortlist
              icon={UserRoundCheck}
              title="Việc của tôi"
              description="Việc tôi đang phụ trách, hạn gần nhất lên đầu."
              tasks={data?.my_tasks ?? []}
              total={data?.task_mine ?? 0}
              loading={isLoading}
              emptyMessage="Chưa có việc nào giao cho bạn."
            />
          </div>
        </div>
      }
    />
  )
}
