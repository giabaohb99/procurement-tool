# ĐỀ XUẤT TỔ CHỨC LẠI TÀI LIỆU DỰ ÁN

| | |
|---|---|
| Bản | 1.2 — 03/11/2026 — **ĐÃ CHỐT** (người chủ đồng ý toàn bộ, giao làm từ P1 dưới mã bao-CR-712). 1.1 theo hướng người chủ: mỗi phân hệ tự chứa đủ loại tài liệu, V1 tách riêng |
| Người đề xuất | A1 Điều phối, theo yêu cầu người chủ |
| Ảnh hưởng | Mọi người viết tài liệu (đại ca, anh Dược, các agent); 245 tệp mã / luật / skill đang trỏ tới đường dẫn `doc/` |

---

## 1. Hiện trạng — vì sao khó đọc

| Vấn đề | Số đo / ví dụ |
|---|---|
| Quá nhiều cửa vào | `doc/` có **19 thư mục cấp 1**, cộng `plans/` (169 tệp), `frontend-v2/plans/` (56 tệp), 3 tệp lẻ ở gốc repo (`TASKS.md`, `task-process.md`, `AGENTS.md`) |
| Hai chỗ cùng tên | `doc/tai-lieu-ky-thuat/` và `doc/erp/tai-lieu-ky-thuat/` |
| Tài liệu một phân hệ nằm rải 3–4 nơi | Văn thư: `doc/erp/van-thu/` + `doc/tai-lieu-chuc-nang/14,15` + `plans/260814-…-van-thu-p0-p3`. Đặt xe / duyệt dấu: 3 thư mục ngoài `doc/erp/` |
| Tài liệu chức năng tách khỏi phân hệ | `doc/tai-lieu-chuc-nang/` 27 tệp đánh số chung `01…19` (có số trùng: hai tệp `16-`, hai tệp `17-`) |
| Đặt tên lẫn kiểu | `Requirement_PO_Detail.md`, `TIEN-DO.md`, `Thiet_Ke_Phan_Quyen.md` cạnh `02-nghi-phep.md`; thư mục tiếng Anh `item/ inventory/ …` cạnh `van-thu/ hai-quan/` |
| Tài liệu thời V1 đứng lẫn với V2 | `doc/yeu-cau/` (Requirement tháng 7), `doc/testcase/`, `doc/thiet-ke/`, `doc/chung/`, `TASKS.md` — đọc vào dễ tin nhầm là còn đúng |
| Dữ liệu lẫn với tài liệu | 9 `.txt`, 3 `.json`, 5 `.xlsx`, 5 `.pdf`, 3 `.py` trong `doc/` |
| Kế hoạch làm việc tách khỏi phân hệ | `plans/` gốc gom kế hoạch của mọi phân hệ, không ai dọn; muốn biết HRM đã lên kế hoạch gì phải lọc tay |

---

## 2. Cấu trúc chuẩn (hướng người chủ)

**Ý chính:** cấp `doc/` chỉ giữ cái **chung**; cái **riêng** của phân hệ nào nằm trọn trong thư mục phân hệ đó, chia con theo **loại tài liệu**, cùng một bộ tên con cho mọi phân hệ. Tài liệu thời V1 vào `doc/v1/`.

