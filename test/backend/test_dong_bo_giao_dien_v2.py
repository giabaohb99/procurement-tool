"""Cổng quyền của `frontend-v2` phải khớp cổng quyền của backend (cụm 09).

Hai ràng buộc, cùng một lý do đặt ở đây: chỉ container `api` (qua mount chỉ-đọc
`/app/fe-src`) hoặc máy thật mới đọc được CẢ HAI cây mã.

1. **`ENTITIES` (09-B)** — danh sách khóa quyền gõ tay của FE = `ENTITIES` của BE.
2. **Mục menu `manage: true`** — mục đó mở khi có `create` HOẶC `write` HOẶC
   `delete`; nếu backend không thật sự gác đủ ba hành động đó thì hành động
   thiếu là **hành động ma**: cấp nó cho ai là người đó thấy menu mở ra rồi mọi
   lời gọi bên trong ăn 403 — mà 403 trên GET KHÔNG bật toast, nên họ chỉ thấy
   một màn trống. Đúng định nghĩa "nút giả".

─── Phần 1 ───

`frontend-v2/src/core/authorization/permission-types.ts` là một mảng GÕ TAY. Nó
không phải danh sách "những khóa v2 đang dùng" mà là BẢN SAO của `ENTITIES` —
`PermissionEntity` là union type, nên khóa nào không có trong mảng thì
`can('khoa_do', 'read')` không biên dịch nổi. Hậu quả thật: người viết màn mới
hoặc ép kiểu, hoặc bỏ luôn cổng quyền ở giao diện.

Lệch đã xảy ra (05/09/2026): backend 53 khóa, frontend 51 — thiếu `seal_request`
và `seal_type` của phân hệ Duyệt dấu. Vô hại lúc phát hiện vì hai khóa đó chưa
có màn nào ở v2, nhưng không có gì canh nên nó sống được bao lâu tùy may rủi.

⚠️ Bài kiểm này đọc mã NGOÀI `backend/`. Container `api` chỉ mount `./backend`
và `./test`, nên đường đọc thường đi qua mount chỉ-đọc `/app/fe-src` (khai trong
`docker-compose.yml`). Chạy ở máy thật hoặc ở CI thì tự dò ngược lên tìm
`frontend-v2/src`. Cùng khuôn với `backend/scripts/gen_status_ts.py`, xem chú
thích `out_path()` bên đó.
"""
import re
from pathlib import Path

import pytest

from app.core.permissions import ACTIONS, ENTITIES

#  Mount chỉ-đọc dành riêng cho bài kiểm này (xem docker-compose.yml, service `api`).
_MOUNT = Path("/app/fe-src")


def _fe_src() -> Path | None:
    """Thư mục `frontend-v2/src`, hoặc None khi môi trường không nhìn thấy nó."""
    if _MOUNT.is_dir():
        return _MOUNT
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "frontend-v2" / "src"
        if candidate.is_dir():
            return candidate
    return None


def _skip_khong_thay_fe():
    pytest.skip(
        "Không thấy frontend-v2/src. Trong container `api` cần mount chỉ-đọc "
        "/app/fe-src (docker-compose.yml) — chạy `docker compose up -d api` một lần."
    )


def _find_ts() -> Path | None:
    src = _fe_src()
    if src is None:
        return None
    return src / "core" / "authorization" / "permission-types.ts"


def _parse_ts_list(source: str, name: str) -> list[str]:
    """Bóc `export const <name> = [ 'a', 'b', … ] as const` thành list[str].

    Cố ý KHÔNG dùng một biểu thức chính quy nuốt cả khối: chú thích trong mảng có
    dấu ngoặc vuông và dấu nháy đơn tiếng Việt ("Đừng"), nên phải cắt theo mốc
    rồi lọc từng dòng.
    """
    start = source.index(f"export const {name} = [")
    end = source.index("] as const", start)
    block = source[start:end]
    #  Bỏ chú thích trước khi bóc chuỗi: chú thích tiếng Việt có dấu nháy đơn.
    block = re.sub(r"/\*.*?\*/", "", block, flags=re.S)
    block = re.sub(r"//[^\n]*", "", block)
    return re.findall(r"'([a-z_]+)'", block)


