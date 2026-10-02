import { appRoutes } from '@/shared/constants/app-routes'

import type { ReportPageConfig } from '../types/report-analytics'
import { WorkReportProjectFilter } from '../components/work-report-project-filter'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/work/summary',
  exportEndpoint: '/api/work/summary/export',
  entity: 'work_task',
  title: 'Công việc & Dự án',
  description:
    'Việc tạo mới/hoàn thành theo kỳ, đang mở, quá hạn, tỷ lệ đúng hạn — theo dự án, người phụ trách, trạng thái, độ ưu tiên.',
  slug: 'work',
  sourcePath: appRoutes.project.list,
  kpis: ['created', 'completed', 'open_tasks', 'overdue_tasks', 'on_time_rate'],
  chartMetric: 'created',
  defaultGroupBy: 'list',
  //  `rankMetric` (H3, review 01/10/2026): hai khối Top xếp theo HAI chỉ số
  //  snapshot khác nhau — không thể dùng chung `meta.rank_by` (mặc định trỏ về
  //  chỉ số đầu `created`), phải khai riêng từng khối.
  breakdowns: [
    { key: 'overdue_by_list', title: 'Top dự án theo quá hạn', rankMetric: 'overdue_tasks' },
    { key: 'open_by_pic', title: 'Top PIC theo việc mở', rankMetric: 'open_tasks' },
  ],
  extraFilters: WorkReportProjectFilter,
  //  `work_task` PUBLIC ở `SCOPE_FIELDS` — phạm vi thật là TƯ CÁCH THÀNH VIÊN dự
  //  án (`visible_list_ids`), không phải pháp nhân. `WorkTask.company_id` lấy từ
  //  pháp nhân người TẠO dự án lúc đó — nhiều nhân sự để trống (= 0) và DEGO là
  //  holding nên dự án xuyên pháp nhân là bình thường (xem đầu
  //  `membership_service.visible_list_ids`); lọc theo nó dễ ẩn nhầm việc thật.
  hideCompany: true,
}

/**
 * Công việc & Dự án — báo cáo kiểu Haravan của phase 06.
 *
 * Bảng dự án gốc vẫn ở `/project/lists` (`sourcePath`): trang này trả lời câu
 * hỏi "đang mở/quá hạn bao nhiêu, ai đang ôm việc" chứ không thay bảng kanban.
 */
export function WorkReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
