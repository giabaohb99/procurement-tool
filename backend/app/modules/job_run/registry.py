"""Sổ mô tả VIỆC CHẠY NGẦM (bao-CR-703): tên task Celery → tên tiếng Việt, mục đích một câu, nhóm, công tắc.

Mỗi task có trong lịch beat (`app/core/celery_app.py`, kể cả lịch chỉ bật theo cấu hình) PHẢI có một dòng ở đây —
`test_so_viec_chay_ngam_cr703.py` đỏ khi thiếu. Task chạy theo yêu cầu (không lịch) khai thêm nếu muốn màn hiện tên đẹp;
không khai thì màn hiện mã task.

`switch` = khóa app_settings (bool) mà TẮT thì việc tự bỏ qua — màn hiện "đang tắt".
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class JobInfo:
    name: str
    purpose: str
    group: str
    switch: str = ""


JOBS: dict[str, JobInfo] = {
    # ── Sao lưu / lưu trữ ──
    "backup.run": JobInfo("Sao lưu cơ sở dữ liệu", "Dump CSDL ERP rồi đẩy lên kho R2, giữ số bản theo cấu hình.", "backup"),
    "audit.archive": JobInfo("Đóng gói nhật ký tháng", "Gói bốn bảng nhật ký của tháng trước lên R2 (không xóa DB).",
                             "backup"),
    "agent.db_backup": JobInfo("Sao lưu CSDL dịch vụ AI", "Dump CSDL của dịch vụ AI / bot rồi đẩy lên kho lưu trữ.",
                               "backup"),
    "agent.db_backup_watch": JobInfo("Canh bản sao lưu dịch vụ AI",
                                     "Báo khi quá 26 giờ chưa có bản sao lưu thành công của CSDL dịch vụ AI.", "monitor"),
    "agent.db_restore_test": JobInfo("Nạp thử bản sao lưu dịch vụ AI",
                                     "Chủ nhật nạp thử bản mới nhất vào CSDL tạm để chắc bản sao lưu dùng được.", "backup"),
    # ── Dọn dữ liệu ──
    "notification.cleanup": JobInfo("Dọn thông báo cũ", "Xóa thông báo trong chuông cũ hơn số ngày giữ.", "cleanup"),
    "customs.cleanup_row_logs": JobInfo("Dọn nhật ký dòng lô hải quan",
                                        "Xóa nhật ký Thêm mới / Đã có / Trùng của lô nạp hải quan quá số ngày giữ.",
                                        "cleanup"),
    "customs.merge_duplicate_lines": JobInfo("Gộp dòng hải quan trùng",
                                             "Gộp dòng hàng cùng tờ khai, giá, lượng nạp nhiều lần; nhóm khác ô để nguyên.",
                                             "cleanup", switch="customs_line_merge_enabled"),
    "customs.cleanup_export_batches": JobInfo("Dọn lô xuất tra cứu thị trường",
                                              "Xóa tệp của lô xuất toàn bộ quá số ngày giữ; lô kẹt quá 2 giờ thì dừng.",
                                              "cleanup"),
    "request_log.cleanup": JobInfo("Dọn nhật ký truy cập GET", "Xóa dòng truy cập GET quá 90 ngày (đã có gói R2).",
                                   "cleanup"),
    "system_log.cleanup_expired": JobInfo("Dọn nhật ký quá 16 tháng",
                                          "Xóa bốn bảng nhật ký quá 16 tháng, chỉ tháng đã có gói R2.", "cleanup"),
    "attachment.purge_orphans": JobInfo("Dọn tệp đính kèm mồ côi",
                                        "Xóa tệp tải lên mà không gắn vào phiếu nào sau 7 ngày.", "cleanup"),
    "usage.cleanup_ui_events": JobInfo("Dọn sự kiện giao diện thô",
                                       "Xóa sự kiện thao tác thô quá 90 ngày và số gom quá 3 năm.", "cleanup"),
    "job_run.cleanup": JobInfo("Dọn sổ việc chạy ngầm", "Xóa lịch sử chạy việc nền quá số ngày giữ.", "cleanup"),
    "agent.group_purge": JobInfo("Dọn tin nhóm chat của bot", "Xóa tin nhóm Telegram / Zalo quá hạn giữ.", "cleanup"),
    "agent.mcp_log_purge": JobInfo("Dọn nhật ký cổng MCP", "Gom số theo ngày rồi xóa nhật ký gọi MCP quá 180 ngày.",
                                   "cleanup"),
    # ── Thống kê / gom số ──
    "usage.aggregate_daily": JobInfo("Gom số dùng hệ thống theo ngày",
                                     "Gom sự kiện hôm qua thành số theo người cho hồ sơ cách làm việc.", "stats"),
    "feature_usage.aggregate_daily": JobInfo("Gom số dùng theo chức năng",
                                             "Gom số dùng từng chức năng theo ngày (sau gom theo người).", "stats"),
    "capability.build_cycles": JobInfo("Dựng vòng đời phiếu", "Tính vòng đời phiếu mới chạm tới cho báo cáo năng lực.",
                                       "stats"),
    "usage.build_weekly_snapshots": JobInfo("Chụp số tuần", "Thứ Hai chụp số của tuần vừa qua cho hồ sơ cách làm việc.",
                                            "stats"),
    "agent.ai_usage_push": JobInfo("Đẩy số dùng AI về ERP",
                                   "Gom số lượt dùng AI theo người × ngày từ dịch vụ AI về ERP.", "stats"),
    # ── Giám sát / cảnh báo ──
    "system_log.detect_anomalies": JobInfo("Dò dấu hiệu bất thường",
                                           "Quét 30 phút vừa qua: IP lạ, đổi thiết bị, xóa hàng loạt, 403 dồn dập.",
                                           "monitor"),
    "sync_log.alert_stale_failures": JobInfo("Báo lỗi đồng bộ quá 24 giờ",
                                             "Chuông sáng cho dòng sổ đồng bộ hỏng quá 24 giờ chưa tự vá được.",
                                             "monitor"),
    "agent.health_check": JobInfo("Theo dõi sức khỏe môi trường", "Gọi health từng môi trường mỗi phút, báo khi hỏng.",
                                  "monitor"),
    "agent.runner_watch": JobInfo("Canh máy sửa mã", "Báo khi máy sửa mã của bot mất liên lạc hoặc nối lại.", "monitor"),
    "agent.resource_report_due": JobInfo("Báo tài nguyên máy chủ", "07:35 gửi bản tin RAM / đĩa / tải máy chủ.",
                                         "monitor"),
    # ── Đồng bộ hệ thống khác ──
    "datxe.pull_updated": JobInfo("Kéo đặt xe / duyệt dấu từ app cũ",
                                  "Kéo phiếu mới đổi trên app đặt xe / duyệt dấu cũ về ERP.", "sync",
                                  switch="sync_datxe_enabled"),
    "datxe.retry_pending": JobInfo("Chạy lại đồng bộ app cũ đang chờ", "Thử lại các dòng sổ đồng bộ từ app cũ còn chờ.",
                                   "sync", switch="sync_datxe_enabled"),
    "datxe.full_sweep": JobInfo("Quét đủ app đặt xe cũ", "Lưới an toàn hằng đêm: quét toàn bộ để bắt phiếu sót.",
                                "sync", switch="sync_datxe_enabled"),
    "datxe.retry_outbound": JobInfo("Đẩy lại ERP sang app cũ", "Thử lại các thay đổi ERP chưa đẩy được sang app cũ.",
                                    "sync", switch="sync_datxe_outbound_enabled"),
    "coffee.pull_orders": JobInfo("Kéo đơn POS365", "Kéo đơn bán của quầy cà phê để cộng / trừ điểm.", "sync"),
    "coffee.check_voids": JobInfo("Soát đơn POS365 bị hủy", "Trừ lại điểm của đơn đã hủy trên POS365.", "sync"),
    "coffee.monthly_reset": JobInfo("Đặt lại điểm cà phê theo kỳ", "Ngày 1 hằng tháng chốt kỳ và đặt lại điểm.", "sync"),
    "coffee.reconcile": JobInfo("Đối chiếu điểm cà phê", "Đối chiếu sổ điểm với POS365 mỗi sáng.", "sync"),
    # ── Bot / trợ lý AI ──
    "agent.triage_inbox": JobInfo("Phân loại tin đến của bot", "Nhặt tin chưa xử lý của bot và chia việc.", "bot"),
    "agent.deploy_due": JobInfo("Gộp + deploy dev đã hẹn giờ", "Nhặt việc gộp / deploy dev đã tới giờ hẹn.", "bot"),
    "agent.heartbeat": JobInfo("Nhịp báo việc đang chạy", "Việc bot chạy lâu thì nhắn 'em vẫn đang làm'.", "bot"),
    "agent.pull_tickets": JobInfo("Kéo phiếu hỗ trợ cho bot", "Phiếu hỗ trợ ERP giao cho bot thành việc của bot.", "bot"),
    "agent.forward_bells": JobInfo("Chuyển chuông ERP sang chat", "Gửi chuông ERP sang Telegram của người đã liên kết.",
                                   "reminder"),
    "agent.fire_reminders": JobInfo("Bắn lời nhắc đã hẹn", "Nhắn lời nhắc đặt bằng câu nói khi tới giờ.", "reminder"),
    "agent.briefs_due": JobInfo("Bản tin sáng", "Gửi bản tin theo giờ mỗi người tự đặt.", "reminder"),
    "agent.meeting_reminders": JobInfo("Nhắc trước giờ họp", "Nhắc lịch họp sắp tới mỗi 5 phút.", "reminder"),
    "agent.work_due": JobInfo("Nhắc hạn việc Dự án", "Nhắc người được giao trước 1 ngày, ngày hạn, quá hạn.", "reminder"),
    "agent.learning_tick": JobInfo("Vòng tự học của bot", "Đề xuất thuật ngữ và chỗ trợ lý còn thiếu chức năng.", "bot"),
    "agent.session_summary": JobInfo("Tóm tắt buổi chat", "Tóm tắt buổi chat im lặng 30 phút vào ghi chú riêng.", "bot"),
    "agent.meeting_drive_scan": JobInfo("Quét thư mục Họp trên Drive", "Tìm tệp ghi âm / tài liệu họp mới để hỏi làm biên bản.",
                                        "bot"),
    "agent.poll_telegram": JobInfo("Kéo tin Telegram", "Hỏi tin mới của bot Telegram mỗi 10 giây (khi không có poller).",
                                   "bot"),
}
