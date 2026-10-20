# Phase 04 — D0d: Nhóm chỉ số 3.8 «Dùng AI»

## Context links
- `doc/erp/22-ai-ke-hoach-phan-viec.md` §5 «Phần AI» + §7 đợt A0 (Agent 4: `tab_ai_usage_daily` qua cổng B + cờ `via_ai`)
- Nguồn hiện có: `backend/app/modules/assistant/change_model.py` (`tab_assistant_change`: user_id, entity, entity_id, action `ChangeAction`, source `ChangeSource` 0/1 TELEGRAM/2 WEB/3 ZALO/4 MCP)
- `usage_profile/snapshot_sources.py:154-157`, `snapshot_metrics_misc.py:19-20` (`assistant_questions`, `assistant_changes`), `metric_catalog.py` mục 3.4
- agent_hub (DB riêng): `tab_agent_mcp_call(user_id, client_name, tool, status)`, `tab_agent_intent(user_id, channel WEB/TELEGRAM/ZALO)`

## Overview
- P2 · **1 ngày** phần đọc được ngay + **0,5 ngày** nối khi A0 xong · pending · cần **CR-651 đã gộp** (cùng `usage_profile/metric_*` + `modules/report/**`).
- Thêm 8 khóa chỉ số mục **3.8** vào snapshot tuần + một khối trên màn Hồ sơ (khóa 14).

## Key insights
- Từ 19/10 dữ liệu hội thoại (web, Telegram) và nhật ký MCP nằm ở **DB agent_hub**; bộ chỉ số chỉ đọc DB ERP → `assistant_questions` gần như luôn 0. Kênh/ứng dụng/nhóm công cụ **phải chờ A0** đẩy `tab_ai_usage_daily`.
- **«Phiếu do AI soạn» đọc được NGAY**, một phần: `tab_assistant_change` (DB ERP) có `action=CREATE/SUBMIT` + `entity` + `entity_id`. Hạn chế:
  MCP chế độ tách bị ghi `source=TELEGRAM` (cổng B gán cứng `GATEWAY_SOURCE`, `agent_gateway/controller.py:29`); chế độ nhúng `source=0`; YCTT chỉ web; đặt xe không có nháp.
  → đếm **tổng** phiếu AI soạn tin được, **tách kênh thì chưa** cho tới khi A0 sửa `source`.
- Không lấy được «hay nhờ AI làm việc gì» theo nội dung câu hỏi (§7.4 cấm văn bản tự do) → dùng **nhóm công cụ** (`mcp_settings.GROUPS`, A0 đổi sang mã số) + **loại phiếu** (`entity`) của `tab_assistant_change`.
- Hành động AI làm hộ đang bị đếm như người tự làm (`actor_kind=1`). Cờ `via_ai` của A0 giải quyết; D0d chỉ ĐỌC cờ đó, không tự thêm.

## Requirements
- Theo người, cửa sổ 4 tuần như snapshot hiện tại: dùng AI qua kênh nào, nhiều hay ít, nhóm việc hay nhờ, số phiếu AI soạn, tỷ lệ so với tự lập, số lần bị từ chối quyền.
- Không chuyển/không lưu nội dung câu hỏi. Chỉ số + mã.

## Architecture
**Hợp đồng đề xuất gửi Agent 4 cho A0** (A0 sở hữu model + migration + đường cổng B; D0d chỉ đọc):
`tab_ai_usage_daily(id, day DATE, user_id BIGINT, channel SMALLINT AiChannel, client SMALLINT AiClient, tool_group SMALLINT AiToolGroup (0 = hỏi đáp không gọi công cụ),
uses INT, denied INT, errors INT, drafts_created INT, drafts_confirmed INT)` UNIQUE `(day, user_id, channel, client, tool_group)`, INDEX `(day)`.
Mã ở `backend/app/core/ai_usage_codes.py` (thuần stdlib, đăng ký `code_sets`): `AiChannel` 1 WEB · 2 TELEGRAM · 3 ZALO · 4 MCP; `AiClient` 0 không áp dụng · 1 CLAUDE · 2 CHATGPT · 9 KHÁC (map từ `client_name`);
`AiToolGroup` = bản số của `mcp_settings.GROUPS`. Yêu cầu A0 kèm: sửa `source` MCP ở `draft_create`/cổng B; cờ `via_ai` + kênh trong `tab_audit_log`.

**Khóa chỉ số mới** (`metric_catalog.py`, mục `"3.8"`, khóa là định danh cố định):
| Khóa | Đơn vị | Pha | Hướng | Nguồn |
|---|---|---|---|---|
| `ai_uses` | count | 3 | 0 | Σ uses (A0) |
| `ai_active_days` | count | 3 | 0 | số ngày có uses>0 (A0) |
| `ai_main_channel` | code (AiChannel×10+AiClient) | 3 | 0 | kênh+ứng dụng nhiều lượt nhất (A0) |
| `ai_mcp_share` | ratio | 3 | 0 | uses MCP / ai_uses (A0) |
| `ai_top_tool_group` | code | 3 | 0 | nhóm công cụ nhiều lượt nhất (A0) |
| `ai_denied` | count | 3 | -1 | Σ denied (A0) — gợi ý cấp quyền |
| `ai_docs_drafted` | count | 1 | 0 | `tab_assistant_change` action ∈ {CREATE, REUSE} và entity ∈ phiếu theo dõi (đọc được NGAY) |
| `ai_docs_share` | ratio | 1 | 0 | `ai_docs_drafted` / `docs_created` (đã có) |
Pha 3 = «cần A0»: trước A0 các khóa này nằm ở `unmeasured` với lý do `NOT_COLLECTED` (không ghi 0 — đúng luật snapshot).
Thêm đơn vị `code` vào docstring đơn vị nếu chưa có; FE hiển thị nhãn qua bộ mã sinh.
`assistant_questions` (3.4): giữ khóa, đổi nguồn sang `tab_ai_usage_daily(channel=WEB, tool_group=0)` khi A0 xong (không đổi tên khóa).

