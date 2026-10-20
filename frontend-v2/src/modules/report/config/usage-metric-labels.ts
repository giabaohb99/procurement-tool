import { USAGE_UNMEASURED_REASON } from '@/shared/constants/statuses'

/**
 * Tầng HIỂN THỊ của hồ sơ cách làm việc: khóa chỉ số (`metric_catalog` backend,
 * cố định) → nhãn tiếng Việt + cách định dạng. Khóa lạ vẫn hiện (nhãn = khóa)
 * để backend thêm chỉ số trước FE không làm mất số liệu.
 */
export type UsageMetricKind = 'ratio' | 'count' | 'clock' | 'minutes' | 'hours' | 'ms' | 'per100'

export const USAGE_METRIC_LABELS: Record<string, { label: string; kind: UsageMetricKind }> = {
  first_seen_p50_min: { label: 'Giờ vào đầu (giữa)', kind: 'clock' },
  last_action_p50_min: { label: 'Thao tác cuối (giữa)', kind: 'clock' },
  active_ratio: { label: 'Ngày có vào / ngày làm việc', kind: 'ratio' },
  active_workdays: { label: 'Ngày làm việc có vào', kind: 'count' },
  workdays_net: { label: 'Ngày làm việc ròng', kind: 'count' },
  bursts_per_day: { label: 'Phiên làm việc mỗi ngày', kind: 'count' },
  active_minutes_p50: { label: 'Phút hoạt động mỗi ngày', kind: 'minutes' },
  logins: { label: 'Lượt đăng nhập', kind: 'count' },
  offhours_write_share: { label: 'Ghi ngoài giờ', kind: 'ratio' },
  mobile_write_share: { label: 'Ghi trên điện thoại', kind: 'ratio' },
  mobile_approve_share: { label: 'Duyệt trên điện thoại', kind: 'ratio' },
  screen_dwell_avg: { label: 'Ở lại mỗi màn (TB)', kind: 'ms' },
  distinct_screens_30d: { label: 'Số màn khác nhau (30 ngày)', kind: 'count' },
  loop_share: { label: 'Đường đi vòng lại', kind: 'ratio' },
  reports_opened: { label: 'Báo cáo đã mở', kind: 'count' },
  http_403: { label: 'Bị chặn quyền (403)', kind: 'count' },
  form_submit_p50_ms: { label: 'Thời gian lập một phiếu (giữa)', kind: 'ms' },
  drafts_before_submit_p50: { label: 'Lưu nháp trước khi gửi (giữa)', kind: 'count' },
  edits_after_submit_share: { label: 'Phiếu sửa sau khi gửi', kind: 'ratio' },
  returned_rate: { label: 'Phiếu bị trả về / từ chối', kind: 'ratio' },
  form_abandon_rate: { label: 'Mở form rồi bỏ', kind: 'ratio' },
  approval_wait_p50_h: { label: 'Tới lượt → xử lý (giữa)', kind: 'hours' },
  approval_wait_p90_h: { label: 'Tới lượt → xử lý (chậm nhất 10%)', kind: 'hours' },
  pending_now: { label: 'Đang chờ duyệt', kind: 'count' },
  batch_approval_share: { label: 'Duyệt theo lô', kind: 'ratio' },
  month_end_create_share: { label: 'Phiếu lập 3 ngày cuối tháng', kind: 'ratio' },
  on_behalf_received: { label: 'Được bấm hộ', kind: 'count' },
  on_behalf_done: { label: 'Bấm hộ người khác', kind: 'count' },
  imports: { label: 'Lần nhập file', kind: 'count' },
  import_error_rate: { label: 'Dòng nhập lỗi', kind: 'ratio' },
  work_on_time_rate: { label: 'Việc dự án đúng hạn', kind: 'ratio' },
  work_overdue_open: { label: 'Việc dự án quá hạn đang mở', kind: 'count' },
  notif_read_rate: { label: 'Thông báo đã đọc', kind: 'ratio' },
  notif_read_p50_min: { label: 'Gửi → đọc (giữa)', kind: 'minutes' },
  mention_reply_p50_h: { label: 'Nhắc tên → trả lời (giữa)', kind: 'hours' },
  comments: { label: 'Bình luận', kind: 'count' },
  assistant_questions: { label: 'Câu hỏi trợ lý AI', kind: 'count' },
  assistant_changes: { label: 'Thay đổi do trợ lý AI', kind: 'count' },
  saved_prefs: { label: 'Bộ lọc / cột đã lưu', kind: 'count' },
  http_422_per_100_writes: { label: 'Lỗi nhập liệu (422) / 100 lần lưu', kind: 'per100' },
  search_empty_rate: { label: 'Tìm không ra kết quả', kind: 'ratio' },
  help_views: { label: 'Lượt xem hướng dẫn', kind: 'count' },
  tickets: { label: 'Yêu cầu hỗ trợ', kind: 'count' },
  exports: { label: 'Lần xuất Excel', kind: 'count' },
  export_per_list_view: { label: 'Xuất Excel / lượt xem danh sách', kind: 'ratio' },
  new_ip_logins: { label: 'Đăng nhập từ IP lạ', kind: 'count' },
  new_device_logins: { label: 'Đăng nhập từ thiết bị lạ', kind: 'count' },
  max_parallel_ips: { label: 'Nhiều nơi cùng lúc (số IP)', kind: 'count' },
  export_rows_spike: { label: 'Xuất vượt mức thường', kind: 'count' },
  max_deletes_10min: { label: 'Xóa hàng loạt (10 phút)', kind: 'count' },
  proxied_days_ratio: { label: 'Ngày được bấm hộ', kind: 'ratio' },
  heatmap_top3_share: { label: 'Dồn vào 3 khung giờ', kind: 'ratio' },
  page_views: { label: 'Lượt xem màn hình', kind: 'count' },
  docs_created: { label: 'Phiếu đã lập', kind: 'count' },
  docs_submitted: { label: 'Phiếu đã gửi', kind: 'count' },
  proxy_share: { label: 'Phiếu được lập hộ', kind: 'ratio' },
  export_entity_weeks_max: { label: 'Số tuần liền xuất cùng loại dữ liệu', kind: 'count' },
  active_after_resign: { label: 'Nghỉ việc vẫn hoạt động', kind: 'count' },
}

export function metricLabel(key: string, override?: string): string {
  return override ?? USAGE_METRIC_LABELS[key]?.label ?? key
}

/** Tên loại phiếu theo `entity` backend (`TRACKED_DOC_ENTITIES`). */
export const USAGE_DOC_ENTITY_LABELS: Record<string, string> = {
  purchase_request: 'Yêu cầu mua hàng',
  survey_request: 'Yêu cầu báo giá',
  purchase_order: 'Đơn mua hàng',
  goods_receipt: 'Nhận hàng',
  payment_request: 'Đề nghị thanh toán',
  document: 'Văn bản',
  leave_request: 'Đơn nghỉ phép',
  vehicle_booking: 'Đặt xe',
  seal_request: 'Đóng dấu',
  labor_contract: 'Hợp đồng lao động',
}

/** Lý do chưa đo được — nhãn lấy từ `USAGE_UNMEASURED_REASON` (sinh từ backend), viết thường để nối sau «Chưa đo được — ». */
export function unmeasuredReasonLabel(code: number): string {
  const label = USAGE_UNMEASURED_REASON.find((o) => o.value === String(code))?.label
  return label ? label.toLowerCase() : 'không rõ lý do'
}
