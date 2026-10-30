"""Đọc Kho skill cho AI bên ngoài (bao-CR-622, K2 của doc/erp/21 §5.1) — cổng MCP gọi qua cổng B.

Ba việc, đều dưới quyền NGƯỜI CẦM KHÓA và chỉ trên tập `access_service.visible_skills` của người đó:
  list_for_ai   — danh sách skill (tên gọi, tiêu đề, tóm tắt) để AI chọn
  read_for_ai   — nội dung phiên bản ĐÃ XUẤT BẢN + danh sách tệp
  file_for_ai   — một tệp đính kèm dạng chữ

Mức bảo mật của BỘ (constants.SecurityLevel): Mở → nội dung + tệp · Bảo vệ → nội dung, KHÔNG tệp · Khóa → chỉ tiêu đề +
tóm tắt (nội dung chỉ trợ lý nội bộ đọc). Skill không đọc được trả `denied` với câu giống hệt skill không tồn tại — người
ngoài không dò được tên skill của phòng khác.

Tên gọi (`name`) là slug; hai bộ cùng có một slug thì skill đó gọi bằng `MÃ-BỘ/slug`.

ai-CR-220 (K7): Trợ lý web + bot (TRỢ LÝ NỘI BỘ) cũng đọc qua đây với `internal=True` — vẫn đúng tập `visible_skills` của
người hỏi, nhưng mức bảo mật chỉ chặn AI BÊN NGOÀI: nội bộ đọc cả nội dung bộ Khóa lẫn tệp đính kèm bộ Bảo vệ.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from .access_service import visible_skills
from .constants import SecurityLevel
from .model import AiSkillFile, AiSkillSet, AiSkillVersion

NOT_FOUND = "Không có skill **{name}** trong những skill bạn được đọc — gọi list_skills để xem tên đúng."
MAX_LIST = 200
#  ai-CR-228 (đại ca nối ChatGPT 19/10: ChatGPT đọc skill dài nhất kho rồi bảo "không trả về nội dung", chỉ nhắc lại phần
#  tóm tắt): câu dặn cũ "đừng đọc lại nguyên văn… tài sản công ty" làm AI tưởng KHÔNG được dùng nội dung. Nói thẳng là
#  được dùng; chỉ không chép nguyên bài ra ngoài.
APPLY_NOTE = ("Dùng nội dung này để trả lời và làm việc cho người dùng (được tóm tắt, trích ý, áp dụng vào việc); chỉ "
              "không chép lại nguyên văn cả bài ra ngoài.")
FILES_NOTE = "Skill có tệp đính kèm (files) — cần chi tiết thì đọc bằng read_skill_file."
#  Chia trang nội dung dài: ChatGPT bỏ qua kết quả công cụ quá dài (skill nhà máy ~35k ký tự). Mỗi lần trả tối đa PAGE_CHARS,
#  cắt ở ranh giới tiêu đề / đoạn / dòng; ghép các trang lại = nguyên văn.
PAGE_CHARS = 10_000
_MIN_PAGE = PAGE_CHARS // 2


def page_of(text: str, offset=0, limit: int = PAGE_CHARS) -> dict:
    """{content, offset, next_offset (None = hết), total_chars}. Cắt ở ranh giới đẹp nhất trong nửa sau của trang: tiêu đề
    (dòng bắt đầu #) > đoạn (dòng trống) > xuống dòng; không có thì cắt cứng đúng `limit`."""
    text = text or ""
    total = len(text)
    try:
        start = max(0, int(offset or 0))
    except (TypeError, ValueError):
        start = 0
    if start >= total:
        return {"content": "", "offset": start, "next_offset": None, "total_chars": total,
                "page_note": f"offset {start} đã qua cuối nội dung ({total} ký tự) — đọc lại từ offset=0." if total else ""}
    end = start + limit
    if end < total:
        window = text[start:end]
        cut = -1
        for marker in ("\n#", "\n\n", "\n"):
            pos = window.rfind(marker, _MIN_PAGE)
            if pos > 0:
                cut = pos + 1               # giữ dấu xuống dòng ở trang này, trang sau mở bằng tiêu đề / đoạn mới
                break
        if cut > 0:
            end = start + cut
    else:
        end = total
    out = {"content": text[start:end], "offset": start, "next_offset": end if end < total else None, "total_chars": total}
    if end < total:
        out["page_note"] = (f"Mới đọc tới ký tự {end}/{total}. Gọi lại với offset={end} để đọc tiếp TRƯỚC khi trả lời câu "
                            "cần chi tiết ở phần sau.")
    return out


def _iso(value):
    return value.isoformat(timespec="seconds") if value else None


def _named(db: Session, user) -> list[dict]:
    """visible_skills + tên gọi duy nhất (slug, trùng slug giữa các bộ thì thêm mã bộ)."""
    rows = visible_skills(db, user)
    if not rows:
        return []
    codes = {s.id: s.code for s in db.query(AiSkillSet.id, AiSkillSet.code)
             .filter(AiSkillSet.id.in_({r["skill_set_id"] for r in rows}))}
    seen: dict[str, int] = {}
    for row in rows:
        seen[row["slug"].lower()] = seen.get(row["slug"].lower(), 0) + 1
    for row in rows:
        row["name"] = row["slug"] if seen[row["slug"].lower()] == 1 else f"{codes.get(row['skill_set_id'], '')}/{row['slug']}"
    return rows


def _find(db: Session, user, name: str) -> dict | None:
    name = (name or "").strip()
    for row in _named(db, user):
        if row["name"].lower() == name.lower():
            return row
    return None


def list_for_ai(db: Session, user, query: str = "", skill_set: str = "", internal: bool = False) -> dict:
    rows = _named(db, user)
    q, s = (query or "").strip().lower(), (skill_set or "").strip().lower()
    if q:
        rows = [r for r in rows if q in f"{r['name']} {r['title']} {r['summary']}".lower()]
    if s:
        rows = [r for r in rows if s in r["skill_set"].lower()]
    file_counts = {}
    if rows:
        from sqlalchemy import func

        file_counts = dict(db.query(AiSkillFile.skill_id, func.count(AiSkillFile.id))
                           .filter(AiSkillFile.skill_id.in_({r["skill_id"] for r in rows}))
                           .group_by(AiSkillFile.skill_id).all())
    items = [{"name": r["name"], "title": r["title"], "summary": r["summary"], "skill_set": r["skill_set"],
              "version": r["version_no"], "updated_at": _iso(r["updated_at"]),
              "files": (int(file_counts.get(r["skill_id"], 0))
                        if internal or r["security_level"] == SecurityLevel.OPEN else 0),
              "content_readable": internal or r["security_level"] != SecurityLevel.LOCKED}
             for r in rows[:MAX_LIST]]
    out = {"total": len(rows), "items": items,
           "note": "Gọi read_skill với đúng `name` để đọc hướng dẫn trước khi làm việc nghiệp vụ liên quan."}
    if not rows:
        out["note"] = ("Bạn chưa được giao skill nào" + (" khớp bộ lọc" if (q or s) else "")
                       + ". Nhờ quản trị Kho skill AI gán quyền đọc nếu cần.")
    return out


def read_for_ai(db: Session, user, name: str, internal: bool = False, offset=0) -> dict:
    row = _find(db, user, name)
    if row is None:
        return {"denied": True, "error": NOT_FOUND.format(name=name)}
    out = {"skill_id": row["skill_id"], "name": row["name"], "title": row["title"], "summary": row["summary"],
           "skill_set": row["skill_set"], "version": row["version_no"], "updated_at": _iso(row["updated_at"]),
           "security_level": row["security_level_label"]}
    if row["security_level"] == SecurityLevel.LOCKED and not internal:
        out["note"] = "Bộ skill này ở mức Khóa: nội dung chỉ trợ lý nội bộ của công ty đọc, AI bên ngoài chỉ thấy tóm tắt."
        return out
    version = db.get(AiSkillVersion, row["version_id"])
    out.update(page_of(version.body_md if version else "", offset))
    if internal or row["security_level"] == SecurityLevel.OPEN:
        out["files"] = [{"path": f.path, "size": f.size} for f in db.query(AiSkillFile)
                        .filter(AiSkillFile.skill_id == row["skill_id"]).order_by(AiSkillFile.path)]
    else:
        out["files"] = []
        out["files_note"] = "Bộ skill ở mức Bảo vệ: tệp đính kèm không trả cho AI bên ngoài."
    out["note"] = APPLY_NOTE + (" " + FILES_NOTE if out.get("files") else "")
    return out


def file_for_ai(db: Session, user, name: str, path: str, internal: bool = False, offset=0) -> dict:
    row = _find(db, user, name)
    if row is None:
        return {"denied": True, "error": NOT_FOUND.format(name=name)}
    if row["security_level"] != SecurityLevel.OPEN and not internal:
        return {"denied": True, "skill_id": row["skill_id"],
                "error": f"Bộ skill của **{row['name']}** không mở tệp đính kèm cho AI bên ngoài."}
    found = (db.query(AiSkillFile).filter(AiSkillFile.skill_id == row["skill_id"],
                                          AiSkillFile.path == (path or "").strip()).first())
    if found is None:
        return {"error": f"Skill **{row['name']}** không có tệp **{path}** — xem danh sách tệp trong read_skill.",
                "skill_id": row["skill_id"]}
    return {"skill_id": row["skill_id"], "name": row["name"], "path": found.path, **page_of(found.content_text, offset),
            "note": APPLY_NOTE}
