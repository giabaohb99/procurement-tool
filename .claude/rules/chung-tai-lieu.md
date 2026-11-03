---
paths:
  - "doc/**"
---
# Luật viết và xếp tài liệu (`doc/`)

> Nạp khi sửa bất kỳ tệp nào trong `doc/`. Nguồn: đề xuất 1.2 đã chốt 03/11/2026
> (`doc/tai-lieu-ky-thuat/de-xuat-to-chuc-lai-tai-lieu.md`, mục 2–3), bao-CR-712. Mục lục mọi luật / skill / agent:
> `doc/tai-lieu-ky-thuat/quy-dinh/README.md`.

## Khuôn thư mục

```
doc/
├── README.md              bản đồ duy nhất: muốn biết gì → đọc đâu
├── plans/                 kế hoạch TỔNG (nhiều phân hệ, lộ trình toàn hệ, đợt phát hành)
├── tai-lieu-ky-thuat/     tài liệu CHUNG: sổ change-log*, nhat-ky-task, quy-dinh/, kien-truc/, phan-quyen/, van-hanh/
├── erp/<phan-he>/         MỘT thư mục MỘT phân hệ V2 (nen-tang = phần dùng chung giữa phân hệ)
│   ├── README.md          phạm vi · trạng thái · người phụ trách · mục lục · CR liên quan
│   ├── chuc-nang/         người dùng / BA đọc: màn nào làm gì, luật nghiệp vụ
│   ├── tai-lieu-ky-thuat/ thiết kế riêng: bảng, API, luồng, bẫy
│   ├── nghien-cuu/        so sánh ERPNext / sản phẩm khác, khảo sát, câu hỏi chờ chốt
│   ├── plans/             <YYMMDD>-<slug>[-<mã CR>]/plan.md + phase-*.md + reports/
│   ├── kiem-thu/          kịch bản kiểm thử tay
│   ├── du-lieu/           tệp nguồn (xlsx, pdf, json)
│   └── luu-tru/           tài liệu hết hiệu lực của phân hệ
├── agent-hub/  he-agent/  (cùng khuôn con như một phân hệ)
└── v1/                    mọi thứ thời Mini Tool Thu Mua V1
```

Khuôn con chỉ tạo **khi có nội dung** — không dựng thư mục rỗng cho đủ bộ.

## Tài liệu bắt buộc của mỗi phân hệ (người chủ chốt 03/11/2026)

Mỗi `doc/erp/<phan-he>/` (kể cả `agent-hub/`) phải có đủ bốn tệp dưới; chưa viết xong thì vẫn tạo tệp với trạng thái
*Nháp* và ghi rõ phần còn thiếu. Khuôn mẫu ở `doc/tai-lieu-ky-thuat/quy-dinh/mau/` — chép khuôn rồi điền, đừng tự chế bố cục.

| Tệp | Trả lời câu hỏi | Khuôn |
|---|---|---|
| `README.md` | Phân hệ này là gì, tới đâu, ai giữ, đọc gì trước | `mau/mau-readme-phan-he.md` |
| `chuc-nang/01-yeu-cau-chuc-nang.md` | Làm được gì: từng chức năng (mã `CN-<phân hệ>-NN`), ai dùng, luật nghiệp vụ, màn hình, trạng thái *có / đang làm / chưa* | `mau/mau-yeu-cau-chuc-nang.md` |
| `chuc-nang/02-yeu-cau-phi-chuc-nang.md` | Chạy tốt cỡ nào: hiệu năng, phân quyền và dữ liệu nhạy cảm, lưu trữ và sao lưu, nhật ký, giới hạn đầu vào, đồng thời, tích hợp, pháp lý (mã `PCN-<phân hệ>-NN`) | `mau/mau-yeu-cau-phi-chuc-nang.md` |
| `tai-lieu-ky-thuat/api.md` | Gọi gì: mỗi đường API một dòng — phương thức, đường, mục đích, quyền (`entity.action`), phạm vi, dữ liệu vào / ra chính, lỗi riêng, ai gọi (màn nào, công cụ MCP nào) | `mau/mau-tai-lieu-api.md` |

