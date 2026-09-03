# -*- coding: utf-8 -*-
"""Replay bài mẫu diễn đàn từ môi trường này sang môi trường khác QUA API THẬT.

Hai bước, hai chỗ chạy:

1. XUẤT (chạy TRONG container api của môi trường nguồn — cần app.*):
       docker compose exec -T api python scripts/replay_forum_posts.py export \\
           --ids 28,32-43 > forum_export.json
   In JSON ra stdout: bài (body/format/audience/kind/box THEO TÊN/title/prefix)
   + comment (cây 2 cấp) + reaction, tác giả ghi bằng MÃ ĐĂNG NHẬP.

2. ĐĂNG LẠI (chạy trên máy host, cần `requests`, KHÔNG cần app.*):
       python backend/scripts/replay_forum_posts.py replay \\
           --file forum_export.json --base https://devthumua.degoholding.vn

Vì sao qua API chứ không dump DB: giữ nguyên mọi luật của service (sanitize
rich text, ép audience theo box, chuông, đếm), và id bài/comment hai bên
khác nhau nên script tự remap (box map theo TÊN — id box hai môi trường
không trùng nhau).

Chống đăng trùng theo cặp (title, 60 ký tự body đầu) so với feed đích —
chạy lại không đăng đúp. Bài có FILE đính kèm chưa hỗ trợ (đợt bài mẫu
28+32-43 ảnh toàn link ngoài trong HTML rich nên không cần); muốn thêm thì
phải tải file về rồi upload lại qua /api/attachments.

Tài khoản demo phải TỒN TẠI ở môi trường đích với đúng mật khẩu quy ước
(mã đăng nhập = mật khẩu, riêng nhóm DEMO_* dùng demo123). KHÔNG chạy
replay vào prod — prod chưa có diễn đàn và không có tài khoản demo.
"""
import argparse
import json
import sys

DEMO_PASSWORDS = {
    "TESTREQ": "TESTREQ",
    "DEMOTP": "DEMOTP",
    "DEMONV": "DEMONV",
    "DEMOQL": "DEMOQL",
    "DEMO_MANAGER_PURCHASE": "demo123",
}


def parse_id_ranges(raw: str) -> list[int]:
    """"28,32-43" -> [28, 32, 33, ..., 43]."""
    ids: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            ids.extend(range(int(lo), int(hi) + 1))
        elif part:
            ids.append(int(part))
    return ids


# ---------------------------------------------------------------- export ----

def run_export(ids: list[int]) -> None:
    sys.path.insert(0, "/app")  # chạy dạng scripts/x.py thì /app không tự có trong sys.path
    from app.core.database import SessionLocal
    import app.core.all_models  # noqa: F401 — nạp đủ mapper trước khi query
    from app.modules.forum.model import ForumBoard, ForumPost, ForumReaction
    from app.modules.comment.model import Comment
    from app.modules.user.model import User

    db = SessionLocal()
    users = dict(db.query(User.id, User.email).all())
    boards = {b.id: b.name for b in db.query(ForumBoard).all()}
    out = []
    for pid in ids:
        p = db.get(ForumPost, pid)
        if p is None:
            print(f"BO QUA: khong co bai {pid}", file=sys.stderr)
            continue
        comments = (db.query(Comment)
                    .filter(Comment.entity == "forum_post", Comment.entity_id == pid)
                    .order_by(Comment.id).all())
        reactions = (db.query(ForumReaction)
                     .filter(ForumReaction.post_id == pid)
                     .order_by(ForumReaction.id).all())
        out.append({
            "local_id": pid,
            "author": users.get(p.created_by),
            "body": p.body,
            "body_format": p.body_format,
            "audience": p.audience,
            "kind": p.kind,
            "board_name": boards.get(p.board_id),
            "title": p.title or "",
            "prefix": p.prefix,
            "comments": [{
                "local_id": c.id,
                "author": users.get(c.created_by),
                "body": c.body,
                "parent_id": c.parent_id,
                "reply_to_user_id": c.reply_to_user_id,
            } for c in comments],
            "reactions": [{"user": users.get(r.created_by), "kind": r.kind}
                          for r in reactions],
        })
    print(json.dumps(out, ensure_ascii=False, indent=1))


# ---------------------------------------------------------------- replay ----

def login(base: str, username: str) -> dict:
    import requests

    r = requests.post(f"{base}/api/auth/login",
                      json={"username": username, "password": DEMO_PASSWORDS[username]},
                      timeout=30)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        raise RuntimeError(f"login {username}: {data}")
    return {"Authorization": f"Bearer {data['data']['access_token']}"}


