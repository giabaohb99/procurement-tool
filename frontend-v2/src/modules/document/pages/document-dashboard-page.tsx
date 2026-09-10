import { AlertTriangle, CalendarClock, CheckCircle2, FileText, PenLine } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { CHART_COLORS, CHART_NEUTRAL, ChartCard } from '@/shared/ui/chart'
import { ColumnChart } from '@/shared/ui/column-chart'
import { DonutChart } from '@/shared/ui/donut-chart'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { StatCard } from '@/shared/ui/stat-card'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { DocumentDashboardFilters } from '../components/document-dashboard-filters'
import { DocumentPriorityMatrix } from '../components/document-priority-matrix'
import { toDashboardParams, type DateRangeKey } from '../helpers/dashboard-date-range'
import { useDocumentDashboard } from '../hooks/use-document-dashboard'
import type { DocumentRecord } from '../types/document-record'
import type { DocumentTodo } from '../types/document-dashboard'

/**
 * Tổng quan Văn thư: KPI + văn bản ban hành theo tháng + cơ cấu theo loại +
 * việc cần xử lý + văn bản gần đây.
 *
 * Dựng đúng khuôn trang Tổng quan Thu mua (`ProcurementDashboardPage`) — cùng
 * `StatCard`, `ChartCard`, `ColumnChart`, `DonutChart` — để hai phân hệ không
 * đọc ra hai thứ tiếng khác nhau.
 *
 * Toàn bộ lấy từ MỘT lần gọi `/api/documents/dashboard`, và backend đã lọc theo
 * đúng phạm vi dữ liệu như danh sách văn bản.
 */
