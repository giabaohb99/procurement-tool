/**
 * Định nghĩa từng chỉ số của «Bộ chỉ số đánh giá» (duoc-CR-649) — tầng HIỂN THỊ, khóa theo `metric_catalog.py` backend.
 * Nguồn gốc nội dung: `plans/261019-1450-tracking-ho-so-lam-viec-cr641/metric-definitions.md`. Backend chỉ trả khóa và mã (luật R2).
 * Thêm khóa ở backend mà quên khai ở đây thì `usage-metric-definitions.test.ts` đỏ.
 */
export interface UsageMetricDefinition {
  /** Chỉ số cho biết điều gì. */
  meaning: string
  /** Cách tính, viết bằng lời. */
  formula: string
  /** Lấy số từ đâu. */
  source: string
}

/** Mục §3.x của backend → tên nhóm hiển thị (cùng thứ tự với hồ sơ một người). */
export const USAGE_METRIC_SECTIONS: { section: string; title: string }[] = [
  { section: '3.1', title: 'Nhịp làm việc' },
  { section: '3.2', title: 'Màn hay vào' },
  { section: '3.3', title: 'Cách làm phiếu' },
  { section: '3.4', title: 'Phản hồi và phối hợp' },
  { section: '3.5', title: 'Mức thành thạo' },
  { section: '3.6', title: 'An toàn tài khoản' },
]

const REQ_LOG = 'Nhật ký truy cập hệ thống'
const AUDIT = 'Nhật ký thao tác (audit)'
const UI_EVENT = 'Sự kiện giao diện (chỉ có từ khi bật thu thập)'
const WINDOW = 'trong cửa sổ 4 tuần gần nhất'

