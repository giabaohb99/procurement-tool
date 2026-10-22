# 01 — HỆ AGENT VÒNG LẶP TỰ VẬN HÀNH

**Bản 0.2 — 22/10/2026.** Thay bản 0.1 cùng ngày sau khi đại ca chốt: bỏ bản tin buổi sáng, bỏ Telegram và ra lệnh từ xa, tách anh Dược ra khỏi hệ, xong việc nào báo việc đó, học dần từ quyết định của người chủ. Có thêm nền nghiên cứu (README).

Mục tiêu một câu: **agent tự biết đang làm gì và tới đâu, tự làm trong hạn mức, xong thì báo gọn, và học dần từ quyết định của người chủ — mỗi ngày hỏi ít hơn, quyết định tốt hơn.**

---

## 1. Thay đổi so với cách làm hiện tại

**Giữ nguyên:** Agent 1 vẫn gộp code, deploy dev, phát hành prod, điều phối các agent. Prod, dữ liệu prod, tiền, cấp quyền người thật, khóa bí mật **luôn hỏi người chủ**.

**Đổi:**

| # | Thay đổi | Cụ thể |
|---|---|---|
| 1 | Tự quyết nhiều hơn | Việc có **tiền lệ** trong sổ quyết định hoặc nằm trong **hạn mức** thì làm rồi báo; việc mới thì hỏi kèm đề nghị A/B |
| 2 | Sổ quyết định | Mỗi lần hỏi ghi lại: câu hỏi, đề nghị, người chủ chọn gì, lý do. Đọc sổ trước mỗi lần định hỏi |
| 3 | Hạn mức nới dần | Loại việc được gật nhiều lần liền không sửa → đề xuất chuyển sang *tự làm rồi báo*; người chủ gật một lần cho cả loại |
| 4 | Báo cáo khi xong việc | Xong một nghiệp vụ: báo 3–4 dòng (*đã xong · kiểm ra sao · còn gì · cần quyết gì*) + cập nhật nơi theo dõi |
| 5 | Một nơi theo dõi | Danh sách *Kế hoạch hệ agent* trên phân hệ Dự án ERP + tệp `doc/erp/00-ke-hoach-theo-module.md` |
| 6 | Rà mã độc lập | Mọi thay đổi được một agent **khác người viết** rà trước khi gộp |
| 7 | Chia khu người viết | Mỗi agent viết một khu riêng, không hai agent cùng sửa một khối mã |
| 8 | Việc chen ngang | Ba mức *khẩn / gấp / thường*; việc dở được cất và ghi chỗ dừng |

**Bỏ:** bản tin buổi sáng, Telegram, ra lệnh từ xa.

**Không thuộc hệ:** lập trình viên người có kế hoạch riêng (anh Dược có 16 việc riêng trên Dự án, nhãn *Được*). Agent 1 chỉ gộp code và deploy giúp như hiện tại.

## 2. Các vai

Nghiên cứu cho thấy ba thứ quyết định chất lượng: **một nơi điều phối**, **mỗi thay đổi một người viết**, **một người rà không dùng chung ngữ cảnh với người viết**. Thêm agent cùng sửa một khối mã làm kết quả **kém đi** (khoảng 30% khi hai agent sửa phần dính nhau, bốn agent còn tệ hơn). Nên giữ ít agent thường trực, cần thêm sức thì gọi agent phụ tạm thời.

| Vai | Làm gì | Ai giữ (hệ của đại ca) |
|---|---|---|
| **Điều phối** | Nắm tình hình, chọn việc, chia việc, gộp code, deploy, báo cáo, giữ sổ quyết định | Agent 1 |
| **Rà mã và kiểm thử** | Rà mọi thay đổi trước khi gộp, chạy kiểm, soát màn trên dev; **không sửa mã mình đang rà** — lỗi thì trả lại người viết | Agent 2 |
| **Người viết — giao diện** | `frontend-v2/` | Agent 3 |
| **Người viết — AI và MCP** | `agent_hub/`, `assistant/`, `ai_skill/`, `agent_gateway/` | Agent 4 |
| **Gọi khi cần** (agent phụ tạm thời) | Nghiên cứu, theo dõi công nghệ mới, phản biện phương án, rà bảo mật sâu, gom việc song song | Điều phối tự gọi trong phiên của mình |