- Trang **`/docs`** (Swagger do FastAPI tự sinh) **giữ mở** trên dev và prod (người chủ chốt 03/11/2026) — đó là bản tra
  cứu đầy đủ, sinh từ mã. `api.md` không chép lại toàn bộ tham số: nó giữ phần Swagger không nói được (quyền, phạm vi,
  luật nghiệp vụ, ai gọi) và trỏ sang nhóm (tag) tương ứng trên `/docs`.
- Thêm / đổi / bỏ chức năng hay đường API thì sửa `01`, `02`, `api.md` **trong cùng commit** với mã.

## Mười luật

1. **Riêng thì về phân hệ, chung thì lên cấp `doc/`.** Tài liệu chỉ nói về một phân hệ → `doc/erp/<phan-he>/<loại>/`.
   Nói về nhiều phân hệ / toàn hệ → `doc/plans/` hoặc `doc/tai-lieu-ky-thuat/`.
2. **Một sự thật một chỗ.** Chỗ khác cần thì liên kết, không chép.
3. **Thư mục phân hệ nào cũng có `README.md`** (phạm vi, trạng thái, người phụ trách, mục lục). Thêm tệp là thêm dòng
   mục lục trong cùng commit.
4. **Đặt tên:** chữ thường, không dấu, nối gạch ngang; tiền tố số `NN-` theo thứ tự đọc, không trùng số trong một thư
   mục. Cấm `CamelCase`, `snake_case`, chữ HOA. Thư mục kế hoạch: `<YYMMDD>-<slug>[-<mã CR>]/`.
5. **Đầu mỗi tài liệu một bảng nhỏ:** *Bản · Ngày · Người phụ trách · Trạng thái (Nháp / Hiệu lực / Hết hiệu lực) · CR
   liên quan*. `plan.md` thêm dòng *Trạng thái kế hoạch: đang làm / xong / bỏ*.
6. **Hết hiệu lực không đứng cạnh bản đúng:** đổi trạng thái + dòng *"Thay bằng: <liên kết>"*, rồi dời vào `luu-tru/`
   của chính phân hệ đó (`doc/erp/<phan-he>/luu-tru/`) hoặc `doc/v1/` nếu là của V1.
7. **Sổ không dời, không chẻ:** `change-log*.md`, `nhat-ky-task.md` giữ đúng đường dẫn (script đồng bộ Dự án, skill, bộ
   nhớ agent đều đọc).
8. **Kế hoạch xong thì rút ý:** quyết định, luật, bẫy còn giá trị → `chuc-nang/` hoặc `tai-lieu-ky-thuat/` của phân hệ
   (luật cho người viết mã → `.claude/rules/`); thư mục kế hoạch giữ lại trong `plans/` của phân hệ với trạng thái *xong*.
9. **Tệp không phải chữ** để trong `du-lieu/` của phân hệ (hoặc `doc/v1/du-lieu/`); tệp dựng lại được (PDF xuất từ md)
   không commit.
10. **Dời bằng `git mv`**, sửa mọi chỗ trỏ tới trong cùng commit (CLAUDE.md, `.claude/rules`, skill, agent,
    `seed_help_*`, gói tri thức AI, script, `doc/README.md`). Chạy bài kiểm tự động trước khi đẩy:
    `python backend/scripts/kiem_tai_lieu.py` — liên kết hỏng, tên sai luật, phân hệ thiếu `README.md`, tệp lẻ cấp
    `doc/`, skill / luật chưa có trong mục lục.

## Kế hoạch của agent

Kế hoạch làm việc ghi vào **`doc/erp/<phan-he>/plans/<YYMMDD>-<slug>[-<mã CR>]/`** (phân hệ chính của kế hoạch); kế
hoạch nhiều phân hệ / toàn hệ ghi **`doc/plans/`**. **Không** ghi vào `plans/` ở gốc repo hay `frontend-v2/plans/`
nữa (hai chỗ đó đang được dời về phân hệ, bao-CR-712 P4).

## Không thuộc `doc/`

Công cụ đọc thẳng theo đường dẫn cố định nên giữ nguyên chỗ: `CLAUDE.md`, `AGENTS.md`, `.claude/rules/`,
`.claude/skills/`, `.claude/agents/`, `frontend-v2/docs/ui/`, `backend/app/modules/ai_skill/seed_handbook/`,
`README.md` của thư mục mã, bài HDSD trong `seed_help_*.py`.