export const USAGE_METRIC_DEFINITIONS: Record<string, UsageMetricDefinition> = {
  // 3.1 Nhịp làm việc
  first_seen_p50_min: { meaning: 'Người này thường bắt đầu làm việc lúc mấy giờ.', formula: 'Mỗi ngày có hoạt động lấy phút đầu tiên có thao tác, rồi lấy giá trị giữa của các ngày.', source: `${REQ_LOG} + sự kiện giao diện` },
  last_action_p50_min: { meaning: 'Người này thường thao tác lần cuối trong ngày lúc mấy giờ.', formula: 'Mỗi ngày có hoạt động lấy phút thao tác cuối cùng, rồi lấy giá trị giữa của các ngày.', source: `${REQ_LOG} + sự kiện giao diện` },
  workdays_net: { meaning: 'Số ngày người này đáng ra phải làm việc, làm mẫu số cho các tỷ lệ.', formula: 'Cộng các ngày làm việc theo Lịch làm việc, trừ ngày lễ và ngày nghỉ phép đã duyệt.', source: 'Lịch làm việc, ngày lễ, đơn nghỉ phép đã duyệt' },
  active_workdays: { meaning: 'Số ngày làm việc người này có vào hệ thống.', formula: 'Đếm ngày làm việc có ít nhất một thao tác.', source: REQ_LOG },
  active_ratio: { meaning: 'Mức đều đặn dùng hệ thống so với số ngày phải làm.', formula: 'Ngày làm việc có vào chia cho ngày làm việc ròng (tối đa 100%).', source: REQ_LOG },
  proxied_days_ratio: { meaning: 'Bao nhiêu ngày làm việc người này không vào hệ thống nhưng có người khác bấm hộ.', formula: 'Ngày làm việc không có thao tác riêng mà có phiếu được bấm hộ, chia cho ngày làm việc ròng.', source: 'Phiếu được lập hộ, duyệt thay theo ủy quyền' },
  bursts_per_day: { meaning: 'Một ngày làm việc ngắt thành mấy đợt (nghỉ giữa đợt quá 30 phút).', formula: 'Đếm chuỗi thao tác liên tục, chuỗi kết thúc khi nghỉ quá 30 phút; lấy trung bình mỗi ngày có vào.', source: `${REQ_LOG} + sự kiện giao diện` },
  active_minutes_p50: { meaning: 'Mỗi ngày người này thực sự thao tác khoảng bao nhiêu phút.', formula: 'Cộng độ dài các đợt làm việc trong ngày, lấy giá trị giữa của các ngày.', source: `${REQ_LOG} + sự kiện giao diện` },
  logins: { meaning: 'Số lần đăng nhập mới.', formula: `Đếm phiên đăng nhập được tạo ${WINDOW}.`, source: 'Bảng phiên đăng nhập' },
  offhours_write_share: { meaning: 'Phần việc ghi dữ liệu diễn ra ngoài giờ hoặc cuối tuần, ngày lễ.', formula: 'Số lượt ghi (tạo, sửa, xóa) ngoài giờ làm việc chia cho tổng lượt ghi; giờ nghỉ trưa tính trong giờ.', source: REQ_LOG },
  mobile_write_share: { meaning: 'Phần thao tác ghi dữ liệu làm bằng điện thoại.', formula: 'Lượt ghi từ phiên đăng nhập trên điện thoại chia cho tổng lượt ghi.', source: `${REQ_LOG} + phiên đăng nhập` },
  mobile_approve_share: { meaning: 'Phần việc duyệt phiếu làm bằng điện thoại.', formula: 'Lượt duyệt từ phiên đăng nhập trên điện thoại chia cho tổng lượt duyệt.', source: `${AUDIT} + phiên đăng nhập` },
  heatmap_top3_share: { meaning: 'Hoạt động dồn vào ít khung giờ hay trải đều.', formula: 'Tổng thao tác của 3 ô giờ × thứ đông nhất chia cho tổng thao tác.', source: REQ_LOG },
  // 3.2 Màn hay vào
  page_views: { meaning: 'Số lần mở màn hình.', formula: `Đếm lượt xem màn hình ${WINDOW}.`, source: UI_EVENT },
  screen_dwell_avg: { meaning: 'Trung bình người này ở lại một màn bao lâu.', formula: 'Tổng thời gian tab đang hiện chia cho số lần rời màn.', source: UI_EVENT },
  distinct_screens_30d: { meaning: 'Độ rộng sử dụng: đã dùng bao nhiêu màn khác nhau.', formula: 'Đếm màn khác nhau có lượt xem trong 30 ngày.', source: UI_EVENT },
  loop_share: { meaning: 'Hay đi vòng lại màn cũ, dấu hiệu không tìm ra chỗ cần đến.', formula: 'Số lần đi A → B → A chia cho tổng số bộ ba màn liên tiếp.', source: `${UI_EVENT}, chỉ trong 90 ngày` },
  reports_opened: { meaning: 'Người này có xem báo cáo không.', formula: `Đếm lượt mở báo cáo ${WINDOW}.`, source: REQ_LOG },
  http_403: { meaning: 'Bao nhiêu lần bị chặn vì thiếu quyền, dấu hiệu được phân quyền chưa đủ hoặc thử vào chỗ không được phép.', formula: `Đếm lượt bị từ chối quyền (403) ${WINDOW}.`, source: REQ_LOG },
  // 3.3 Cách làm phiếu
  docs_created: { meaning: 'Khối lượng phiếu người này lập mới.', formula: 'Cộng số phiếu lập mới của các loại phiếu theo dõi.', source: AUDIT },
  docs_submitted: { meaning: 'Khối lượng phiếu người này gửi đi.', formula: 'Cộng số phiếu gửi của các loại phiếu theo dõi.', source: AUDIT },
  form_submit_p50_ms: { meaning: 'Lập một phiếu mất bao lâu từ lúc mở form đến lúc gửi.', formula: 'Giá trị giữa của thời gian mở form → bấm gửi.', source: `${UI_EVENT}, chỉ 6 biểu mẫu` },
  drafts_before_submit_p50: { meaning: 'Phải lưu nháp mấy lần mới gửi được phiếu.', formula: 'Với mỗi phiếu gửi lần đầu, đếm số lần người tạo sửa trước khi gửi; lấy giá trị giữa.', source: AUDIT },
  edits_after_submit_share: { meaning: 'Phiếu gửi rồi còn phải sửa lại, dấu hiệu gửi vội.', formula: 'Số phiếu người tạo sửa sau khi gửi chia cho số phiếu đã gửi.', source: AUDIT },
  returned_rate: { meaning: 'Phiếu bị người khác trả về hoặc từ chối, tức chất lượng phiếu.', formula: 'Số phiếu bị trả về hoặc từ chối bởi người khác chia cho số phiếu đã gửi.', source: AUDIT },
  form_abandon_rate: { meaning: 'Mở form lập phiếu rồi bỏ dở.', formula: 'Số lần bỏ form chia cho số lần mở form.', source: `${UI_EVENT}, chỉ 6 biểu mẫu` },
  approval_wait_p50_h: { meaning: 'Việc duyệt đến tay người này thì thường xử lý sau bao lâu.', formula: 'Giá trị giữa của (lúc xử lý − lúc việc đến lượt), tính theo giờ lịch.', source: 'Việc duyệt của bộ máy phê duyệt' },
  approval_wait_p90_h: { meaning: 'Những việc duyệt chậm nhất tồn bao lâu.', formula: 'Mốc 90%: chín phần mười số việc được xử lý nhanh hơn mức này.', source: 'Việc duyệt của bộ máy phê duyệt' },
  pending_now: { meaning: 'Hiện đang tồn bao nhiêu việc chờ người này duyệt.', formula: 'Đếm việc duyệt giao cho người này chưa xử lý.', source: 'Việc duyệt của bộ máy phê duyệt' },
  batch_approval_share: { meaning: 'Duyệt dồn một lượt nhiều phiếu, ít xem kỹ từng phiếu.', formula: 'Lượt duyệt nằm trong cụm từ 5 quyết định trong 10 phút trở lên chia cho tổng lượt duyệt.', source: 'Việc duyệt của bộ máy phê duyệt' },
  month_end_create_share: { meaning: 'Phiếu dồn vào cuối tháng mới lập.', formula: 'Phiếu lập trong 3 ngày cuối tháng chia cho tổng phiếu lập (3 tháng gần nhất).', source: AUDIT },
  on_behalf_received: { meaning: 'Số phiếu của người này do người khác lập hộ.', formula: 'Đếm phiếu có người đề nghị là người này nhưng người tạo là người khác, cộng việc duyệt thay.', source: 'Phiếu nghỉ phép, YCMH, đóng dấu; ủy quyền duyệt' },
  on_behalf_done: { meaning: 'Số phiếu người này lập hộ người khác.', formula: 'Đếm phiếu người này tạo mà người đề nghị là người khác, cộng việc duyệt thay.', source: 'Phiếu nghỉ phép, YCMH, đóng dấu; ủy quyền duyệt' },
  proxy_share: { meaning: 'Phần phiếu của người này do người khác lập hộ.', formula: 'Số phiếu được lập hộ chia cho (phiếu tự lập + phiếu được lập hộ).', source: 'Phiếu nghỉ phép, YCMH, đóng dấu; ủy quyền duyệt' },
  imports: { meaning: 'Có nhập dữ liệu hàng loạt bằng file không.', formula: `Đếm lần nhập file ${WINDOW}.`, source: 'Lô nhập dữ liệu' },
  import_error_rate: { meaning: 'Chất lượng file nhập: bao nhiêu dòng bị lỗi.', formula: 'Tổng dòng lỗi chia cho tổng dòng của các lần nhập.', source: 'Lô nhập dữ liệu' },
  work_on_time_rate: { meaning: 'Việc dự án hoàn thành đúng hạn.', formula: 'Số việc hoàn thành trước hoặc đúng hạn chia cho số việc đã hoàn thành có hạn.', source: 'Việc trong phân hệ Dự án' },
  work_overdue_open: { meaning: 'Đang tồn bao nhiêu việc dự án quá hạn mà chưa xong.', formula: 'Đếm việc được giao đã quá hạn và chưa hoàn thành.', source: 'Việc trong phân hệ Dự án' },
  // 3.4 Phản hồi và phối hợp
  notif_read_rate: { meaning: 'Có đọc thông báo hệ thống gửi đến không.', formula: `Số thông báo đã đọc chia cho số thông báo nhận ${WINDOW}.`, source: 'Bảng thông báo' },
  notif_read_p50_min: { meaning: 'Nhận thông báo thì bao lâu sau mới đọc.', formula: 'Giá trị giữa của (lúc đọc − lúc gửi).', source: 'Bảng thông báo (chỉ tính từ ngày có cột thời điểm đọc)' },
  mention_reply_p50_h: { meaning: 'Được nhắc tên trong bình luận thì bao lâu sau trả lời.', formula: 'Giá trị giữa của (bình luận đầu tiên của người được nhắc sau lúc nhắc − lúc nhắc), tính theo giờ.', source: 'Bình luận và lượt nhắc tên (ước lượng gần đúng)' },
  comments: { meaning: 'Mức tham gia trao đổi trên phiếu.', formula: `Đếm bình luận do người này viết ${WINDOW}. Không đọc nội dung bình luận.`, source: 'Bảng bình luận' },
  assistant_questions: { meaning: 'Có dùng trợ lý AI để hỏi không.', formula: `Đếm câu hỏi gửi trợ lý AI ${WINDOW}. Không lưu chủ đề.`, source: 'Tin nhắn trợ lý AI' },
  assistant_changes: { meaning: 'Có nhờ trợ lý AI thay đổi dữ liệu không.', formula: `Đếm thay đổi do trợ lý AI thực hiện ${WINDOW}.`, source: 'Bảng thay đổi của trợ lý AI' },
  // 3.5 Mức thành thạo
  saved_prefs: { meaning: 'Biết tùy chỉnh hệ thống cho thuận tay (lưu bộ lọc, chỉnh cột).', formula: 'Đếm tùy chọn bộ lọc và cột đã lưu của người này.', source: 'Tùy chọn người dùng' },
  http_422_per_100_writes: { meaning: 'Nhập liệu sai nhiều hay ít (hệ thống từ chối dữ liệu không hợp lệ).', formula: 'Số lượt bị báo lỗi 422 chia cho số lượt lưu, nhân 100.', source: REQ_LOG },
  search_empty_rate: { meaning: 'Tìm kiếm mà không ra kết quả, dấu hiệu chưa quen cách tìm.', formula: 'Số lần tìm không ra kết quả chia cho tổng số lần tìm. Không lưu từ khóa.', source: UI_EVENT },
  help_views: { meaning: 'Có tự tìm hướng dẫn không.', formula: 'Đếm lượt xem trang hướng dẫn và câu hỏi thường gặp.', source: UI_EVENT },
  tickets: { meaning: 'Có phải nhờ hỗ trợ không.', formula: 'Đếm yêu cầu hỗ trợ do người này gửi.', source: 'Bảng yêu cầu hỗ trợ' },
  exports: { meaning: 'Mức dùng xuất Excel, cần đối chiếu với nhu cầu báo cáo thật.', formula: `Đếm lần xuất Excel ${WINDOW}.`, source: 'Nhật ký xuất dữ liệu' },
  export_per_list_view: { meaning: 'Xem danh sách xong là xuất luôn hay xem ngay trên màn.', formula: 'Số lần xuất Excel chia cho số lượt xem màn danh sách.', source: `Nhật ký xuất dữ liệu + ${UI_EVENT.toLowerCase()}` },
  export_entity_weeks_max: { meaning: 'Xuất đều đặn nhiều tuần liền một loại dữ liệu, dấu hiệu làm Excel song song.', formula: 'Số tuần liên tiếp nhiều nhất có xuất cùng một loại dữ liệu.', source: 'Nhật ký xuất dữ liệu' },
  // 3.6 An toàn tài khoản
  new_ip_logins: { meaning: 'Đăng nhập từ địa chỉ mạng chưa từng thấy.', formula: 'Đếm lần đăng nhập từ IP không xuất hiện trong 90 ngày trước.', source: 'Bảng phiên đăng nhập' },
  new_device_logins: { meaning: 'Đăng nhập từ thiết bị chưa từng thấy.', formula: 'Đếm lần đăng nhập từ bộ (loại thiết bị, hệ điều hành, trình duyệt) không xuất hiện trong 90 ngày trước.', source: 'Bảng phiên đăng nhập' },
  max_parallel_ips: { meaning: 'Một tài khoản bị dùng từ nhiều nơi cùng lúc.', formula: 'Số địa chỉ IP khác nhau lớn nhất trong một khung 10 phút.', source: REQ_LOG },
  export_rows_spike: { meaning: 'Tuần này xuất dữ liệu nhiều bất thường so với thói quen.', formula: 'Có (1) khi số dòng xuất trong tuần vượt 3 lần mức p95 của chính người đó trong 12 tuần trước (và từ 1.000 dòng trở lên).', source: 'Nhật ký xuất dữ liệu' },
  max_deletes_10min: { meaning: 'Xóa hàng loạt trong thời gian ngắn.', formula: 'Số thao tác xóa nhiều nhất trong một khung trượt 10 phút.', source: AUDIT },
  active_after_resign: { meaning: 'Tài khoản của người đã nghỉ việc vẫn còn hoạt động.', formula: 'Có (1) khi ngày nghỉ việc đã qua mà tài khoản vẫn có thao tác.', source: 'Hồ sơ nhân sự + nhật ký truy cập' },
}