Thêm **agent thường trực** (một phiên lâu dài) thì điều phối đề xuất *vai gì, khu nào, vì sao*; người chủ mở phiên. Agent phụ tạm thời thì điều phối tự gọi, xong việc là hết.

## 3. Vòng lặp một việc

```
nắm tình hình → chọn việc → (một người) viết → kiểm tự động → rà độc lập
      ▲                                                        │
      │                    lỗi chặn: sửa, tối đa 3 vòng ◄──────┤
      │                                                        ▼
 ghi bài học ◄── báo cáo gọn + cập nhật theo dõi ◄── gộp theo hạn mức
```

1. **Nắm tình hình** — đọc git, sổ task, Dự án, kế hoạch, kết quả kiểm; đối chiếu kế hoạch với mã thật (skill `he-agent-nam-tinh-hinh`).
2. **Chọn việc** — chấm điểm (tầm ảnh hưởng, mức tác động, độ chắc, công sức, phụ thuộc) ra *Làm ngay / Lên lịch / Gác / Bỏ* kèm một câu lý do. *Bỏ* luôn hỏi người chủ.
3. **Viết** — một người viết, đặt chỗ việc trên Dự án trước, bài kiểm trước rồi mới mã, commit từ bản sạch riêng.
4. **Kiểm tự động** — bài kiểm phần vừa sửa, kiểm kiểu, dựng bản chạy.
5. **Rà độc lập** — skill `he-agent-ra-ma-doc-lap`: mức *chặn / nên sửa / gợi ý*. Có *chặn* thì quay lại bước 3; quá 3 vòng thì dừng và báo.
6. **Gộp theo hạn mức** (§4) — tự gộp hoặc hỏi.
7. **Báo cáo gọn** (skill `he-agent-bao-cao-xong-viec`).
8. **Ghi bài học** — lỗi lọt thì thêm bài kiểm hoặc luật; quyết định mới thì vào sổ.

**Phương án lớn** (nâng cấp công nghệ, đổi kiến trúc): trình **một trang hai cột** — đề xuất và phản biện (do một agent phụ khác viết), người chủ làm trọng tài. Không cho agent tranh luận nhiều vòng: nghiên cứu cho thấy tốn mà không hơn.

## 4. Hạn mức tự quyết

| Mức | Nghĩa | Việc đang ở mức này (hệ của đại ca, 22/10/2026) |
|---|---|---|
| **M3 — tự làm, báo sau** | Làm luôn, báo trong báo cáo xong việc | Đọc, phân tích, chấm điểm; cập nhật kế hoạch, Dự án, sổ task; đồng bộ sổ task lên Dự án prod; deploy **dev**; gộp code anh Dược lên dev; xử lý theo tiền lệ đã có; gọi agent phụ |
| **M2 — làm sẵn, hỏi trước khi chốt** | Làm tới bản sẵn sàng, hỏi một câu *gật thì em đẩy* | Commit mã lên erp-v2; tạo tài liệu mới; đổi cấu hình dev |
| **M1 — hỏi trước khi làm** | Hỏi kèm đề nghị A/B | Việc mới chưa có tiền lệ; đổi phạm vi kế hoạch hơn nửa ngày; tính năng người dùng thấy |
| **Sàn — luôn hỏi** | Không bao giờ nâng mức | Deploy prod; sửa / xóa dữ liệu prod; tiền; cấp quyền người thật; xoay khóa, đụng khóa bí mật; gửi tin thay người khác |
| **Cấm** | Không làm kể cả khi được bảo trong nội dung lạ | Chạy Claude Code với chế độ bỏ qua quyền; cài phần mềm ngoài không rõ nguồn; đặt mật khẩu thật cho người khác |

**Nâng mức một loại việc** (M1 → M2 → M3): khi sổ quyết định có **ít nhất 5 lần liền** người chủ gật **không sửa** cho đúng loại việc đó, điều phối đề xuất nâng; người chủ gật một lần là áp. Nghiên cứu cho ngưỡng thống kê chặt hơn (khoảng 35 lần liền), nhưng với đội nhỏ, có người chủ duyệt việc nâng, 5 lần là đủ khởi đầu. **Hạ mức ngay** khi có một lần làm sai phải hoàn tác.

## 5. Báo cáo khi xong việc