```
doc/
├── README.md                      Bản đồ DUY NHẤT: muốn biết gì → đọc đâu
├── plans/                         Kế hoạch TỔNG (nhiều phân hệ, lộ trình toàn hệ, đợt phát hành)
│   └── 00-ke-hoach-theo-module.md ← dời từ doc/erp/
├── tai-lieu-ky-thuat/             Tài liệu CHUNG cho cả hệ
│   ├── change-log.md, change-log-bao.md, change-log-ai.md, nhat-ky-task.md   ← sổ, KHÔNG dời
│   ├── quy-dinh-tai-lieu.md       ← luật ở mục 3
│   ├── kien-truc/                 cấu trúc mã, sơ đồ, từ điển dữ liệu (mô tả bảng DB), danh mục module
│   ├── phan-quyen/                phân quyền hai trục, phạm vi dữ liệu
│   └── van-hanh/                  nhánh và deploy, Docker, bảo mật, rà soát hiệu năng, đánh giá chất lượng mã
├── erp/                           V2 — MỘT thư mục MỘT phân hệ, cùng một khuôn bên trong
│   ├── nen-tang/                  phần dùng chung giữa các phân hệ (luồng duyệt, thông báo, phiếu hỗ trợ, bình luận, nhập xuất)
│   └── <phan-he>/                 thu-mua, kho, mat-hang, nhan-hang, xuat-hang, lo-serial, hai-quan, nhap-khau, san-xuat,
│       │                          hrm, van-thu, duyet-dau, dat-xe, cong-viec, dien-dan, diem-ca-phe, tro-ly-ai, crm
│       ├── README.md              cửa vào: phạm vi · trạng thái · ai phụ trách · mục lục · CR liên quan
│       ├── chuc-nang/             tài liệu chức năng (người dùng, BA đọc): màn nào làm gì, luật nghiệp vụ
│       ├── tai-lieu-ky-thuat/     thiết kế riêng của phân hệ: bảng, API, luồng, bẫy
│       ├── nghien-cuu/            so sánh ERPNext / sản phẩm khác, khảo sát, câu hỏi chờ chốt
│       ├── plans/                 kế hoạch theo CR của phân hệ: <YYMMDD>-<slug>/plan.md + phase-*.md + reports/
│       ├── kiem-thu/              kịch bản kiểm thử tay
│       └── du-lieu/               tệp nguồn của phân hệ (xlsx, pdf, json)
├── agent-hub/                     Bộ máy AI làm ra phần mềm — sản phẩm riêng, dùng cùng khuôn con như một phân hệ
├── he-agent/                      Luật vận hành hệ agent (giữ nguyên)
└── v1/                            Mọi thứ thời Mini Tool Thu Mua V1 (frontend/ đóng băng)
    ├── README.md                  ghi rõ: V1 còn chạy ở thumua.degoholding.vn tới đợt Đ-15, KHÔNG nhận tính năng mới
    ├── yeu-cau/  thiet-ke/  kiem-thu/  chung/  du-lieu/
    └── luu-tru/                   tài liệu hết hiệu lực khác (nếu có)
```

Khuôn con chỉ tạo **khi có nội dung** — không dựng thư mục rỗng cho đủ bộ.

**Không thuộc phạm vi dời** (mã hoặc công cụ đọc thẳng): `CLAUDE.md`, `AGENTS.md`, `.claude/rules/`, `.claude/skills/`, `frontend-v2/docs/ui/`, `backend/app/modules/ai_skill/seed_handbook/`, `README.md` của từng thư mục mã, bài HDSD trong `seed_help_*.py`.

### 2.1. Đánh giá hướng này

| | |
|---|---|
| **Được** | Mọi thứ của một phân hệ ở một chỗ, kể cả kế hoạch → người phụ trách phân hệ tự quản, recap theo phân hệ chỉ cần đọc một thư mục, giao việc cho agent chỉ cần chỉ một đường dẫn. Cấp chung (`plans/`, `tai-lieu-ky-thuat/`) mỏng và rõ nghĩa. V1 tách hẳn nên không ai đọc nhầm yêu cầu tháng 7 là yêu cầu hiện tại |
| **Phải lo** | (1) Công cụ lập kế hoạch của agent đang mặc định ghi vào `plans/` ở gốc repo → phải đổi luật trong CLAUDE.md / skill để agent ghi vào `doc/erp/<phan-he>/plans/`, kế hoạch nhiều phân hệ mới ghi `doc/plans/`. (2) Nghiệp vụ thu mua **dùng chung một backend cho V1 và V2** — tài liệu luật nghiệp vụ (YCMH, YCBG, ĐMH, YCTT) đúng cho cả hai, nên vào `erp/thu-mua/chuc-nang/`; `v1/` chỉ nhận thứ **riêng của V1** (yêu cầu gốc tháng 6–7, thiết kế giao diện cũ, testcase cũ). (3) Phần dùng chung giữa phân hệ (luồng duyệt, phân quyền) dễ bị chép vào từng phân hệ → luật *một sự thật một chỗ*: để ở `erp/nen-tang/` hoặc `tai-lieu-ky-thuat/`, phân hệ chỉ liên kết |
| **Kết luận** | **Nên theo hướng này.** Nó tốt hơn bản 1.0 (bản 1.0 để kế hoạch ở `plans/` gốc rồi dọn — vẫn tách khỏi phân hệ) |