/** Chỉ số hoãn / bỏ → lý do (khóa theo `DEFERRED_METRICS` backend). */
export const USAGE_DEFERRED_METRICS: Record<string, { title: string; reason: string }> = {
  approval_wait_ycmh_dmh: { title: 'Thời gian duyệt YCMH / ĐMH', reason: 'Hoãn: hai loại phiếu này duyệt ngoài bộ máy phê duyệt nên không có mốc «đến lượt» đáng tin.' },
  comments_own_vs_other: { title: 'Bình luận phiếu mình so với phiếu người khác', reason: 'Hoãn: phải tra chủ phiếu của từng loại phiếu mới tách được.' },
  http_422_per_field: { title: 'Lỗi nhập liệu theo từng trường', reason: 'Hoãn: phải bóc nội dung phản hồi lỗi mới biết trường nào sai.' },
  unused_permissions_90d: { title: 'Quyền 90 ngày không dùng', reason: 'Hoãn: lượt đọc không ánh xạ được về quyền, chỉ làm được nửa phần ghi nên dễ kết luận sai «quyền thừa».' },
  assistant_topics: { title: 'Chủ đề hay hỏi trợ lý AI', reason: 'Bỏ: là văn bản tự do, trái nguyên tắc không lưu nội dung.' },
}