export function DocumentDashboardPage() {
  //  Mặc định «Tất cả»: mở trang lên là thấy toàn cảnh. Mặc định "Hôm nay" thì
  //  gần như lúc nào cũng là một trang trắng toàn số 0, và người dùng kết luận
  //  hệ thống hỏng chứ không nghĩ tới bộ lọc.
  const [companyId, setCompanyId] = useState<number | undefined>()
  const [departmentId, setDepartmentId] = useState<number | undefined>()
  const [rangeKey, setRangeKey] = useState<DateRangeKey>('all')
  //  Khoảng ngày TỰ CHỌN — chỉ có nghĩa khi `rangeKey === 'custom'`. Giữ ở đây
  //  chứ không suy ra từ `rangeKey` như mấy mức bày sẵn: hai đầu do người dùng
  //  chấm trên lịch, không có công thức nào tính ra được.
  const [fromDate, setFromDate] = useState<string | undefined>()
  const [toDate, setToDate] = useState<string | undefined>()

  const { data, isLoading } = useDocumentDashboard(
    toDashboardParams(companyId, departmentId, rangeKey, { from: fromDate, to: toDate }),
  )

  const kpi = data?.kpi
  const issuedYear = (data?.issued_12m ?? []).reduce((sum, item) => sum + item.value, 0)
  const matrixTotal = Object.values(data?.priority_matrix ?? {}).reduce((sum, so) => sum + so, 0)

  return (
    <PageContainer>
      {/*  Dòng mô tả ẩn ở khổ điện thoại — cùng luật `ModuleDashboard` đã áp cho
           mọi trang tổng quan phân hệ. Câu giới thiệu này đọc một lần rồi thôi,
           nhưng ngốn hai dòng ở đầu MỌI lần mở màn, ngay trên thứ người ta vào
           đây để xem. (Trang này dựng tay `PageContainer` + `PageHeader` chứ
           không qua `ModuleDashboard` vì nó có bộ lọc và năm biểu đồ riêng, nên
           luật kia không tự chạm tới.) */}
      <PageHeader
        title="Văn thư"
        description={
          <span className="max-md:hidden">
            Công văn, quyết định, quy chế và biểu mẫu nội bộ.
          </span>
        }
      />

      <DocumentDashboardFilters
        companyId={companyId}
        departmentId={departmentId}
        rangeKey={rangeKey}
        fromDate={fromDate}
        toDate={toDate}
        onChange={(next) => {
          setCompanyId(next.companyId)
          setDepartmentId(next.departmentId)
          setRangeKey(next.rangeKey)
          setFromDate(next.fromDate)
          setToDate(next.toDate)
        }}
      />

      {/*  Năm thẻ KPI: 2 → 3 → 5 cột. Thiếu mốc `lg` ở giữa thì khoảng
           1024–1279px (cửa sổ chia đôi màn 13") tụt thẳng về 2 cột, tức ba hàng
           thẻ chiếm gần nửa màn hình trước khi thấy được biểu đồ nào.

           ⚠️ HAI Ô MỘT HÀNG ở khổ hẹp (`grid-cols-2`), không phải một. Bản cũ
           để `sm:grid-cols-2` — dưới 640px mỗi ô chiếm trọn bề ngang, nên năm ô
           xếp dọc thành **650px** chỉ để bày năm con số, và mọi biểu đồ nằm
           ngoài tầm mắt. Hai ô một hàng còn ~330px, vừa đúng một màn. Cùng luật
           đã áp cho Tổng quan Dự án. */}
      <div className="mb-4 grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-3 xl:grid-cols-5">
        <StatCard
          icon={CheckCircle2}
          label="Đang có hiệu lực"
          value={kpi?.effective ?? 0}
          hint="Văn bản đang áp dụng"
          loading={isLoading}
        />
        <StatCard
          icon={PenLine}
          label="Đang chờ duyệt"
          value={kpi?.submitted ?? 0}
          hint={kpi?.submitted ? 'Cần phê duyệt' : 'Không tồn đọng'}
          tone={kpi?.submitted ? 'warning' : undefined}
          loading={isLoading}
        />
        <StatCard
          icon={AlertTriangle}
          label="Cần rà lại"
          value={kpi?.needs_review ?? 0}
          hint={kpi?.needs_review ? 'Văn bản cha đã đổi' : 'Không có'}
          tone={kpi?.needs_review ? 'danger' : undefined}
          loading={isLoading}
        />
        <StatCard
          icon={CalendarClock}
          label="Sắp hết hiệu lực"
          value={kpi?.expiring ?? 0}
          hint="Trong 30 ngày tới"
          tone={kpi?.expiring ? 'warning' : undefined}
          loading={isLoading}
        />
        <StatCard
          icon={FileText}
          label="Bản nháp"
          value={kpi?.draft ?? 0}
          hint="Đang soạn"
          loading={isLoading}
        />
      </div>

      {/*
        HAI BỐ CỤC, một cây DOM.

        - **13 inch** (`lg`, khoảng 1280–1470px ngang) → **3 cột**:
              [ ban hành theo tháng  ×2 ][ việc cần xử lý ]
              [ cơ cấu theo loại ][ ma trận ưu tiên   ×2 ]
              [ văn bản gần đây                       ×3 ]
        - **15 inch trở lên** (`2xl`, từ 1536px — MacBook 15/16" mặc định là
          1680/1728) → **4 cột**, cả trang gọn trong HAI hàng:
              [ ban hành theo tháng ×2 ][ việc cần xử lý ][ cơ cấu theo loại ]
              [ ma trận ưu tiên     ×2 ][ văn bản gần đây               ×2  ]

        Thứ tự thẻ trong DOM cố định (tháng · việc · cơ cấu · ma trận · gần đây)
        và được chọn để **cả hai mốc đều lấp kín lưới**. Đảo thứ tự cho đẹp ở một
        mốc thì mốc kia thừa ra một ô trống — đúng lỗi bố cục cũ, nơi thẻ ma trận
        chiếm 2 cột và bỏ hở cột thứ ba.

        Không dùng `grid-flow-dense`: nó lấp lỗ bằng cách kéo thẻ phía sau lên
        trước, nên thứ tự đọc trên màn hình khác thứ tự bàn phím đi qua.
      */}
      <div className="grid items-start gap-4 lg:grid-cols-3 2xl:grid-cols-4">
        <ChartCard
          className="lg:col-span-2"
          title="Văn bản ban hành theo tháng"
          description={`${issuedYear} văn bản trong 12 tháng gần nhất`}
          loading={isLoading}
          isEmpty={issuedYear === 0}
          emptyLabel="12 tháng qua chưa ban hành văn bản nào."
        >
          <ColumnChart data={data?.issued_12m ?? []} unit="văn bản" />
        </ChartCard>

        <ChartCard
          title="Việc cần xử lý"
          description={`${(data?.todo ?? []).reduce((s, i) => s + i.count, 0)} việc đang chờ`}
          loading={isLoading}
          isEmpty={(data?.todo ?? []).length === 0}
          emptyLabel="Không có việc nào đang treo."
        >
          <ul className="divide-y">
            {(data?.todo ?? []).map((item) => (
              <TodoRow key={item.key} item={item} />
            ))}
          </ul>
        </ChartCard>

        <ChartCard
          title="Cơ cấu theo loại"
          description="Văn bản đang có hiệu lực."
          loading={isLoading}
          isEmpty={(data?.by_type ?? []).length === 0}
        >
          <DonutChart
            centerLabel="văn bản"
            unit="văn bản"
            data={(data?.by_type ?? []).map((item, index) => ({
              label: item.name,
              value: item.value,
              //  Quá 4 loại thì phần đuôi dùng xám trung tính — bảng màu chỉ có
              //  4 tông đã kiểm cho người mù màu.
              color: CHART_COLORS[index] ?? CHART_NEUTRAL,
            }))}
          />
        </ChartCard>

        <ChartCard
          className="lg:col-span-2"
          title="Thống kê văn bản theo mức độ quan trọng, khẩn cấp"
          description="Văn bản đang có hiệu lực, chia theo hai trục ưu tiên."
          loading={isLoading}
          isEmpty={matrixTotal === 0}
          emptyLabel="Chưa có văn bản nào đang có hiệu lực."
        >
          <DocumentPriorityMatrix data={data?.priority_matrix} />
        </ChartCard>

        <ChartCard
          //  Trải hết hàng ở 13" (3 cột) và nằm cạnh ma trận ở màn rộng (2/4).
          //  Danh sách 8 dòng, mỗi dòng bốn phần — hẹp hơn nữa là số hiệu và
          //  ngày rơi xuống dòng thứ hai.
          className="lg:col-span-3 2xl:col-span-2"
          title="Văn bản gần đây"
          description="8 văn bản mới nhất trong phạm vi bạn xem được."
          loading={isLoading}
          isEmpty={(data?.recent ?? []).length === 0}
          emptyLabel="Chưa có văn bản nào."
        >
          <ul className="divide-y">
            {(data?.recent ?? []).map((row) => (
              <RecentRow key={row.id} row={row} />
            ))}
          </ul>
        </ChartCard>
      </div>
    </PageContainer>
  )
}

