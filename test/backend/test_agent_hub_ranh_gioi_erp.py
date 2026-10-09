"""ai-CR-153 — canh ranh giới bot / ERP.

Ở dev và prod, bot (`modules/agent_hub/`) chạy TÁCH khỏi ERP (`AGENT_MODE=service`, DB riêng, không có bảng phiếu). Mã
phía bot muốn đụng dữ liệu ERP phải đi qua `agent_hub/erp.py` (bản `_Local` + `_Remote`) và một đường cổng B
(`agent_gateway/controller.py`). ai-CR-152: nút «Xác nhận sửa / xóa» trên Telegram import thẳng `confirm_update` rồi
chạy trên DB của bot — mọi bài kiểm khác vẫn xanh vì chúng chạy bot và ERP chung một DB. Bài này đọc mã (không chạy),
nên bắt được loại lỗi đó ngay lúc viết.

Luật: trong `agent_hub/*.py`, import một phân hệ ERP (khác `agent_hub`, `assistant`) chỉ được ở
  - tệp ranh giới: `erp.py` (cửa ra ERP), `draft_create.py` (chạy phía ERP, cổng B gọi);
  - hàm tên đuôi `_local` (bản chạy thẳng trong ERP, cổng B gọi);
  - hoặc đã khai trong `DA_RA` kèm một câu nói vì sao an toàn.
Riêng tool GHI của trợ lý (`update_tool`, `draft_tool`) thì chỉ tệp ranh giới mới được import.
"""
from __future__ import annotations

import ast
from pathlib import Path

import app.modules.agent_hub as _bot_pkg  # noqa: E402 — lấy đúng thư mục mã đang chạy (container gắn backend vào /app)

BOT_DIR = Path(_bot_pkg.__file__).resolve().parent
BOUNDARY_FILES = {"erp.py", "draft_create.py"}
ALLOWED_PREFIXES = ("app.modules.agent_hub", "app.modules.assistant")
WRITE_TOOLS = ("app.modules.assistant.tools.update_tool", "app.modules.assistant.tools.draft_tool")

#  (tệp, phân hệ) đã rà — chỉ thêm khi chắc chắn chế độ service không đi vào đó, kèm lý do.
DA_RA = {
    ("bells.py", "app.modules.notification.model"): "chỉ làm gợi ý kiểu; chuông đọc qua erp.notifications_after",
    ("service.py", "app.modules.department.model"): "nhánh chạy chung; chế độ service đã rẽ ErpUser ngay phía trên",
    ("service.py", "app.modules.employee.model"): "nhánh chạy chung; chế độ service đã rẽ ErpUser ngay phía trên",
    ("controller.py", "app.modules.employee.field_limits"): "chỉ là kiểu chuỗi có trần độ dài, không đụng dữ liệu",
    ("db_backup.py", "app.modules.backup.service"): "dùng lại hàm dump để sao lưu chính DB của bot",
}


def _imports(tree: ast.AST):
    """(tên module đầy đủ, hàm bao quanh) cho mọi câu import; `from a.b import c` cho cả `a.b` lẫn `a.b.c`."""
    out: list[tuple[str, str]] = []

    def walk(node, func: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                walk(child, child.name)
                continue
            if isinstance(child, ast.ImportFrom) and child.module and child.level == 0:
                out.append((child.module, func))
                out.extend((f"{child.module}.{a.name}", func) for a in child.names)
            elif isinstance(child, ast.Import):
                out.extend((a.name, func) for a in child.names)
            walk(child, func)

    walk(tree, "")
    return out


def _violations() -> list[str]:
    bad: list[str] = []
    for path in sorted(BOT_DIR.glob("*.py")):
        if path.name in BOUNDARY_FILES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for name, func in _imports(tree):
            if not name.startswith("app.modules."):
                continue
            if name.startswith(WRITE_TOOLS):
                bad.append(f"{path.name}:{func or '<đầu tệp>'} import {name} — tool GHI của trợ lý chỉ gọi qua erp.py")
                continue
            if name.startswith(ALLOWED_PREFIXES) or func.endswith("_local"):
                continue
            if any(path.name == f and name.startswith(m) for f, m in DA_RA):
                continue
            bad.append(f"{path.name}:{func or '<đầu tệp>'} import {name}")
    return sorted(set(bad))


def test_phia_bot_khong_goi_thang_vao_erp():
    assert len(list(BOT_DIR.glob("*.py"))) > 20, f"không thấy mã bot ở {BOT_DIR} — bài canh sẽ xanh giả"
    bad = _violations()
    assert not bad, (
        "Mã phía bot import thẳng phân hệ ERP — ở chế độ service (dev/prod) DB của bot KHÔNG có bảng đó:\n  "
        + "\n  ".join(bad)
        + "\nĐi qua agent_hub/erp.py (_Local + _Remote) và một đường cổng B ở agent_gateway/controller.py; "
          "chắc chắn an toàn thì khai vào DA_RA kèm lý do."
    )


def test_bai_canh_bat_duoc_dung_loi_ai_cr_152():
    """Mẫu lỗi thật: hàm xử nút xác nhận import confirm_update rồi chạy trên DB của bot."""
    src = ("def _resolve_proposal(db, chat_id):\n"
           "    from app.modules.assistant.tools.update_tool import confirm_update\n"
           "    return confirm_update(db, None, '')\n")
    found = [n for n, f in _imports(ast.parse(src)) if n.startswith(WRITE_TOOLS)]
    assert found and all(f for _, f in _imports(ast.parse(src)))


def test_cong_kiem_chay_them_bai_canh_khi_dung_phan_bot(tmp_path):
    from app.modules.agent_hub import coder

    for t in coder.BOUNDARY_TESTS:
        (tmp_path / t).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / t).write_text("")
    picked = coder.gate_tests(str(tmp_path), ["backend/app/modules/agent_hub/service.py",
                                              "test/backend/test_agent_hub.py"])
    assert picked == sorted({"test/backend/test_agent_hub.py", *coder.BOUNDARY_TESTS})
    assert coder.gate_tests(str(tmp_path), ["backend/app/modules/leave/service.py"]) == []