### 2.2. Skill, agent và luật viết mã dùng chung

Ba thứ này **công cụ (Claude Code, Codex) đọc thẳng theo đường dẫn cố định** nên không dời vào `doc/` được — dời là agent không thấy nữa. Cách làm: giữ tệp ở chỗ công cụ đọc, gom cho gọn, và để `doc/` chỉ giữ **mục lục trỏ tới** (không chép nội dung).

| Loại | Chỗ thật (bắt buộc) | Hiện có | Chỉnh |
|---|---|---|---|
| **Skill của dự án** | `.claude/skills/<tên>/SKILL.md` | 13 skill, đã ở một chỗ | Giữ. Mỗi skill một dòng trong mục lục |
| Skill toàn máy | `~/.claude/skills/` (máy từng người) | 15 skill ngoài + graphify | Không trong repo; mục lục ghi tên + mục đích để ai cài máy mới biết cần gì |
| **Định nghĩa agent** | `.claude/agents/*.md` | 4 (ai-mcp, dieu-phoi, giao-dien-v2, tai-lieu-kiem-thu) | Giữ |
| **Luật viết mã chung** (đặt tên hàm / biến / tệp, ngôn ngữ chuỗi và chú thích, không emoji, commit, cách viết bài kiểm) | `.claude/rules/` — tệp **không khai `paths:`** thì luôn nạp | Đang rải: `backend/.claude/rules/naming.md` và `frontend-v2/.claude/rules/naming.md` **trùng một đoạn**, `doc/chung/NAMING_CONVENTIONS.md` (bản V1), một phần trong CLAUDE.md, một phần trong bộ nhớ agent | Gom về **một tệp `.claude/rules/chung-dat-ten-va-quy-uoc.md`** (luôn nạp); xóa đoạn trùng ở hai tệp `naming.md`; `NAMING_CONVENTIONS.md` → `doc/v1/` |
| **Luật theo khu** (backend, frontend-v2, nhân sự, thu mua…) | `.claude/rules/<khu>-*.md` có `paths:` (chỉ nạp khi sửa đúng thư mục); `frontend-v2/.claude/rules/*` | 8 + 7 tệp | Giữ, đặt tên theo tiền tố khu: `chung-*`, `backend-*`, `v2-*`, `hr-*`, `thu-mua-*` |
| **Luật viết tài liệu** (mục 3 dưới) | `.claude/rules/chung-tai-lieu.md` với `paths: doc/**` | chưa có | Mới: agent sửa tài liệu là tự nạp luật này |
| Hướng dẫn cho Codex | `AGENTS.md` | Bản chép tay của CLAUDE.md, dễ lệch | Rút gọn thành một dòng: *đọc CLAUDE.md và `.claude/rules/`* |

**Mục lục cho người đọc:** `doc/tai-lieu-ky-thuat/quy-dinh/README.md` — ba bảng: *luật chung · luật theo khu · skill và agent*, mỗi dòng: tên, khi nào nạp / khi nào dùng, ai giữ, liên kết tới tệp thật. Thêm skill hay luật mới thì thêm một dòng ở đây trong cùng commit (bài kiểm tự động ở mục 3.10 soát luôn: skill / luật nào chưa có trong mục lục thì báo).