function TodoRow({ item }: { item: DocumentTodo }) {
  return (
    <li className="flex items-center justify-between gap-3 py-2.5 first:pt-0">
      <div className="min-w-0">
        <p className="text-sm font-medium">{item.label}</p>
        <p className="text-xs text-muted-foreground">{item.hint}</p>
      </div>
      <span
        className={cn(
          'shrink-0 text-lg font-semibold tabular-nums',
          item.tone === 'warning' && 'text-warning',
        )}
      >
        {item.count}
      </span>
    </li>
  )
}

/**
 * Một dòng của khối «Văn bản gần đây».
 *
 * ⚠️ **Khổ hẹp xếp HAI DÒNG, tiêu đề lên trước.** Bốn phần nhét trên một hàng
 * 358px thì «chưa cấp số» — chuỗi dài nhất và ít giá trị nhất — chiếm gần một
 * phần ba, còn tên văn bản (thứ duy nhất nói đó là văn bản gì) bị cắt còn dăm
 * chữ. Ở màn rộng một hàng vẫn đúng: thẻ này trải 3/4 cột nên bốn phần đều đủ
 * chỗ.
 *
 * ⚠️ `md:contents` là thứ giữ MỘT cây DOM cho cả hai bố cục: ở khổ rộng, khối
 * bọc phần phụ tan ra và ba thẻ con trở thành con trực tiếp của hàng flex, rồi
 * `md:order-*` xếp chúng về đúng thứ tự cũ (số hiệu · tên · trạng thái · ngày).
 * Chép thành hai nhánh JSX thì sớm muộn hai khổ màn hiện hai thứ khác nhau.
 */
function RecentRow({ row }: { row: DocumentRecord }) {
  return (
    <li className="py-2.5 first:pt-0">
      <Link
        to={appRoutes.document.documentDetail(row.id)}
        className="flex flex-col gap-0.5 text-sm hover:underline md:flex-row md:flex-wrap md:items-center md:gap-2"
      >
        <span className="min-w-0 truncate font-medium md:order-2 md:flex-1">{row.title}</span>

        <span className="flex min-w-0 items-center gap-2 md:contents">
          {/*  `font-mono` chỉ dành cho SỐ HIỆU thật. Câu «chưa cấp số» là lời
               nói, không phải mã: bày bằng chữ đều nét thì các chữ cái dãn ra
               như một dãy ký tự rời, đọc ra như lỗi hiển thị chứ không như một
               câu. */}
          <span
            className={cn(
              'shrink-0 text-xs text-muted-foreground md:order-1',
              row.display_code ? 'font-mono' : 'italic',
            )}
          >
            {row.display_code || 'chưa cấp số'}
          </span>
          <span className="truncate text-xs text-muted-foreground md:order-3">
            {row.status_label}
          </span>
          {row.effective_date && (
            <span className="shrink-0 text-xs text-muted-foreground md:order-4">
              {formatDate(row.effective_date)}
            </span>
          )}
        </span>
      </Link>
    </li>
  )
}
