---
name: them-cong-cu-mcp
description: Thêm hoặc đổi một công cụ cho cổng MCP / Trợ lý web / bot của DEGO ERP — đủ mọi chỗ phải khai (sổ công cụ, cổng MCP, nhóm cấu hình G7, bộ lọc công cụ, nhãn ý định, cổng B, bài kiểm canh cửa). Dùng mỗi khi tạo tool mới trong assistant/tools/ hay agent_hub/mcp.py, hoặc đổi tên / tham số / kết quả của tool cũ.
---

# Thêm một công cụ cho AI

## Khi nào dùng
Thêm tool mới hay đổi tool cũ cho Trợ lý web, bot (core_v2) hoặc cổng MCP (ChatGPT, Claude…). Sót một chỗ khai là bài
kiểm canh cửa đỏ — hoặc tệ hơn, tool chạy được nhưng lọt quyền / lọt khóa chỉ đọc.

## Các bước
1. **Viết spec** ở `backend/app/modules/assistant/tools/<khu>_tool.py`: `ToolSpec(name, description, parameters, handler)`.
   Handler nhận `ctx` (`ctx.db`, `ctx.user`, `ctx.can(entity)`), tự gác quyền: `ctx.can` + `apply_scope` / `get_scoped`;
   thiếu quyền trả `base.denied(...)`, không trả rỗng lặng lẽ.
2. **Đăng ký** trong `assistant/tools/__init__.py` → `_active_specs()`.
3. **Kết quả theo chuẩn §5.6** (`doc/erp/21-kho-skill-ai-mcp.md`): đường dẫn tuyệt đối, `total / page / has_more` + `note`,
   tiền có `currency` + trước / sau VAT, trạng thái mã + nhãn, gọn. Dài thì chia trang có `next_offset` (ai-CR-228).
4. **Cổng MCP** (`agent_hub/mcp.py`):
   - chỉ đọc → thêm vào `READ_TOOLS` (khóa chỉ đọc mới thấy); ghi → `is_write_tool` phải trả True, đi khuôn nháp →
     `confirm_draft`;
   - không mở qua MCP → `HIDDEN`; bỏ khỏi MCP nhưng giữ cho Trợ lý → `MCP_RETIRED` kèm tên thay thế;
   - đọc nhiều dòng → `ROW_BUDGET_TOOLS`; có kết quả cấu trúc → `STRUCTURED_TOOLS`;
   - tool RIÊNG của cổng (không qua sổ Trợ lý) → `GATEWAY_READ_TOOLS` / `SKILL_TOOL_DEFS`; trùng tên với sổ Trợ lý thì
     lọc bản sổ khỏi `list_tools` (ai-CR-220).
5. **Nhóm cấu hình G7** (`agent_hub/mcp_settings.py` → `GROUPS`): tool phải thuộc ĐÚNG MỘT nhóm, nhóm nhạy cảm để tắt
   mặc định (đại ca chốt Q4).
6. **Bộ lọc công cụ** (`assistant/tool_router.py`): thêm vào nhóm có regex chữ đã bỏ dấu, hoặc `CORE` nếu cần mọi câu.
   Câu thật của người dùng phải khớp nhóm (ai-CR-224: «sự kiện» không nạp nhóm lịch → bot nói sai «không xóa được»).
7. **Nhãn ý định** `agent_hub/intent_ledger.py` → `TOOL_SUB`.
8. **Chạy ở đâu**: tool đọc ERP chạy phía ERP qua cổng B `/tools/run` — không phải làm gì. Tool chạy NGAY trong dịch vụ
   AI (Google, sổ nhớ, nhóm chat…) → module phải nằm trong `erp.LOCAL_TOOL_MODULES`. Cần dữ liệu ERP mới thì thêm cặp
   `_Local` / `_Remote` trong `agent_hub/erp.py` + đường `agent_gateway/controller.py` (chữ ký cổng B, user lấy từ chữ ký).