---

## 3. Quy định (bản đề xuất của `quy-dinh-tai-lieu.md`)

1. **Riêng thì về phân hệ, chung thì lên cấp `doc/`.** Tài liệu chỉ nói về một phân hệ → `doc/erp/<phan-he>/<loại>/`. Nói về nhiều phân hệ / toàn hệ → `doc/plans/` hoặc `doc/tai-lieu-ky-thuat/`.
2. **Một sự thật một chỗ.** Chỗ khác cần thì liên kết, không chép.
3. **Thư mục phân hệ nào cũng có `README.md`** (phạm vi, trạng thái, người phụ trách, mục lục). Thêm tệp là thêm dòng mục lục trong cùng commit.
4. **Đặt tên:** chữ thường, không dấu, nối gạch ngang; tiền tố số `NN-` theo thứ tự đọc, không trùng số trong một thư mục. Cấm `CamelCase`, `snake_case`, chữ HOA. Thư mục kế hoạch: `<YYMMDD>-<slug>[-<mã CR>]/`.
5. **Đầu mỗi tài liệu một bảng nhỏ:** *Bản · Ngày · Người phụ trách · Trạng thái (Nháp / Hiệu lực / Hết hiệu lực) · CR liên quan*. `plan.md` thêm dòng *Trạng thái kế hoạch: đang làm / xong / bỏ*.
6. **Hết hiệu lực không đứng cạnh bản đúng:** đổi trạng thái + dòng *"Thay bằng: <liên kết>"*, rồi dời vào `luu-tru/` của chính phân hệ đó (`doc/erp/<phan-he>/luu-tru/`) hoặc `doc/v1/` nếu là của V1.
7. **Sổ không dời, không chẻ:** `change-log*.md`, `nhat-ky-task.md` giữ đúng đường dẫn (script đồng bộ Dự án, skill, bộ nhớ agent đều đọc).
8. **Kế hoạch xong thì rút ý:** quyết định, luật, bẫy còn giá trị → `chuc-nang/` hoặc `tai-lieu-ky-thuat/` của phân hệ (luật cho người viết mã → `.claude/rules/`); thư mục kế hoạch giữ lại trong `plans/` của phân hệ với trạng thái *xong*.
9. **Tệp không phải chữ** để trong `du-lieu/` của phân hệ (hoặc `doc/v1/du-lieu/`); tệp dựng lại được (PDF xuất từ md) không commit.
10. **Dời bằng `git mv`**, sửa mọi chỗ trỏ tới trong cùng commit. **Bài kiểm tự động** quét `doc/`: liên kết hỏng, tên sai luật, phân hệ thiếu `README.md`, tệp lẻ ở cấp `doc/`.

---

## 4. Bảng dời

