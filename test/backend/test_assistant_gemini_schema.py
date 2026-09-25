"""Lược đồ tool gửi cho Gemini — bao-CR-462.

Gemini chỉ nhận `enum` là danh sách CHUỖI. Tool nào khai bộ mã SỐ (luật R2/QĐ-11) thì API trả
400 và hỏng CẢ lượt hỏi, không riêng tool đó — nên chốt chặn phải nằm ở adapter.
"""
from app.modules.assistant.provider.gemini import _gemini_schema


def test_bo_enum_so_va_noi_bang_loi():
    """Bộ mã số: bỏ `enum`, giữ kiểu số, danh sách giá trị chuyển xuống phần mô tả."""
    out = _gemini_schema({
        "type": "object",
        "properties": {
            "status": {"type": "integer", "enum": [1, 2, 3], "description": "Trạng thái."},
        },
    })
    status = out["properties"]["status"]
    assert "enum" not in status
    assert status["type"] == "integer"
    assert "1 | 2 | 3" in status["description"]


def test_giu_nguyen_enum_chuoi():
    """Bộ mã chuỗi vốn hợp lệ với Gemini — không được đụng vào."""
    goc = {"type": "object", "properties": {
        "status": {"type": "string", "enum": ["active", "expired"]},
    }}
    out = _gemini_schema(goc)
    assert out["properties"]["status"]["enum"] == ["active", "expired"]
    assert goc["properties"]["status"]["enum"] == ["active", "expired"]  # không sửa tại chỗ


def test_di_sau_vao_mang_va_object_long_nhau():
    out = _gemini_schema({
        "type": "object",
        "properties": {
            "lines": {"type": "array", "items": {
                "type": "object",
                "properties": {"kind": {"type": "integer", "enum": [7, 8]}},
            }},
        },
    })
    kind = out["properties"]["lines"]["items"]["properties"]["kind"]
    assert "enum" not in kind and "7 | 8" in kind["description"]


def test_moi_tool_dang_bat_deu_hop_le_voi_gemini():
    """Chốt chặn thật: sau khi dọn, không tool nào còn `enum` phi chuỗi."""
    from app.modules.assistant.tools import tool_defs

    def soat(schema, duong):
        if not isinstance(schema, dict):
            return
        for v in schema.get("enum", []):
            assert isinstance(v, str), f"{duong} còn enum phi chuỗi: {v!r}"
        for ten, con in (schema.get("properties") or {}).items():
            soat(con, f"{duong}.{ten}")
        soat(schema.get("items"), f"{duong}[]")

    for d in tool_defs():
        soat(_gemini_schema(d.parameters), d.name)
