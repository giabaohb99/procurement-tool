"""Tách LỊCH TRÌNH có giờ từ tệp kế hoạch (Markdown) thành danh sách sự kiện — máy làm, không để model nhớ (ai-CR-227).

Lượt run #368–369 (dev 19/10/2026): tệp ghi 01:30 ngủ khách sạn Ruby Trảng Bom, 05:15 đổ xăng Trảng Bom, 09:00 ăn sáng quán
Tazon — Lạc Lạc tạo lịch 01:30 «Dừng Long Thành», 04:00 «Ăn sáng Phan Thiết» (soạn lại từ trí nhớ hội thoại). Nay giờ, tên
điểm, việc làm, ghi chú lấy NGUYÊN VĂN từ bảng trong tệp; link bản đồ lấy đúng link có trong tệp.

Khuôn đọc được: mỗi ngày một tiêu đề `## …` có ngày `dd/mm` (năm lấy từ `dd/mm/yyyy` đầu tiên trong tệp), bên dưới một
bảng Markdown có cột `Giờ` (cột khác: Điểm dừng / Làm gì / Ghi chú — đọc theo TÊN cột), giờ dạng `21:00`, `~01:30`, `6h30`.
Giờ nhỏ hơn giờ dòng trước trong cùng ngày = đã qua nửa đêm (sang ngày sau).
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta

WEEKDAYS = ("Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật")
DATE_RX = re.compile(r"(?<!\d)(\d{1,2})/(\d{1,2})(?:/(\d{4}))?(?!\d)")
TIME_RX = re.compile(r"^~?\s*(\d{1,2})\s*[:h]\s*(\d{2})")
LINK_RX = re.compile(r"\[([^\]]*)\]\((https?://[^)\s]+)\)")
BOLD_RX = re.compile(r"\*\*(.+?)\*\*")
#  Ký hiệu trang trí trong tệp (biểu tượng, sao…) — bỏ khỏi tên sự kiện.
DECOR_RX = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿️‍*_`]")
MAX_GAP = timedelta(hours=6)          # khoảng tới dòng kế tiếp dài hơn thế thì coi như hết việc, mặc định 60 phút
DEFAULT_LEN = timedelta(minutes=60)
MAX_EVENTS = 200
#  «nghỉ ~45 phút», «Tham quan 1–1,5 tiếng», «Ngủ ~3,5 tiếng» — lấy số ĐẦU làm thời lượng (không vượt giờ dòng kế tiếp).
DURATION_RX = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:[–-]\s*\d+(?:[.,]\d+)?\s*)?(phút|tiếng|giờ)", re.I)


def _duration(*texts: str) -> timedelta | None:
    for t in texts:
        m = DURATION_RX.search(t or "")
        if m:
            n = float(m.group(1).replace(",", "."))
            return timedelta(minutes=n) if m.group(2).lower() == "phút" else timedelta(hours=n)
    return None


def weekday_of(d: date) -> str:
    return WEEKDAYS[d.weekday()]


def _clean(cell: str) -> str:
    return " ".join(DECOR_RX.sub("", cell or "").split()).strip(" -–")


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _year_of(text: str, today: date) -> int:
    for d, m, y in DATE_RX.findall(text):
        if y:
            return int(y)
    return today.year


def extract(text: str, today: date | None = None) -> dict:
    """{"su_kien": [...], "doan_map": [...], "canh_bao": [...]} — danh sách theo đúng thứ tự trong tệp."""
    today = today or date.today()
    year = _year_of(text or "", today)
    events: list[dict] = []
    sections: list[dict] = []
    warnings: list[str] = []
    section: dict | None = None
    header: list[str] | None = None
    for raw in (text or "").splitlines():
        line = raw.strip()
        if line.startswith("## "):
            m = DATE_RX.search(line)
            section = {"tieu_de": _clean(line[3:]), "ngay": None, "links": [], "events": []}
            if m:
                try:
                    section["ngay"] = date(int(m.group(3) or year), int(m.group(2)), int(m.group(1)))
                except ValueError:
                    warnings.append(f"Ngày lạ ở tiêu đề «{_clean(line[3:])}» — bỏ qua phần này.")
            sections.append(section)
            header = None
            continue
        if section is None:
            continue
        for label_line in (line,):
            for label, url in LINK_RX.findall(label_line):
                bold = BOLD_RX.search(label_line)
                name = _clean(bold.group(1)) if bold else _clean(label)
                section["links"].append({"ten": name.split(" · ")[0], "url": url})
        if not line.startswith("|"):
            continue
        cells = _cells(line)
        if all(set(c) <= set("-: ") for c in cells):
            continue                                    # dòng kẻ |---|---|
        if cells and cells[0].strip("* ").lower() == "giờ":
            header = [c.strip("* ").lower() for c in cells]
            continue
        if header is None or section["ngay"] is None:
            continue
        m = TIME_RX.match(cells[0])
        if not m:
            continue
        hh, mm = int(m.group(1)), int(m.group(2))
        if hh > 23 or mm > 59:
            warnings.append(f"Giờ lạ «{cells[0]}» ở {section['tieu_de']} — bỏ dòng này.")
            continue
        col = {name: (cells[i] if i < len(cells) else "") for i, name in enumerate(header)}
        day = section["ngay"]
        prev = section["events"][-1]["start"] if section["events"] else None
        start = datetime.combine(day, datetime.min.time()).replace(hour=hh, minute=mm)
        while prev is not None and start <= prev:
            start += timedelta(days=1)                  # qua nửa đêm
        place_raw = col.get("điểm dừng") or col.get("điểm") or col.get("địa điểm") or ""
        bold = BOLD_RX.search(place_raw)
        place = _clean(place_raw)
        name = _clean(bold.group(1)) if bold else place.split(" – ")[0]
        what = _clean(col.get("làm gì") or col.get("hoạt động") or "")
        note = _clean(col.get("ghi chú") or "")
        ev = {"start": start, "ten": name, "dia_diem": place, "lam_gi": what, "ghi_chu": note,
              "gio_ghi_trong_tep": cells[0].strip(), "phan": section["tieu_de"]}
        section["events"].append(ev)
        if len(events) + sum(len(s["events"]) for s in sections) > MAX_EVENTS:
            warnings.append(f"Tệp có hơn {MAX_EVENTS} dòng giờ — chỉ lấy {MAX_EVENTS} dòng đầu.")
            break
    for s in sections:
        evs = s["events"]
        for i, ev in enumerate(evs):
            nxt = evs[i + 1]["start"] if i + 1 < len(evs) else None
            dur = _duration(ev["lam_gi"], ev["ghi_chu"])
            if dur is not None and (nxt is None or ev["start"] + dur <= nxt):
                ev["end"] = ev["start"] + dur
            else:
                ev["end"] = nxt if nxt is not None and nxt - ev["start"] <= MAX_GAP else ev["start"] + DEFAULT_LEN
            if i == 0 and s["links"]:
                ev["links"] = s["links"]
            events.append(ev)
    out = []
    for i, ev in enumerate(events, start=1):
        title = ev["ten"] + (f" — {ev['lam_gi']}" if ev["lam_gi"] else "")
        desc = [f"Giờ trong tệp: {ev['gio_ghi_trong_tep']}", ev["dia_diem"]]
        if ev["ghi_chu"]:
            desc.append(f"Ghi chú: {ev['ghi_chu']}")
        for link in ev.get("links", []):
            desc.append(f"Bản đồ {link['ten']}: {link['url']}")
        out.append({"stt": i, "ngay": ev["start"].strftime("%d/%m/%Y"), "thu": weekday_of(ev["start"].date()),
                    "bat_dau": ev["start"].isoformat(timespec="minutes"), "ket_thuc": ev["end"].isoformat(timespec="minutes"),
                    "tieu_de": title[:200], "dia_diem": ev["dia_diem"][:300], "mo_ta": "\n".join(d for d in desc if d),
                    "phan": ev["phan"]})
    for a, b in zip(out, out[1:]):
        if b["bat_dau"] < a["ket_thuc"]:
            warnings.append(f"Sự kiện {a['stt']} và {b['stt']} chồng giờ — hỏi lại người dùng trước khi tạo.")
    links = [{"phan": s["tieu_de"], **l} for s in sections for l in s["links"]]
    return {"su_kien": out, "doan_map": links, "canh_bao": warnings}


__all__ = ["extract", "weekday_of", "WEEKDAYS"]
