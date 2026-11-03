# VĂN THƯ (QUẢN LÝ VĂN BẢN)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

## Phân hệ này là gì

Phân hệ quản lý văn bản nội bộ do chính tập đoàn ban hành: soạn thảo, phê duyệt, ban hành, cấp số hiệu, phân phối,
phạm vi áp dụng, phiên bản và clone xuống pháp nhân con. Phân hệ xây ngay trong mã nguồn Thu mua, dùng lại tài khoản,
nhân sự, phòng ban, pháp nhân, phân quyền, thông báo và kho tệp đã có. Giao diện chỉ có trên `frontend-v2`, gốc đường
dẫn `/document` (bản đồ màn ở [tài liệu chức năng §1](chuc-nang/10-van-thu-van-ban.md#1-bản-đồ-màn-hình)).

Bộ tài liệu thiết kế ngày 13/08/2026 đảo hai quyết định của bộ thiết kế văn thư độc lập trước đó: làm trong Thu mua
thay vì hệ riêng, và clone xuống pháp nhân con là cơ chế hợp lệ có kiểm soát. Lý do ở
[nghiên cứu `00` mục 2](nghien-cuu/00-danh-gia-va-cau-hoi.md).

## Tới đâu rồi

| Mảng | Trạng thái | Ghi chú |
|---|---|---|
| Văn bản nội bộ (`origin = 1`): soạn, duyệt, ban hành, số hiệu, phiên bản, phạm vi, quan hệ, clone | Đã có trong mã; môi trường chưa ghi rõ cho từng mảng | Tài liệu chức năng mô tả là đã chạy; riêng luồng duyệt Văn bản ghi hiện trạng prod từ 22/10/2026 ([§13.1](chuc-nang/10-van-thu-van-ban.md#131-luồng-riêng-một-pháp-nhân-ca-agc-22102026)) |
| Văn bản pháp luật ngoài (`origin = 2`), văn bản đến (`origin = 3`) | Chưa làm | Cột đã khai, chưa có màn hình |
| Nơi nhận và xác nhận đã đọc · sổ văn bản đến · trích lục chính thức · lớp chặn theo mức mật | Chưa làm | [Tài liệu chức năng §17](chuc-nang/10-van-thu-van-ban.md#17-chưa-làm--biết-trước-để-khỏi-tìm) |
| Bản lưu trữ hợp đồng lao động | Đã có trong mã | duoc-CR-629, duoc-CR-640 |
| Thư mục văn bản và tìm toàn văn | Đã có trong mã | Luật cho người viết mã ở `.claude/rules/document-folders-search.md` |

Ghi chú: README cũ (13/08/2026) ghi "chưa có dòng mã nào"; thông tin đó đã cũ, nay mã đã có (xem
[api.md](tai-lieu-ky-thuat/api.md)).

## Đọc gì trước

| Muốn biết | Đọc |
|---|---|
| Làm được gì | [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) |
| Chạy tốt cỡ nào, ai được xem gì | [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) |
| Gọi API nào | [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) · nhóm `document`, `doc_folder`, `document_book`, `doc_type`, `dossier`… trên `/docs` |
| Thiết kế, bảng dữ liệu, bẫy | [tai-lieu-ky-thuat/04-bang-du-lieu.md](tai-lieu-ky-thuat/04-bang-du-lieu.md), [tai-lieu-ky-thuat/05-vong-doi-phien-ban.md](tai-lieu-ky-thuat/05-vong-doi-phien-ban.md) |
| So sánh, khảo sát, câu hỏi chờ chốt | [nghien-cuu/00-danh-gia-va-cau-hoi.md](nghien-cuu/00-danh-gia-va-cau-hoi.md) (17 câu hỏi mục 8), [nghien-cuu/03-lark-approver.md](nghien-cuu/03-lark-approver.md) |
| Kế hoạch đang làm / đã xong | [plans/02-lo-trinh-phat-trien.md](plans/02-lo-trinh-phat-trien.md) |
| Kịch bản kiểm thử tay | [kiem-thu/06-kich-ban-test.md](kiem-thu/06-kich-ban-test.md) |
| Hành vi đã có bài kiểm tự động giữ | [chuc-nang/11-van-thu-cac-ca-da-kiem.md](chuc-nang/11-van-thu-cac-ca-da-kiem.md) |
| Hướng dẫn người dùng | Trung tâm trợ giúp, bài *Hướng dẫn sử dụng Văn bản* (`backend/scripts/seed_help_van_ban.py`) và *Hướng dẫn sử dụng công cụ văn thư* (`backend/scripts/seed_help_van_thu.py`) |

## Điều cần nhớ (giữ từ README cũ)

1. Kho tệp vẫn là bucket công khai; bài kiểm chỉ khóa phần API không phát đường dẫn. Chưa đưa văn bản Tuyệt mật thật vào
   hệ ([các ca đã kiểm §3.2](chuc-nang/11-van-thu-cac-ca-da-kiem.md#32-tệp-đính-kèm)).
2. Cấp số văn bản khóa dòng bộ đếm trong cùng giao dịch với việc ghi bản ghi; không có đường "xin một số" đứng riêng.
3. Bộ máy duyệt không có tùy chọn "không tìm thấy người duyệt thì tự duyệt qua".
4. Sửa văn bản đã ban hành có hai cách, không dùng lẫn: quy chế lên phiên bản mới giữ mã, quyết định thì ra văn bản mới
   sửa đổi văn bản cũ ([05-vong-doi-phien-ban.md](tai-lieu-ky-thuat/05-vong-doi-phien-ban.md)).

## Mục lục

| Tệp | Nội dung | Trạng thái |
|---|---|---|
| [changelog.md](changelog.md) | Nhật ký thay đổi của bộ tài liệu thiết kế (13/08/2026) | chưa ghi |
| [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) | Yêu cầu chức năng, mã `CN-VT-NN` | Nháp, bản 0.1 |
| [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) | Yêu cầu phi chức năng, mã `PCN-VT-NN` | Nháp, bản 0.1 |
| [chuc-nang/10-van-thu-van-ban.md](chuc-nang/10-van-thu-van-ban.md) | Tài liệu chức năng chính: màn hình, vòng đời, số hiệu, phạm vi, quyền, phê duyệt, ban hành | chưa ghi |
| [chuc-nang/11-van-thu-cac-ca-da-kiem.md](chuc-nang/11-van-thu-cac-ca-da-kiem.md) | Hành vi đã được bài kiểm tự động khóa, số đo hiệu năng, lỗi đã biết | chưa ghi |
| [chuc-nang/12-danh-sach-tinh-nang.md](chuc-nang/12-danh-sach-tinh-nang.md) | Danh sách 174 tính năng thiết kế ban đầu (nhóm N, A–M, S) | Bản 1.3, 13/08/2026 |
| [du-lieu/convert-van-thu-to-pdf.py](du-lieu/convert-van-thu-to-pdf.py) | Script chuyển tài liệu văn thư sang PDF | chưa ghi |
| [du-lieu/huong-dan-su-dung-van-ban.pdf](du-lieu/huong-dan-su-dung-van-ban.pdf) | Hướng dẫn sử dụng Văn bản (PDF) | chưa ghi |
| [du-lieu/huong-dan-su-dung-van-ban-ban-cu.pdf](du-lieu/huong-dan-su-dung-van-ban-ban-cu.pdf) | Hướng dẫn sử dụng Văn bản, bản cũ (PDF) | chưa ghi |
| [du-lieu/mo-ta-luong-nghiep-vu-van-ban.pdf](du-lieu/mo-ta-luong-nghiep-vu-van-ban.pdf) | Mô tả luồng nghiệp vụ văn bản (PDF) | chưa ghi |
| [du-lieu/quan-ly-van-thu-bo-tai-lieu.pdf](du-lieu/quan-ly-van-thu-bo-tai-lieu.pdf) | Bộ tài liệu quản lý văn thư (PDF) | chưa ghi |
| [kiem-thu/06-kich-ban-test.md](kiem-thu/06-kich-ban-test.md) | Kịch bản chạy tay một vòng đời văn bản trên local | Bản 1.0, 22/08/2026 |
| [nghien-cuu/00-danh-gia-va-cau-hoi.md](nghien-cuu/00-danh-gia-va-cau-hoi.md) | Đánh giá cách làm, ba lỗ hổng phải vá trước, 17 câu hỏi | Bản 1.0, 13/08/2026 |
| [nghien-cuu/03-lark-approver.md](nghien-cuu/03-lark-approver.md) | Đối chiếu 82 tính năng Lark Approver | chưa ghi |
| [plans/02-lo-trinh-phat-trien.md](plans/02-lo-trinh-phat-trien.md) | Lộ trình 10 phase, không mốc thời gian | chưa ghi |
| [tai-lieu-ky-thuat/04-bang-du-lieu.md](tai-lieu-ky-thuat/04-bang-du-lieu.md) | 25 bảng mới, 4 bảng sửa, chỉ mục, ràng buộc, chỗ dễ sai | Bản 1.1 |
| [tai-lieu-ky-thuat/05-vong-doi-phien-ban.md](tai-lieu-ky-thuat/05-vong-doi-phien-ban.md) | Sửa văn bản đã ban hành: lên phiên bản hay ra văn bản sửa đổi | Bản 1.1, 13/08/2026 |
| [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) | Bảng đường API dựng tự động từ mã | Nháp, bản 0.1, 03/11/2026 |
| [`plans/260814-1036-van-thu-p0-p3/`](plans/260814-1036-van-thu-p0-p3/plan.md) | VĂN THƯ — PHASE 0→3 · KẾ HOẠCH TRIỂN KHAI (dời từ `plans/` gốc, bao-CR-712) | chưa ghi |
| [`plans/260824-1342-trang-thai-tra-ve-van-ban/`](plans/260824-1342-trang-thai-tra-ve-van-ban/plan.md) | Văn bản — tách trạng thái **Trả về** và **Đã từ chối** (dời từ `plans/` gốc, bao-CR-712) | chưa ghi |
| [`plans/260921-0920-dieu-kien-ap-dung-ho-so/`](plans/260921-0920-dieu-kien-ap-dung-ho-so/plan.md) | Điều kiện áp dụng của hồ sơ (dời từ `plans/` gốc, bao-CR-712) | chưa ghi |
| [`plans/reports/`](plans/reports/) | Báo cáo của agent khi làm kế hoạch (dời từ `plans/` gốc, bao-CR-712) | chưa ghi |

## Mã nguồn

- Backend: `backend/app/modules/document/`, `backend/app/modules/doc_catalog/`, `backend/app/modules/dossier/`
- Giao diện v2: `frontend-v2/src/modules/document/`, `frontend-v2/src/modules/dossier/`
- Luật cho người viết mã: `.claude/rules/document-folders-search.md` (thư mục, tìm toàn văn, bản lưu trữ hợp đồng lao động)