def _load_fe(name: str) -> list[str]:
    path = _find_ts()
    if path is None or not path.exists():
        _skip_khong_thay_fe()
    return _parse_ts_list(path.read_text(encoding="utf-8"), name)


def test_entities_frontend_khop_backend():
    fe = _load_fe("ENTITIES")

    thieu = [e for e in ENTITIES if e not in fe]
    thua = [e for e in fe if e not in ENTITIES]

    assert thieu == [], (
        f"frontend-v2 THIẾU {len(thieu)} khóa backend đang gác: {thieu}. "
        "Thêm vào ENTITIES của permission-types.ts."
    )
    assert thua == [], (
        f"frontend-v2 khai THỪA {len(thua)} khóa backend không có: {thua}. "
        "Khóa ma thì `can()` luôn trả false, nút bị giấu vĩnh viễn."
    )
    assert len(fe) == len(ENTITIES)


def test_entities_frontend_khong_trung_lap():
    #  Mảng gõ tay + nhiều người thêm dòng => chép đôi là chuyện thường. Trùng
    #  không làm sai `can()` nhưng làm sai mọi phép đếm dựa trên nó.
    fe = _load_fe("ENTITIES")
    assert len(set(fe)) == len(fe), "ENTITIES của frontend-v2 có khóa lặp"


def test_actions_frontend_khop_backend_cong_them_process():
    """`ACTIONS` của FE = ACTIONS backend + `process`.

    `process` KHÔNG phải một ô trong ma trận vai trò — backend bồi thêm cờ đó cho
    nhân sự thu mua ở bản đồ quyền trả về lúc đăng nhập. Nó được phép có ở FE và
    được phép KHÔNG có trong `permissions.ACTIONS`; mọi chênh lệch khác là lỗi.
    """
    fe = _load_fe("ACTIONS")

    assert fe[: len(ACTIONS)] == list(ACTIONS), (
        f"ACTIONS lệch: backend={list(ACTIONS)} frontend={fe}"
    )
    assert fe[len(ACTIONS):] == ["process"], (
        "FE chỉ được có đúng một action ngoài ma trận vai trò là `process`; "
        f"đang thừa {fe[len(ACTIONS):]}"
    )


# ═══════════════════════════ Phần 2 ═══════════════════════════
#
# Mục menu khai `manage: true` (`app/router/module-visibility.ts`) mở khi người
# dùng có `create` HOẶC `write` HOẶC `delete` trên khóa của mục. Backend không
# gác một trong ba hành động đó thì hành động ấy là **hành động ma**: nó vẫn
# hiện thành ô tick ở màn Phân quyền (ma trận dựng từ `ENTITIES × ACTIONS`),
# cấp cho ai là người đó thấy menu mở ra rồi mọi lời gọi bên trong ăn 403 — và
# 403 trên GET KHÔNG bật toast (`core/api/http-client.ts`), nên tất cả những gì
# họ thấy là một màn hình trống. Không có triệu chứng nào chỉ đúng nguyên nhân.

_MANAGE_ACTIONS = ("create", "write", "delete")

#  Chỗ ĐANG lệch, ghi nhận có chủ ý để bài kiểm bắt được cái MỚI thay vì đỏ
#  vĩnh viễn. Sửa được cái nào thì xóa dòng đó đi (bài kiểm sẽ nhắc).
#
#  · `setting`   — backend chỉ có `read` (xem cấu hình) + `write` (lưu, thử
#    email, thử kho tệp). Cấu hình là MỘT bản ghi duy nhất, không có "tạo" và
#    không có "xóa", nên hai ô đó vốn không có nghĩa. Ba mục menu ăn theo
#    (Tổng quan · Cấu hình hệ thống · Nhật ký hệ thống).
#  · `backup`    — backend có `read` (danh sách, tải về), `create` (chạy ngay),
#    `delete` (xóa bản lưu). Không có `write`: đã có bản dump rồi thì không sửa
#    được gì bên trong nó.
_LECH_DA_BIET = {
    ("setting", "create"),
    ("setting", "delete"),
    ("backup", "write"),
}


