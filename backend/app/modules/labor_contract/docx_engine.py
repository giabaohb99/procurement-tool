"""BỘ MÁY .docx cho mẫu HĐLĐ: kiểm mẫu lúc tải lên + render. THUẦN (không DB, không HTTP).

Mẫu do NGƯỜI DÙNG tải lên nên mọi bước đều phải coi là đầu vào không tin cậy:
  - SSTI: Jinja mặc định chạy được `{{ ''.__class__.__mro__ ... }}` → bắt buộc
    `ImmutableSandboxedEnvironment` (chặn thuộc tính nội bộ, chặn sửa đối tượng, trần `range`).
  - `& < > "` trong tên / địa chỉ phá XML → `autoescape=True`.
  - Zip bomb: trần số mục + tổng dung lượng giải nén.
  - Macro: không nhận gói có `vbaProject.bin` / content-type `macroEnabled`.
  - Biến ngoài danh mục sẽ render RỖNG IM LẶNG → chặn ngay lúc tải lên, nêu tên biến.
  - DoS CPU: vòng `for` lồng nhau (100000 x 100000) ngốn CPU mà sandbox không chặn → mẫu CHỈ được
    chứa biểu thức `{{ ten_bien }}` thuần. MỌI thẻ lệnh `{% ... %}` (kể cả `{%p`, `{%tr`, `{%r`
    của docxtpl, vốn bị `patch_xml` đổi về `{% %}` trước khi tới Jinja) và mọi biểu thức khác tên
    biến (gọi hàm, truy cập thuộc tính, phép tính, filter) bị TỪ CHỐI ngay ở bước phân tích cú pháp.
    Kiểm nằm ở `_parse` của môi trường nên phủ cả thân bài, đầu/chân trang, chú thích cuối trang
    và thuộc tính tài liệu — mọi chỗ docxtpl cho render. Chú thích `{# #}` bị lexer bỏ, vô hại.
  - Word hay TÁCH RUN (`{{ ho_` + `ten }}` do soát chính tả / định dạng giữa chừng): ca docxtpl
    không gộp được hiện ra thành biến lạ / lỗi cú pháp → người dùng gõ lại biến MỘT lượt.
"""
from io import BytesIO

from docxtpl import DocxTemplate
from jinja2 import StrictUndefined, TemplateError, nodes
from jinja2.sandbox import ImmutableSandboxedEnvironment

from app.modules.labor_contract.docx_package_check import (  # noqa: F401  (re-export cho nơi gọi cũ)
    MAX_ZIP_ENTRIES, TemplateRejected, check_package)
from app.modules.labor_contract.placeholder_catalog import KNOWN_KEYS, sample_context


class ForbiddenTemplateSyntax(TemplateError):
    """Mẫu dùng cú pháp ngoài `{{ ten_bien }}` — xem docstring đầu tệp."""


def _ensure_only_simple_variables(tree: nodes.Template) -> None:
    """Chỉ nhận chữ tĩnh + `{{ ten_bien }}`. Bất kỳ nút nào khác (For/If/Set/Call/Getattr/Filter...) → từ chối."""
    for node in tree.body:
        if not isinstance(node, nodes.Output):
            raise ForbiddenTemplateSyntax(
                f"Mẫu có thẻ lệnh {{% {type(node).__name__.lower()} %}} — mẫu chỉ được dùng biến "
                "dạng {{ ten_bien }}, không dùng vòng lặp / điều kiện")
        for child in node.nodes:
            if isinstance(child, nodes.TemplateData):
                continue
            if isinstance(child, nodes.Name) and child.ctx == "load":
                continue
            raise ForbiddenTemplateSyntax(
                "Mẫu có biểu thức phức tạp (gọi hàm, thuộc tính, phép tính hoặc bộ lọc) — "
                "mỗi dấu {{ }} chỉ được chứa đúng một tên biến trong danh mục")


