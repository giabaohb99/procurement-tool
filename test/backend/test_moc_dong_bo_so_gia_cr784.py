"""duoc-CR-784 — BÀI CANH TĨNH: mọi chỗ ĐMH gọi `_sync_pr(` (mốc đổi dòng / trạng thái đơn) phải gọi `sync_po_price_ledger(`.

Sổ giá là dữ liệu dẫn xuất nên sót một mốc nghĩa là giá cũ treo trong sổ, im lặng. `_sync_pr` đã là "mọi nơi đổi dòng ĐMH"
(đồng bộ YCMH cần đúng các mốc đó), nên bài này đọc AST của `purchase_order/*.py`: hàm nào gọi `_sync_pr` mà không gọi hook
sổ giá thì đỏ, trừ những hàm khai miễn trừ dưới đây kèm lý do.
"""
import ast
from pathlib import Path

import app.modules.purchase_order as po_pkg

#  {"tệp.py::hàm": lý do}. Thêm dòng phải có lý do thật; hết cần thì gỡ (bài kiểm bên dưới bắt dòng thừa).
MIEN_TRU = {
    "edit_service.py::create_po": "đơn mới luôn ở Nháp nên chưa có dòng sổ giá — thêm hook chỉ tốn thêm truy vấn mỗi lần sinh đơn "
                                  "(bài chụp số truy vấn của bao-CR-715 sẽ đỏ)",
    "reprice_service.py::reprice_po": "VIỆC TREO duoc-CR-784: tệp `reprice_service.py` chưa lên erp-v2 (phiên khác giữ) nên chưa "
                                      "gắn hook; cho tới lúc đó giá đổi bằng reprice chỉ vào sổ khi `backfill_product_price_ledger "
                                      "--apply` chạy lại hoặc ĐMH đổi mốc kế tiếp. GẮN HOOK RỒI GỠ DÒNG NÀY.",
}


def _call_names(fn: ast.AST) -> set[str]:
    names = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            f = node.func
            names.add(f.id if isinstance(f, ast.Name) else getattr(f, "attr", ""))
    return names


def _functions_calling_sync_pr() -> dict[str, set[str]]:
    out = {}
    for path in sorted(Path(po_pkg.__file__).parent.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for fn in ast.walk(tree):
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names = _call_names(fn)
                if "_sync_pr" in names:
                    out[f"{path.name}::{fn.name}"] = names
    return out


def test_moi_ham_goi_sync_pr_deu_goi_hook_so_gia():
    funcs = _functions_calling_sync_pr()
    assert funcs, "không thấy hàm nào gọi _sync_pr — bài canh mất tác dụng, kiểm lại đường dẫn"
    missing = sorted(k for k, names in funcs.items() if "sync_po_price_ledger" not in names and k not in MIEN_TRU)
    assert missing == [], (
        f"{missing} gọi _sync_pr mà không gọi sync_po_price_ledger — sổ giá sẽ giữ giá cũ. "
        "Gắn `sync_po_price_ledger(db, po)` ngay sau lời gọi, hoặc khai MIEN_TRU kèm lý do."
    )


def test_mien_tru_khong_thua():
    funcs = _functions_calling_sync_pr()
    for key in MIEN_TRU:
        #  `reprice_service.py` là tệp của phiên khác, có thể CHƯA lên erp-v2: vắng tệp / vắng hàm thì miễn trừ đứng yên (không
        #  đỏ). Khi nó lên mà đã gắn hook thì phải gỡ dòng miễn trừ; khi nó lên mà chưa gắn thì bài `test_moi_ham_...` vẫn xanh
        #  nhờ miễn trừ này — việc cần làm nằm ở TODO của MIEN_TRU (gắn `sync_po_price_ledger(db, po)` sau `_sync_pr`).
        if key not in funcs:
            continue
        assert "sync_po_price_ledger" not in funcs[key], f"{key} đã có hook sổ giá — gỡ khỏi MIEN_TRU"


def test_ba_diem_gan_hook_ngoai_purchase_order():
    """Ba nơi KHÔNG có `_sync_pr` nhưng đổi dòng ĐMH / lịch sử: snapshot_line, hoàn tác lô nhập, nạp lại legacy."""
    import inspect

    from app.modules.import_tool import service as import_service
    from app.modules.purchase_history import service as history_service
    assert "_record_in_price_ledger(db, obj, item)" in inspect.getsource(history_service.snapshot_line)
    assert "sync_po_price_ledger(db, po, commit=False)" in inspect.getsource(import_service._revert_po)
    legacy = Path(po_pkg.__file__).resolve().parents[3] / "scripts" / "import_purchase_history_legacy.py"
    if legacy.exists():   # trong container, `scripts/` nằm cạnh `app/`
        assert "sync_history_ledger" in legacy.read_text(encoding="utf-8")
