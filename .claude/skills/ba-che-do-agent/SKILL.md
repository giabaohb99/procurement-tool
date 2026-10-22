---
name: ba-che-do-agent
description: Ba chế độ chạy dịch vụ AI của DEGO ERP (AGENT_MODE nhúng / service / erp) — mã nào chạy ở tiến trình nào, đọc DB nào, biến .env nào, bẫy đã gặp (mất audit, issuer OAuth, cache trạm), và cách thử cả ba trước khi đẩy. Dùng khi sửa agent_hub / assistant / ai_skill / agent_gateway, khi dựng dịch vụ AI mới, hoặc khi một tính năng chạy ở local nhưng hỏng ở dev / prod.
---

# Ba chế độ của dịch vụ AI

## Khi nào dùng
Mọi thay đổi trong `agent_hub/`, `assistant/`, `ai_skill/`, `agent_gateway/`; dựng / soát `.env.agent`; lỗi kiểu «local
chạy, dev hỏng».

## Bản đồ
| `AGENT_MODE` | Ai chạy | DB | Đường vào |
|---|---|---|---|
| (trống) nhúng | một tiến trình ERP làm hết (bot, MCP, Trợ lý) | DB ERP chứa cả `tab_agent_*` | `app/main.py` nhánh else |
| `service` | dịch vụ AI riêng: `app/agent_main.py`, poller, worker, beat (`docker-compose.agent-hub.yml`) | DB `agent_hub` (`migrations_agent`) | ERP proxy sang `http://agent-api:8000` |
| `erp` | ERP chỉ còn cổng B (`agent_gateway/controller.py`) + proxy (`agent_gateway/proxy.py`) | DB ERP | `/api/agent-hub/*`, `/api/assistant/*`, `/api/mcp`, `/api/oauth/*`, `/.well-known/oauth-*` |

- Dịch vụ AI KHÔNG đụng DB ERP: mọi dữ liệu ERP đi `agent_hub/erp.py` → `_Remote` gọi cổng B `/api/agent-gw/*` (chữ ký
  `AGENT_SERVICE_SECRET`, user nằm trong chữ ký). Nhúng thì `_Local` gọi thẳng.
- Công cụ Trợ lý: đọc ERP chạy phía ERP (`/tools/run`); module trong `erp.LOCAL_TOOL_MODULES` chạy ngay trong dịch vụ AI.
- Bảng chỉ có ở DB ERP: `tab_audit_log`, `tab_ai_skill*`, `tab_setting` của ERP. Bảng `tab_agent_*` (khóa MCP, OAuth,
  nhật ký cổng, tin nhắn bot) ở DB `agent_hub` khi tách.
- Beat ở service chỉ giữ lịch tên `agent-*` (`core/celery_app.py`); vòng tốn tiền model có cờ riêng
  (`AGENT_BRIEFS_ENABLED`, `AGENT_SESSION_SUMMARY_ENABLED`, `AGENT_TRIAGE_ENABLED`, `AGENT_AUTO_MEMORY_ENABLED`).

## Biến .env chính (tên biến, KHÔNG ghi giá trị)
- Dịch vụ AI (`.env.agent`): `AGENT_MODE=service`, `DB_*` của `agent_hub`, `JWT_SECRET` TRÙNG ERP (Fernet khóa xem lại +
  chuỗi ký OAuth suy từ đây), `AGENT_GATEWAY_URL` = TÊN CONTAINER api ERP, `AGENT_SERVICE_SECRET`, `AGENT_ERP_URL` = gốc
  công khai (issuer OAuth), `AGENT_TELEGRAM_*`, `AGENT_BOT_NAME`, `R2_*` + `STORAGE_PREFIX` (sao lưu DB agent_hub; đủ
  endpoint + access key + public url mới coi là sẵn sàng).
- ERP chế độ `erp`: `AGENT_MODE=erp`, `AGENT_SERVICE_URL`, `AGENT_SERVICE_SECRET`. Không đặt token bot ở ERP.

## Các bước khi sửa
1. Đọc xem mã mình sửa chạy ở tiến trình nào (bảng trên). Cần dữ liệu ERP từ dịch vụ AI → thêm cặp `_Local` / `_Remote`
   trong `erp.py` + đường cổng B, KHÔNG import model ERP rồi query.
2. Ghi nhật ký thao tác → `agent_hub.erp.audit` (không `core.audit.record`).
3. Thêm bảng / cột `tab_agent_*` → hai migration (ERP + `migrations_agent`), cùng nội dung, «chỉ thêm khi thiếu».
4. Lời nhắc core_v2: phần TĨNH (system) không chứa thứ đổi mỗi lượt; phần theo người (danh mục skill) để CUỐI system;
   phần đổi mỗi lượt vào `turn_context` đầu tin người dùng — trạm cache theo tiền tố công cụ → system → lịch sử.

## Bẫy đã gặp
- 13/10 sự cố sót `change_undo.py` khi `git add` → tiến trình service không nạp được; luôn kiểm nạp cả ba chế độ.
- 15/10 trạm modelapi: đổi một chữ ở system là ghi lại cả bộ đệm (~20k token) — system phải tĩnh.
- 16/10 ai-CR-207: gọi cổng B không kèm user → «Tài khoản không tồn tại», danh sách công cụ cụt ở chế độ tách.
- 19/10 ai-CR-222: issuer OAuth lấy `X-Forwarded-Host` → giả được, và ở chế độ tách thành gốc nội bộ `agent:8001`.
  Nay chỉ lấy `AGENT_ERP_URL`; thiếu thì 503.
- 19/10 ai-CR-223: đường hỏi về tệp không đi core_v2 → không phân luồng model → rơi vào khóa trạm đầu tiên (DeepSeek nghĩ
  hết 8192 token ra nội dung).
- 19/10 ai-CR-226: audit công cụ chạy tại chỗ ghi vào DB `agent_hub` → `tab_audit_log doesn't exist`, mất trắng.
- 19/10 Agent 1 đo: trạm cộng thêm ~40–45k token mỗi lần gọi ngoài phần mình gửi (~10–15k) — xem `cache_read` trong
  `AgentRun.artifact` trước khi kết luận lời nhắc của mình phình.
- Bài kiểm chạy «ERP» và «dịch vụ AI» trong CÙNG tiến trình (cùng `AGENT_MODE`) → phía ERP cũng đi cổng B; đừng khẳng
  định số lượt HTTP chính xác ở bài kiểm tách dịch vụ.

## Kiểm
```bash
for m in embedded erp; do docker exec -e AGENT_MODE=$m agenthub-agent-api-1 sh -c "cd /app && python -c 'import app.main'"; done
docker exec -e AGENT_MODE=service agenthub-agent-api-1 sh -c "cd /app && python -c 'import app.agent_main, app.modules.agent_hub.tasks'"
docker exec agenthub-agent-api-1 sh -c "cd /app && alembic heads; alembic -c alembic_agent.ini heads"   # mỗi chuỗi MỘT đầu
docker exec agenthub-agent-api-1 sh -c "python -m pytest test/backend/test_agent_hub_tach_dich_vu.py -q -p no:cacheprovider"
```
Bài kiểm chế độ tách: dựng FastAPI chứa router cổng B, `AGENT_MODE=service`, giả `erp.requests.request` gọi vào
TestClient (mẫu: fixture `gateway` trong `test_agent_hub_nhat_ky_qua_cong_b_cr226.py`).