| Hiện tại | Tới |
|---|---|
| `doc/erp/00-ke-hoach-theo-module.md` | `doc/plans/00-ke-hoach-theo-module.md` |
| `doc/erp/tai-lieu-ky-thuat/*` (kiến trúc v2, từ điển dữ liệu, danh sách màn), `technical-design.md`, `thiet-ke-ky-thuat-chi-tiet.md`, `so-do-ky-thuat.md` | `doc/tai-lieu-ky-thuat/kien-truc/` |
| `doc/phan-quyen/Thiet_Ke_Phan_Quyen.md`, `Requirement_VaiTro.md` | `doc/tai-lieu-ky-thuat/phan-quyen/` (đổi tên kebab); `Plan_*`, `Test_*` → `doc/v1/` |
| `quy-trinh-nhanh-va-deploy.md`, `gioi-han-tai-nguyen-docker.md`, `so-ghi-nhan-loi-bao-mat.md`, `ra-soat-*`, `danh-gia-chat-luong-backend.md`, `vps-dev-tai-khoan-ida.md` | `doc/tai-lieu-ky-thuat/van-hanh/` |
| `mo-hinh-du-lieu-san-pham.md` | `doc/erp/mat-hang/tai-lieu-ky-thuat/` (CLAUDE.md trỏ tới — sửa cùng commit) |
| `tdd-redesign-kho.md` | `doc/erp/kho/tai-lieu-ky-thuat/` |
| `tdd-bao-cao-thuc-hien-ycbg.md` | `doc/erp/thu-mua/tai-lieu-ky-thuat/` |
| `doc/tai-lieu-chuc-nang/01–08, 12, 19` | `doc/erp/thu-mua/chuc-nang/` |
| `doc/tai-lieu-chuc-nang/14, 15` | `doc/erp/van-thu/chuc-nang/` |
| `doc/tai-lieu-chuc-nang/16-du-an-cong-viec` | `doc/erp/cong-viec/chuc-nang/` |
| `doc/tai-lieu-chuc-nang/17-nghi-phep`, `18-dat-phong-hop` | `doc/erp/hrm/chuc-nang/` |
| `doc/tai-lieu-chuc-nang/16-dat-xe`, `doc/dat-xe-duyet-dau/`, `doc/dong-bo-dat-xe-duyet-dau/` | `doc/erp/dat-xe/` (`chuc-nang/`, `plans/`, `tai-lieu-ky-thuat/dong-bo-app-cu/`) |
| `doc/tai-lieu-chuc-nang/17-duyet-dau`, `doc/duyet-dau/` | `doc/erp/duyet-dau/` |
| `doc/tai-lieu-chuc-nang/09, 10, 11, 13` | `doc/erp/nen-tang/chuc-nang/` |
| `doc/erp/hrm/*.md` hiện có | `doc/erp/hrm/chuc-nang/` (bản chức năng) hoặc `tai-lieu-ky-thuat/`; `doc/erp/tham-khao-hrm/` → `doc/erp/hrm/nghien-cuu/` |
| `doc/erp/item, inventory, receiving, delivery, batch-serial` | `mat-hang, kho, nhan-hang, xuat-hang, lo-serial` (`00-nghien-cuu-*` → `nghien-cuu/`) |
| `doc/erp/nghien-cuu/erpnext/` | tách theo phân hệ: phần HRM → `hrm/nghien-cuu/`, mua hàng – kho → `thu-mua/` + `kho/nghien-cuu/`; báo cáo chung `12-muc-do-…` → `doc/plans/` |
| `doc/erp/tai-lieu-ai/` | `doc/erp/tro-ly-ai/` |
| `plans/<kế hoạch>` ở gốc repo, `frontend-v2/plans/*` | `doc/erp/<phan-he>/plans/<kế hoạch>` theo phân hệ chính của kế hoạch; kế hoạch nhiều phân hệ → `doc/plans/`; `plans/reports/` lẻ → theo phân hệ |
| `doc/huong-dan-su-dung/van-ban/*.pdf` | `doc/erp/van-thu/du-lieu/` (đổi tên tệp có dấu và khoảng trắng) |
| `doc/yeu-cau/`, `doc/testcase/`, `doc/thiet-ke/`, `doc/chung/`, `doc/sheet/`, `doc/datamau/`, `TASKS.md`, `task-process.md` | `doc/v1/…` (`datamau` có 2 chỗ trong mã trỏ tới — sửa cùng commit) |
| `doc/testcase-bao/` | `doc/erp/thu-mua/kiem-thu/` (vẫn dùng cho V2) |
| `doc/danh-sach-tinh-nang.xlsx` | `doc/v1/du-lieu/` |

---

## 5. Lộ trình