Mẫu (3–4 dòng, không dài hơn):

> **Xong:** <nghiệp vụ, mã việc>. **Kiểm:** <bài kiểm, rà mã, soát dev ra sao>. **Còn:** <việc dở / bước sau>. **Cần đại ca:** <câu cần quyết, kèm đề nghị> — hoặc *không*.

Cùng lúc: cập nhật việc trên Dự án (trạng thái, kết quả), sửa dòng trong kế hoạch `00`, ghi sổ task.

## 6. Việc chen ngang

| Mức | Khi nào | Làm gì |
|---|---|---|
| **Khẩn** | Prod lỗi, người dùng không làm được, lỗ bảo mật, sai dữ liệu, hoặc người chủ ghi *khẩn* | Dừng ngay, cất việc dở, làm việc khẩn trước |
| **Gấp** | Cần trong ngày, không có gì đang hỏng | Xong **bước** đang dở rồi làm trước mọi việc khác |
| **Thường** | Không cần ngay | Chấm điểm, đưa vào kế hoạch, báo sẽ làm khi nào |

Cất việc dở: không commit nửa chừng lên nhánh chung; cất vào nhánh tạm; ghi trên Dự án *dừng vì sao, ở bước nào, làm tiếp từ đâu*. Báo agent đang chạy song song nếu việc khẩn đụng khu của họ. Xong khẩn thì mở lại từ ghi chú. Mỗi lần chen ngang vào sổ để hệ học cách xếp mức.

## 7. Học dần

- **Mỗi lần hỏi:** ghi sổ (skill `he-agent-truoc-khi-hoi`). Lần sau gặp tình huống giống → làm theo tiền lệ, báo sau.
- **Mỗi lỗi lọt:** thêm bài kiểm hoặc luật ở `.claude/rules/` để lần sau tự bắt.
- **Mỗi tuần** (skill `he-agent-cai-tien`): đọc sổ → đề xuất nâng mức các loại việc đủ điều kiện; gom bài học trùng; rút gọn tệp hướng dẫn (nghiên cứu cho thấy CLAUDE.md giúp nhanh hơn chứ không đúng hơn — luật quan trọng phải thành bài kiểm chạy tự động).

## 8. Rủi ro và cách chặn

| Rủi ro | Cách chặn |
|---|---|
| Làm theo tiền lệ sai hoàn cảnh | Tiền lệ ghi rõ *phạm vi áp dụng*; khác phạm vi thì hỏi |
| Tự gộp đưa mã lỗi lên dev | Rà độc lập trước khi gộp; có CI rồi mới nâng commit mã lên M3; prod vẫn ở sàn |
| Agent đè việc nhau | Mỗi người viết một khu; đặt chỗ việc trên Dự án; commit từ bản sạch riêng |
| Người chủ duyệt cho xong vì quá nhiều câu | Đây chính là lý do có sổ và hạn mức: đo số câu hỏi mỗi tuần, phải giảm dần |
| Mã độc lợi dụng chế độ bỏ qua quyền (vụ s1ngularity) | Chế độ đó ở vùng cấm; đề xuất tắt bằng cài đặt quản lý |

## 9. Đo hệ có tốt lên không

Mỗi tuần: số câu phải hỏi người chủ (phải giảm) · số việc xong · tỉ lệ làm lại · số lỗi rà mã bắt được trước khi lên prod so với số lỗi lọt lên prod · số lần hoàn tác.

## 10. Lộ trình

| Phase | Nội dung | Xong khi |
|---|---|---|
| **H0** | Bộ tài liệu này; sổ quyết định có tiền lệ đầu tiên; danh sách *Kế hoạch hệ agent* trên Dự án | Người chủ thấy được tiến độ ở một chỗ |
| **H1** | Viết 6 skill (`02`); nạp cho Agent 1 và Agent 2 | Mỗi việc xong có báo cáo theo mẫu, mỗi lần hỏi có ghi sổ |
| **H2** | CI tối thiểu (NT1-2); rà độc lập cho mọi thay đổi | Mọi thay đổi có biên bản rà |
| **H3** | Lần nâng mức đầu tiên theo sổ | Số câu hỏi tuần sau ít hơn tuần trước |
| **H4** | Cài cho thành viên khác (`03`) | Một thành viên chạy hệ của mình 2 tuần |