class _SimpleVariableEnvironment(ImmutableSandboxedEnvironment):
    """Sandbox + chỉ cho `{{ ten_bien }}`. `_parse` là điểm duy nhất `parse`/`from_string`/`compile` cùng đi qua."""

    def _parse(self, source, name, filename):
        tree = super()._parse(source, name, filename)
        _ensure_only_simple_variables(tree)
        return tree


def _make_env() -> ImmutableSandboxedEnvironment:
    #  StrictUndefined: sandbox đổi truy cập thuộc tính nội bộ (`x.__class__`) thành đối tượng
    #  Undefined — mặc định in ra RỖNG nên payload "qua" êm; strict thì in ra là NÉM LỖI, mẫu bị từ chối.
    return _SimpleVariableEnvironment(autoescape=True, undefined=StrictUndefined)


def _open(data: bytes) -> DocxTemplate:
    try:
        return DocxTemplate(BytesIO(data))
    except Exception:  # why: python-docx ném nhiều kiểu lỗi (KeyError, PackageNotFound, lxml) cho gói hỏng
        raise TemplateRejected("Không đọc được nội dung tệp .docx (tệp hỏng hoặc sai cấu trúc).")


def _render_to_bytes(tpl: DocxTemplate, ctx: dict[str, str]) -> bytes:
    try:
        tpl.render(ctx, jinja_env=_make_env(), autoescape=True)
    except ForbiddenTemplateSyntax as exc:  # câu đã trọn nghĩa — không nối thêm mẹo «gõ lại biến»
        raise TemplateRejected(f"{exc}.")
    except TemplateError as exc:  # gồm TemplateSyntaxError và SecurityError của sandbox
        line = getattr(exc, "lineno", None)
        where = f" (gần dòng {line})" if line else ""
        raise TemplateRejected(
            f"Mẫu có lỗi cú pháp hoặc dùng biểu thức không được phép{where}: {exc}. "
            "Chỉ dùng biến dạng {{ ten_bien }} và gõ lại biến một lượt, không định dạng giữa chừng."
        )
    except Exception as exc:  # why: biểu thức hợp cú pháp vẫn nổ lúc chạy (1/0, range quá lớn, kiểu sai…)
        raise TemplateRejected(f"Mẫu lỗi khi chạy thử: {type(exc).__name__}: {exc}")
    out = BytesIO()
    tpl.save(out)
    return out.getvalue()


def inspect_template(data: bytes) -> list[str]:
    """Kiểm mẫu lúc tải lên. Trả danh sách biến dùng (đã sắp); sai → TemplateRejected."""
    check_package(data)
    tpl = _open(data)
    try:
        used = tpl.get_undeclared_template_variables(jinja_env=_make_env())
    except ForbiddenTemplateSyntax as exc:  # câu đã trọn nghĩa — không nối thêm mẹo «gõ lại biến»
        raise TemplateRejected(f"{exc}.")
    except TemplateError as exc:
        raise TemplateRejected(
            f"Mẫu có lỗi cú pháp: {exc}. Gõ lại biến một lượt, không định dạng giữa chừng."
        )
    except Exception:  # why: XML hỏng trong gói (lxml) lộ ra ở bước phân tích biến, không phải TemplateError
        raise TemplateRejected("Không đọc được nội dung tệp .docx (tệp hỏng hoặc sai cấu trúc).")
    unknown = sorted(used - KNOWN_KEYS)
    if unknown:
        raise TemplateRejected(
            "Mẫu dùng biến ngoài danh mục: " + ", ".join(unknown), unknown=unknown
        )
    #  Render thử bằng dữ liệu mẫu: bắt lỗi chỉ lộ lúc chạy (vd. biểu thức bị sandbox chặn).
    #  Dùng bản mở MỚI vì `render` thay đổi chính đối tượng.
    _render_to_bytes(_open(data), sample_context())
    return sorted(used)


def render(data: bytes, ctx: dict[str, str]) -> bytes:
    """Điền `ctx` vào mẫu, trả bytes .docx. Kiểm lại gói (tệp lưu có thể bị thay)."""
    check_package(data)
    return _render_to_bytes(_open(data), ctx)