def call_api(base: str, method: str, path: str, headers: dict, **kw):
    import requests

    r = requests.request(method, f"{base}{path}", headers=headers, timeout=60, **kw)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        raise RuntimeError(f"{method} {path}: {data}")
    return data["data"]


def collect_boxes(node, acc: dict) -> None:
    """Đi qua mọi dict trong cây board, gom {name: id} của BOX (parent_id > 0)."""
    if isinstance(node, dict):
        if node.get("id") and node.get("name") and node.get("parent_id"):
            acc[node["name"]] = node["id"]
        for v in node.values():
            collect_boxes(v, acc)
    elif isinstance(node, list):
        for v in node:
            collect_boxes(v, acc)


def run_replay(base: str, export_file: str) -> None:
    posts = json.load(open(export_file, encoding="utf-8"))

    accounts = set()
    for p in posts:
        accounts.add(p["author"])
        accounts.update(c["author"] for c in p["comments"])
        accounts.update(r["user"] for r in p["reactions"])
    unknown = accounts - set(DEMO_PASSWORDS)
    if unknown:
        sys.exit(f"Khong biet mat khau cac tai khoan: {sorted(unknown)} — "
                 "bo bai cua ho khoi file export hoac bo sung DEMO_PASSWORDS.")

    headers = {}
    for acc in sorted(accounts):
        headers[acc] = login(base, acc)
        print(f"login OK: {acc}")
    any_h = next(iter(headers.values()))

    box_by_name: dict = {}
    collect_boxes(call_api(base, "GET", "/api/forum/boards", any_h), box_by_name)
    need = {p["board_name"] for p in posts if p["board_name"]}
    missing = need - set(box_by_name)
    if missing:
        sys.exit(f"Moi truong dich THIEU box: {missing} — chay seed_forum_boards.py truoc.")

    # Chống trùng: bài box vẫn ra feed (QĐ-D7b) nên quét feed là đủ
    existing = set()
    feed = call_api(base, "GET", "/api/forum/posts?limit=50", any_h)
    for item in feed.get("items", []):
        existing.add((item.get("title") or "", (item.get("body") or "")[:60]))

    created = 0
    for p in posts:
        if ((p["title"] or "", (p["body"] or "")[:60])) in existing:
            print(f"SKIP (da co): local {p['local_id']} — {(p['title'] or p['body'])[:40]!r}")
            continue
        out = call_api(base, "POST", "/api/forum/posts", headers[p["author"]], json={
            "body": p["body"],
            "body_format": p["body_format"],
            "audience": p["audience"],
            "kind": p["kind"],
            "board_id": box_by_name[p["board_name"]] if p["board_name"] else 0,
            "title": p["title"],
            "prefix": p["prefix"],
        })
        new_pid = out["id"]
        created += 1
        print(f"POST local {p['local_id']} -> {new_pid} [{p['author']}] box={p['board_name']}")

        comment_map: dict[int, int] = {}
        for c in p["comments"]:
            cout = call_api(base, "POST", "/api/comments", headers[c["author"]], json={
                "entity": "forum_post",
                "entity_id": new_pid,
                "body": c["body"],
                "parent_id": comment_map.get(c["parent_id"], 0),
                "reply_to_user_id": c["reply_to_user_id"],
            })
            comment_map[c["local_id"]] = cout["id"]
            print(f"  comment {c['local_id']} -> {cout['id']} [{c['author']}]")

        for r in p["reactions"]:
            call_api(base, "POST", f"/api/forum/posts/{new_pid}/like",
                     headers[r["user"]], json={"kind": r["kind"]})
            print(f"  reaction kind={r['kind']} [{r['user']}]")

    print(f"XONG: dang {created} bai moi.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="mode", required=True)

    ap_export = sub.add_parser("export", help="xuat bai tu DB (chay trong container api)")
    ap_export.add_argument("--ids", required=True, help='vd "28,32-43"')

    ap_replay = sub.add_parser("replay", help="dang lai qua API (chay tren host)")
    ap_replay.add_argument("--file", required=True, help="duong dan JSON da xuat")
    ap_replay.add_argument("--base", default="https://devthumua.degoholding.vn",
                           help="goc API dich (mac dinh dev)")

    args = ap.parse_args()
    if args.mode == "export":
        run_export(parse_id_ranges(args.ids))
    else:
        run_replay(args.base.rstrip("/"), args.file)


if __name__ == "__main__":
    main()