def _quet_muc_manage(src: Path) -> list[tuple[str, str, str]]:
    """(đường tệp, nhãn mục, khóa quyền) của mọi mục menu khai `manage: true`."""
    ket_qua: list[tuple[str, str, str]] = []
    for path in sorted(src.glob("modules/*/routes.tsx")):
        text = path.read_text(encoding="utf-8")
        #  Mục menu là một object phẳng trong mảng `nav` — cắt theo cặp ngoặc
        #  KHÔNG lồng nhau là đủ và không cần dựng bộ phân tích cú pháp TS.
        for khoi in re.findall(r"\{[^{}]*\}", text, re.S):
            if "manage: true" not in khoi:
                continue
            khoa = re.search(r"entity:\s*'([a-z_]+)'", khoi)
            nhan = re.search(r"label:\s*'([^']+)'", khoi)
            if khoa:
                ket_qua.append((path.name, nhan.group(1) if nhan else "?", khoa.group(1)))
    return ket_qua


def _cap_require_cua_backend() -> set[tuple[str, str]]:
    """Mọi cặp (entity, action) backend THẬT SỰ gác.

    Gom từ ba nguồn vì backend gác bằng ba cách khác nhau:
      · `require("x", "y")` viết thẳng;
      · `require(ENTITY, "y")` với hằng chuỗi khai ở đầu module;
      · `make_crud_router(..., "x", ...)` — router chung tự gác đủ 4 hành động.
    """
    cap: set[tuple[str, str]] = set()
    goc = Path(__file__).resolve().parents[2] / "backend" / "app"
    if not goc.is_dir():
        goc = Path("/app")
    for path in goc.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        hang = dict(re.findall(r'^([A-Z_][A-Z0-9_]*)\s*=\s*"([a-z_]+)"\s*$', text, re.M))
        for tok, action in re.findall(r'require\(\s*([^,()]+?)\s*,\s*"([a-z_]+)"\s*\)', text):
            tok = tok.strip()
            entity = tok.strip('"') if tok.startswith('"') else hang.get(tok)
            if entity:
                cap.add((entity, action))
        for m in re.finditer(r"make_crud_router\(", text):
            doan = text[m.end() : m.end() + 400]
            khoa = re.search(r'entity\s*=\s*"([a-z_]+)"', doan) or re.search(
                r'^\s*"[^"]*"\s*,\s*"([a-z_]+)"', doan, re.M
            )
            if khoa:
                for action in ("read", *_MANAGE_ACTIONS):
                    cap.add((khoa.group(1), action))
    return cap


def test_muc_menu_manage_khong_mo_bang_hanh_dong_ma():
    src = _fe_src()
    if src is None:
        _skip_khong_thay_fe()

    muc = _quet_muc_manage(src)
    assert muc, "không quét được mục menu nào — biểu thức bóc `manage: true` đã hỏng"

    co_that = _cap_require_cua_backend()
    assert ("role", "write") in co_that, "quét backend hỏng: thiếu cả cặp chắc chắn có"

    lech = {(khoa, a) for _, _, khoa in muc for a in _MANAGE_ACTIONS if (khoa, a) not in co_that}

    moi = sorted(lech - _LECH_DA_BIET)
    assert moi == [], (
        f"Mục menu `manage: true` mở bằng hành động backend KHÔNG gác: {moi}. "
        "Cấp hành động đó cho ai là người đó thấy menu rồi vào trong 403 im lặng. "
        "Hoặc bỏ `manage: true` (đổi sang `action:` đúng hành động), hoặc thêm "
        "vào `_LECH_DA_BIET` kèm lý do."
    )

    da_sua = sorted(_LECH_DA_BIET - lech)
    assert da_sua == [], (
        f"Những cặp này backend đã gác rồi, xóa khỏi `_LECH_DA_BIET`: {da_sua}"
    )