9. **Nhật ký thao tác**: không gọi thẳng `core.audit.record` ở mã chạy trong dịch vụ AI — dùng `agent_hub.erp.audit`.
10. **Bài kiểm canh cửa** — chạy và sửa bảng khai, KHÔNG nới luật:
    - `test_assistant_pham_vi_doc.py`: phân loại tool (`TOOL_GHI / TOOL_CHUNG_TU / TOOL_DANH_MUC / TOOL_KHONG_PHAM_VI`)
      + đếm tổng số tool (sửa con số kèm dòng chú thích);
    - `test_pham_vi_bo_may_duyet_xuyen_suot.py` → `E2_CUA_GAC_CUA_TUNG_TOOL` (một câu: lọc bằng gì);
    - `test_agent_hub_y_dinh_tu_nho.py` (nhãn TOOL_SUB), `test_agent_hub_cau_hinh_mcp_cr216.py` (đúng một nhóm);
    - `test_agent_hub_cong_mcp_cr207.py` (khóa chỉ đọc), `test_agent_hub_ai_cua_toi_cr213.py`;
    - schema ghi mới → `test_canh_do_dai_o_chu_cr538.py` (TARGETS / NO_TARGET); mã hành động mới →
      `test_bo_ma_hanh_dong_cr358.py`; `db.get(` mới trong controller → `test_pham_vi_duong_vong.py`;
      controller mới không gọi `apply_scope` → `test_pham_vi_luat_bat_bien.py` (BB4, lý do thật).
11. **Bài kiểm của tool**: thiếu quyền → denied; ngoài phạm vi và id không tồn tại trả CÙNG một câu; khóa chỉ đọc không
    thấy tool ghi; tham số lạ / quá dài không vỡ.
12. **Tài liệu**: `doc/agent-hub/06-cong-mcp.md` (bảng công cụ + hợp đồng), một dòng `change-log-ai.md`, một mục
    `nhat-ky-task.md` (câu tiếng Việt trọn vẹn) rồi `python backend/scripts/sync_task_journal.py --env-file …`.

## Bẫy đã gặp
- 16/10 ai-CR-207: `erp.tool_defs(db)` không kèm user → chế độ tách gọi cổng B với user rỗng, danh sách cụt.
- 17/10 ai-CR-208/210/211: quên `TOOL_SUB`, bảng E2, phân loại `db.get` → đỏ ở lượt gộp sau (vá ai-CR-217).
- 17/10 ai-CR-216: khóa cấu hình mới chưa vào `SETTING_RAW_KEYS` → lưu G7 hỏng ở chế độ service.
- 19/10 ai-CR-220: thêm tool trùng tên vào sổ Trợ lý → MCP liệt kê hai lần; phải lọc ở `list_tools`.
- 19/10 ai-CR-226: tool chạy tại chỗ ghi audit vào DB `agent_hub` (không có bảng) → mất trắng dấu vết.
- 19/10 ai-CR-228: kết quả ~35k ký tự → ChatGPT bảo «không trả về nội dung»; câu dặn «đừng đọc lại nguyên văn» làm AI
  tưởng không được dùng — chia trang + viết câu dặn cho phép dùng.
- 19/10 ai-CR-227: model bịa link / sai thứ / tự soạn lại dữ liệu từ trí nhớ → để MÁY làm (tách dữ liệu, `reply_guard`),
  không trông vào lời dặn.
- Bash heredoc ăn dấu `\` (regex, `\n`) — sửa bằng Edit hoặc tệp script, rồi đọc lại dòng vừa sửa.

## Kiểm xong
- Bài kiểm tool + các bài canh cửa ở bước 10 xanh (`docker exec agenthub-agent-api-1 sh -c "python -m pytest … -n 3"`).
- Nạp được cả ba chế độ (skill `ba-che-do-agent`, bước Kiểm).
- `tools/list` qua khóa chỉ đọc và khóa được ghi ra đúng; nhật ký cổng có dòng `tools/call` của tool mới.
