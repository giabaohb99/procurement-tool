# HỆ AGENT — CỬA VÀO

Bộ tài liệu cho **hệ agent làm việc cùng một người chủ**: agent tự nắm tình hình, tự làm trong hạn mức, xong việc thì báo gọn, và **học dần từ các quyết định của người chủ** để mỗi ngày phải hỏi ít hơn mà quyết định tốt hơn.

Bộ này viết để **dùng chung**: phần quy trình (vai, vòng lặp, skill, vùng cấm) giống nhau cho mọi người; phần riêng của từng người (sổ quyết định, hạn mức, danh sách theo dõi) tách ra. Đại ca dùng trước; thành viên khác cài theo `03` là có một hệ như vậy cho phần việc của mình.

| Tệp | Đọc khi nào |
|---|---|
| [`01-he-agent-vong-lap-tu-van-hanh.md`](01-he-agent-vong-lap-tu-van-hanh.md) | Hiểu hệ chạy thế nào: vai, vòng lặp, hạn mức, báo cáo, việc chen ngang, học dần |
| [`02-bo-skill.md`](02-bo-skill.md) | Danh sách skill của hệ: mỗi skill làm gì, khi nào dùng, đầu vào / đầu ra |
| [`03-cai-cho-thanh-vien.md`](03-cai-cho-thanh-vien.md) | Cài hệ cho một thành viên mới |
| [`nguoi-chu/`](nguoi-chu/) | Tệp cấu hình của từng người chủ: xưng hô, phần việc, hạn mức, nơi theo dõi |
| [`so-quyet-dinh/`](so-quyet-dinh/) | Sổ quyết định của từng người chủ — dữ liệu để hệ học |
| `.claude/skills/he-agent-*/` (gốc kho mã) | Sáu skill dùng chung: nắm tình hình, trước khi hỏi, báo cáo xong việc, việc chen ngang, rà mã độc lập, cải tiến hằng tuần |

Nền nghiên cứu: báo cáo *Hệ agent phần mềm thu nhỏ* (22/10/2026, lưu ngoài kho mã ở `D:\New folder\thuthapykien\reports\`), so sánh ChatDev, MetaGPT, BMAD, CCPM, Taskmaster, Claude Code, nghiên cứu của Anthropic và Cognition về nhiều agent, và các cách nới quyền tự chủ dần theo lịch sử duyệt.