| Bước | Việc | Rủi ro |
|---|---|---|
| **P0** | Người chủ chốt cấu trúc + câu ở mục 6; báo anh Dược trước (anh đang viết nhiều ở `hrm/` và `plans/` gốc) | — |
| **P1** | Viết `quy-dinh-tai-lieu.md`; đổi luật cho agent ghi kế hoạch vào `doc/erp/<phan-he>/plans/` (CLAUDE.md, AGENTS.md, skill); bài kiểm tự động ở chế độ **chỉ báo** | Thấp |
| **P2** | Dời phần chung và V1: `tai-lieu-ky-thuat/` ba nhóm con, `doc/plans/`, `doc/v1/`, thư mục tiếng Anh. Sửa chỗ trỏ bằng script thay chuỗi, chạy bài kiểm liên kết | Thấp–vừa: cuối ngày, một commit mỗi nhóm |
| **P3** | Dời từng phân hệ về khuôn (mỗi phân hệ một commit, kèm `README.md`): thu mua, kho, mặt hàng, văn thư, đặt xe, duyệt dấu, công việc, diễn đàn, hải quan… **HRM làm cùng anh Dược** | Vừa: đụng bài HDSD / gói tri thức AI có trỏ đường — chạy lại `seed_help_*` trên dev |
| **P4** | Dời `plans/` gốc và `frontend-v2/plans/` về phân hệ, rút ý các kế hoạch đã xong | Thấp |
| **P5** | Bài kiểm sang chế độ **chặn**; skill `recap-hom-qua` đọc thêm *tài liệu sai luật mới phát sinh* | Thấp |

Ước lượng: P1–P5 khoảng 2–3 ngày công của một agent, làm xen kẽ được.

**Sau khi dời phải sửa luôn:** CLAUDE.md, AGENTS.md, `.claude/rules/*`, các skill, `doc/README.md`, các bài HDSD có liên kết tài liệu, script `sync_task_journal.py` (nếu đọc đường dẫn), bộ nhớ của agent có đường dẫn cũ.

---

## 6. Đã chốt 03/11/2026

1. Khuôn con `chuc-nang / tai-lieu-ky-thuat / nghien-cuu / plans / kiem-thu / du-lieu` — giữ như đề xuất.
2. Kế hoạch xong: **giữ** trong `plans/` của phân hệ, ghi trạng thái *xong*, sau khi rút ý.
3. Tệp nhị phân: **giữ trong git** ở `du-lieu/` (chuyển kho tệp tính sau nếu repo phình).
4. Người giữ `README.md`: HRM anh Dược; thu mua, kho, mặt hàng, CRM đại ca và các agent; A1 chạy bài kiểm và nhắc.
5. Luật chung gom về **một tệp** `.claude/rules/chung-dat-ten-va-quy-uoc.md` + mục lục `doc/tai-lieu-ky-thuat/quy-dinh/README.md` (mục 2.2).

6. **Mỗi phân hệ bắt buộc 4 tài liệu:** `README.md`, `chuc-nang/01-yeu-cau-chuc-nang.md`, `chuc-nang/02-yeu-cau-phi-chuc-nang.md`, `tai-lieu-ky-thuat/api.md` — khuôn ở `doc/tai-lieu-ky-thuat/quy-dinh/mau/`, luật ở `.claude/rules/chung-tai-lieu.md`.
7. **Trang `/docs` (Swagger) giữ mở** trên dev và prod; đường API mới / vừa sửa phải có docstring tiếng Việt + `tags` (luật ở `.claude/rules/chung-dat-ten-va-quy-uoc.md` mục 3).

### Câu hỏi gốc (để tra)


1. **Khuôn con của phân hệ:** `chuc-nang/ · tai-lieu-ky-thuat/ · nghien-cuu/ · plans/ · kiem-thu/ · du-lieu/` — đủ chưa, có muốn đổi tên nào không?
2. **Kế hoạch xong:** giữ trong `plans/` của phân hệ với trạng thái *xong* (đề xuất), hay xóa sau khi rút ý?
3. **Tệp nhị phân** (xlsx, pdf nguồn): giữ trong git hay chuyển lên kho tệp (Drive / tab Văn bản của ERP)?
4. **Người giữ `README.md` từng phân hệ:** HRM anh Dược; thu mua, kho, mặt hàng, CRM đại ca và các agent; A1 chạy bài kiểm và nhắc.
