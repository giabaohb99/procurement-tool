"""Sinh bản TypeScript của các bộ mã cố định từ sổ đăng ký `status_catalog` (B-01 / QĐ-9).

Vì sao cần: bộ mã trạng thái hiện được chép tay ở cả backend lẫn giao diện
(`frontend-v2/src/modules/procurement/types/purchase-document.ts` có bốn bản
`Record<string, string>` gõ tay). Ba bản chép lệch nhau là chuyện đã xảy ra thật với
`contract_type` trước CR-118 — bộ lọc chỉ với tới vài giá trị, ô chọn mở ra trống trơn.

Cách H2 ở `doc/erp/06` §5: SINH ra tệp rồi LƯU vào mã nguồn, CI chạy lại và so sánh, chứ
KHÔNG dựng API cho giao diện lấy động lúc chạy. Sinh sẵn thì màn không phải chờ thêm một
lượt gọi, và lệch phiên bản thì CI báo chứ không âm thầm.

Chỉ sinh cho `frontend-v2/`. `frontend/` (bản cũ, prod đang chạy) nằm NGOÀI phạm vi theo
QĐ-10 — xem `doc/erp/15` §4.2.

Chạy TRONG container api:
    docker compose exec -T api python -m scripts.gen_status_ts           # ghi đè tệp .ts
    docker compose exec -T api python -m scripts.gen_status_ts --check   # CI: chỉ so, không ghi

Chạy ở máy (không cần DB — tệp này không đụng CSDL):
    cd backend && python -m scripts.gen_status_ts
"""
import json
import sys
from pathlib import Path

from app.core import code_sets  # noqa: F401  (nạp cho đủ sổ đăng ký)
from app.core.status_catalog import all_sets

_REL = Path("frontend-v2") / "src" / "shared" / "constants" / "statuses.ts"


def out_path() -> Path | None:
    """Tìm ngược lên cho tới khi thấy `frontend-v2/`. None = môi trường không có nó.

    Không tính bậc cứng được: ở máy thì tệp này nằm ở `<repo>/backend/scripts/`, còn trong
    container api thì cả thư mục `backend/` được mount thẳng thành `/app` nên `frontend-v2/`
    KHÔNG có mặt. Kịch bản này chỉ chạy ở máy hoặc ở CI, nơi có đủ cả repo.
    """
    for p in Path(__file__).resolve().parents:
        if (p / _REL).parent.is_dir():
            return p / _REL
    return None

HEADER = """// TỆP SINH TỰ ĐỘNG — ĐỪNG SỬA TAY.
// Nguồn: backend/app/core/status_catalog.py (sổ đăng ký nạp qua app/core/code_sets.py).
// Sinh lại: docker compose exec -T api python -m scripts.gen_status_ts
// Sửa nhãn hay thêm mã thì sửa ở Python rồi sinh lại, đừng vá ở đây — CI so hai bên,
// lệch một ký tự là hỏng build.

export interface StatusOption {
  /** MÃ lưu trong CSDL. Không bao giờ đổi. */
  value: string
  /** Nhãn tiếng Việt để hiển thị. Đổi thoải mái. */
  label: string
  /** Vị trí trong chuỗi tiến trình. Bộ không có thứ tự thì mọi mã đều là 0. */
  sort_order: number
  /** Trạng thái kết, không đi tiếp được. */
  is_terminal: boolean
  /** Nhánh rẽ ra khỏi chuỗi (tạm ngưng, hủy) — không có chỗ trong thứ tự. */
  is_exception: boolean
}
"""

FOOTER = """
/** Nhãn theo mã, cho chỗ chỉ cần hiển thị. */
export function labelOf(options: readonly StatusOption[], value: string | null | undefined): string {
  return options.find((o) => o.value === value)?.label ?? ''
}

/** Chuỗi tiến trình theo sort_order, đã bỏ các mã ngoại lệ. */
export function orderedValues(options: readonly StatusOption[]): string[] {
  return options.filter((o) => !o.is_exception)
    .slice()
    .sort((a, b) => a.sort_order - b.sort_order)
    .map((o) => o.value)
}
"""


def _const_name(set_name: str) -> str:
    return set_name.upper()


def render() -> str:
    parts = [HEADER]
    names = list(all_sets())
    for name, cs in all_sets().items():
        body = ",\n".join(
            "  " + json.dumps(o, ensure_ascii=False) for o in cs.full_options
        )
        parts.append(
            f"\n/** {cs.title} */\n"
            f"export const {_const_name(name)}: readonly StatusOption[] = [\n{body},\n]\n"
        )

    registry = ",\n".join(f"  {n}: {_const_name(n)}" for n in names)
    parts.append(
        "\n/** Tra theo tên bộ, cho chỗ dựng ô chọn động. */\n"
        "export const STATUS_SETS = {\n" + registry + ",\n} as const\n"
    )
    parts.append(FOOTER)
    return "".join(parts)


def main() -> int:
    text = render()
    check = "--check" in sys.argv

    OUT = out_path()
    if OUT is None:
        print("LỖI: không thấy 'frontend-v2/src/shared/constants/' — chạy ở máy hoặc ở CI, "
              "không chạy trong container api.")
        return 2

    old = OUT.read_text(encoding="utf-8") if OUT.exists() else None
    if old == text:
        print(f"OK: {OUT.name} đã khớp với backend ({len(all_sets())} bộ mã).")
        return 0

    if check:
        print(f"LỖI: {OUT} lệch với backend. Chạy lại 'python -m scripts.gen_status_ts'.")
        return 1

    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"Đã ghi {OUT} ({len(all_sets())} bộ mã).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