**Luồng:** `snapshot_sources_ai.py` (tệp mới, 2 truy vấn cố định: GROUP BY user trên `tab_ai_usage_daily` cửa sổ 4 tuần; GROUP BY user trên `tab_assistant_change`) →
`snapshot_metrics_ai.py` (thuần) → `snapshot_builder._user_partials` merge → JSON snapshot (schema v1, thêm khóa = cộng thêm).
Bảng A0 chưa tồn tại → `inspect(...).has_table` một lần/lượt dựng; không có thì mọi khóa pha 3 = `NOT_COLLECTED`.

## Related code files
Tạo BE: `backend/app/modules/usage_profile/snapshot_sources_ai.py` · `snapshot_metrics_ai.py`.
Sửa BE (sau CR-651): `usage_profile/metric_catalog.py` (8 khóa) · `snapshot_builder.py` (gọi nguồn + merge) · `snapshot_sources.py` (chỉ gọi hàm mới) ·
`plans/261019-1450-tracking-ho-so-lam-viec-cr641/metric-definitions.md` (thêm mục 3.8).
Không tạo: model/migration `tab_ai_usage_daily` (A0). Nếu A0 trễ: D0d vẫn giao 2 khóa pha 1.
Sửa FE (sau CR-651): `modules/report/config/usage-metric-labels.ts`, `usage-metric-definitions.ts` (test sẵn có so khớp với `metric_catalog.py`) ·
tạo `modules/report/components/usage-profile/usage-ai-section.tsx` · gắn vào `usage-profile-detail-page.tsx`.

## Implementation steps
1. Gửi hợp đồng bảng + 3 bộ mã cho Agent 4 (qua lead); chốt trước khi A0 viết migration.
2. Khóa 3.8 vào catalog + định nghĩa FE (test `usage-metric-definitions.test.ts` bắt thiếu).
3. Nguồn + tính `ai_docs_drafted`, `ai_docs_share` (pha 1) — giao được ngay.
4. Nhánh A0: nguồn `tab_ai_usage_daily` có gác `has_table`; tính 6 khóa pha 3.
5. Khối «Dùng AI» trên hồ sơ: kênh chính, lượt/tuần, nhóm việc, phiếu AI soạn, bị từ chối quyền.
6. Khi A0 xong: đổi nguồn `assistant_questions`; chạy lại snapshot 4 tuần gần nhất (script backfill có sẵn của CR-641).

## Todo
- [ ] hợp đồng A0 gửi lead
- [ ] 8 khóa + định nghĩa
- [ ] nguồn pha 1 (`tab_assistant_change`)
- [ ] nguồn pha 3 (`tab_ai_usage_daily`, gác has_table)
- [ ] khối FE
- [ ] đổi nguồn `assistant_questions` sau A0

## Tests
Backend `test/backend/test_chi_so_dung_ai_d0.py`: không có bảng A0 → 6 khóa ở `unmeasured=NOT_COLLECTED`, 2 khóa pha 1 có số;
có bảng (tạo trong fixture SQLite) → kênh chính/tỷ lệ MCP/nhóm công cụ đúng; `ai_docs_share` khi `docs_created=0` → `NOT_APPLICABLE`;
đếm truy vấn nguồn AI = 2 bất kể số người; JSON snapshot không chứa chuỗi tự do.
Vitest: `usage-metric-definitions.test.ts` (đã có), `usage-ai-section.test.tsx` (chưa thu → hiện «chưa thu thập», không hiện 0).

## Success criteria
- Hồ sơ một người có khối «Dùng AI»; trước A0 thấy «Phiếu AI soạn: N (x% số phiếu lập)», còn lại «Chưa thu thập»; sau A0 đủ 8 chỉ số.

## Risk assessment
| Rủi ro | K×A | Giảm thiểu |
|---|---|---|
| A0 trễ / đổi hợp đồng | Cao × TB | Tách pha 1/pha 3; gác `has_table`; hợp đồng chốt trước |
| Kênh MCP ghi nhầm Telegram trong `tab_assistant_change` | Chắc × TB | Không tách kênh từ nguồn này; ghi chú ở định nghĩa |
| Đếm trùng «phiếu AI soạn» (CREATE rồi REUSE cùng phiếu) | TB × Thấp | Đếm `DISTINCT (entity, entity_id)` |
| Xung đột CR-651 | Cao × TB | Làm sau khi gộp |

## Security
Chỉ khóa 14 xem (giữ nguyên). Không tên công cụ chi tiết, không nội dung câu hỏi; chỉ mã nhóm. Dữ liệu A0 vào qua cổng B có ký (Agent 4).

## Rollback
Bỏ merge `snapshot_metrics_ai` → khóa 3.8 biến mất khỏi snapshot mới; snapshot cũ giữ khóa thừa vô hại (FE bỏ qua khóa lạ).

## Next steps
A1 (Agent 4) có thể đọc 3.8 qua công cụ `usage_profile` (chỉ người có khóa 14 — doc 22 §6).
