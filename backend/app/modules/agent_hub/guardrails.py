"""LAN CAN của bot: tệp bot code không được đụng + phân loại lệnh trên VPS (ai-CR-067, V-03 + V-05).

Gom về MỘT tệp để luật V-05 khóa được chính nó: bot code không được sửa sổ quyền, phần lệnh prod, và danh
sách tệp cấm của chính mình. Tệp này nằm trong `BANNED_PATTERNS` của chính nó — bản vá nào đụng vào đây đều
dừng ở cổng lệch kế hoạch và leo thang cho đại ca, không bao giờ tự gộp.

Ba nhóm luật:
  1. `BANNED_PATTERNS` — tệp cấm khi sửa mã (luật C3, C4, §E, §G + ba luật tự cải thiện V-05).
  2. `classify_shell` / `classify_sql` — lệnh đại ca gõ cho VPS là CHỈ ĐỌC hay SỬA. Chỉ đọc trên dev thì
     chạy luôn; còn lại phải «đúng». Lệnh đụng bí mật (.env, khóa, mật khẩu) bị từ chối thẳng, kể cả chỉ đọc.
  3. `mask_secrets` — che mọi chuỗi giống bí mật trong kết quả trước khi lên Telegram hay vào sổ.
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# 1. Tệp cấm (so bằng fnmatch trên cả đường dẫn đầy đủ lẫn tên tệp — xem coder.is_banned_path)
# ---------------------------------------------------------------------------
#  Mở rộng danh sách này thì sửa cả bài kiểm `test_tep_cam_thi_leo_thang` và `test_ba_luat_tu_cai_thien`.
BANNED_PATTERNS = (
    ".env", ".env.*",
    "*.pem", "*.key", "*.p12",
    "backend/app/seed_prod.py",
    "backend/migrations/versions/*",          # C3: không migration
    ".github/workflows/*",                    # C4
    "docker-compose.production.yml",          # C4
    "backend/app/core/permissions.py",        # C4: không đụng phân quyền
    "backend/app/core/scoping.py",
    "CLAUDE.md", "*/CLAUDE.md",               # §G: không tự sửa luật của mình
    ".claude/*", "*/.claude/*",
    "doc/agent-hub/02-bo-quy-tac-bot.md",
    "doc/agent-hub/03-so-quyet-dinh.md",      # ai-CR-015: sổ chỉ ghi qua nút đại ca duyệt
    #  V-05 — ba luật tự cải thiện (đại ca chốt 05/10/2026): bot tự sửa được mã của chính nó qua bot code,
    #  NHƯNG không được sửa (1) sổ quyền ra lệnh, (2) cổng duyệt + lệnh prod, (3) danh sách cấm này.
    "backend/app/modules/agent_hub/grants.py",       # (1) ai được ra lệnh sửa mã ở cấp nào
    "backend/app/modules/agent_hub/runners.py",      # (1) máy nào được deploy
    "backend/app/modules/agent_hub/ops.py",          # (2) cổng duyệt thao tác VPS, phân dev/prod
    "backend/app/modules/agent_hub/ops_runner.py",   # (2) phần thi hành trên VPS, sao lưu, tự chữa
    "backend/scripts/deploy/*",                      # (2) deploy.sh — kịch bản lên dev/prod
    "backend/app/modules/agent_hub/guardrails.py",   # (3) chính tệp này
)


# ---------------------------------------------------------------------------
# 2a. Lệnh shell
# ---------------------------------------------------------------------------
SHELL_READ = "read"
SHELL_WRITE = "write"
SHELL_DENIED = "denied"

#  Lệnh đầu của từng đoạn (tách theo | && ; ||) mà coi là chỉ đọc. Chỉ ĐỌC thật: không có `docker exec`
#  (chạy được mọi thứ trong container), không `sed` (có -i), không `find` (có -delete / -exec).
_READ_HEADS = (
    "docker ps", "docker compose ps", "docker compose logs", "docker logs", "docker stats --no-stream",
    "docker system df", "docker images", "docker inspect", "docker compose config --services",
    "df", "du", "free", "uptime", "cat", "tail", "head", "grep", "egrep", "zgrep", "ls", "wc", "sort",
    "uniq", "awk", "cut", "date", "hostname", "nproc", "whoami", "ps", "top -bn1", "pwd", "echo",
    "git log", "git status", "git rev-parse", "git show --stat", "git diff --stat", "git branch",
    "curl -s", "curl -sS", "curl -I", "curl -sI", "journalctl", "systemctl status", "ss -", "netstat",
    "stat", "file", "jq", "vmstat", "iostat", "lsblk", "mount",
)
#  Đụng bí mật thì từ chối, kể cả lệnh chỉ đọc: kết quả sẽ lên Telegram.
_SECRET_HINT = re.compile(
    r"\.env\b|\bprintenv\b|(^|[\s;|&])env(\s|$)|\bset\s*$|/proc/\S*/environ|id_(rsa|ed25519|ecdsa)|\.pem\b|\.key\b|"
    r"authorized_keys|known_hosts|\.ssh/|secret|token|passw|credential|vps_ssh_key|\.p12\b|"
    r"MYSQL_ROOT|JWT_|OAUTH|docker\s+(compose\s+)?config(?!\s+--services)|docker\s+inspect\b.*\benv\b",
    re.IGNORECASE)
#  Thứ không bao giờ chạy qua bot, dù đại ca có «đúng»: xóa hàng loạt, xóa volume, định dạng đĩa, tắt máy.
_NEVER = re.compile(
    r"\brm\s+-[a-z]*r[a-z]*f?\s+(/|~|\$HOME|\*)(\s|$)|\bmkfs|\bdd\s+if=|\bshutdown\b|\breboot\b|\bhalt\b|"
    r"\bdown\b.*(\s-v\b|--volumes)|docker\s+volume\s+(rm|prune)|docker\s+system\s+prune\b.*--volumes|"
    r":\(\)\s*\{|\bchmod\s+-R\s+777\s+/|\bDROP\s+DATABASE\b",
    re.IGNORECASE)
_SPLIT = re.compile(r"\|\||&&|;|\||\n")


def classify_shell(cmd: str) -> tuple[str, str]:
    """(loại, lý do). Chỉ đọc khi MỌI đoạn bắt đầu bằng lệnh trong danh sách đọc và không có chuyển hướng
    ghi (`>`), không thay lệnh (`$(`, dấu huyền). Đụng bí mật / nằm trong danh sách cấm hẳn → từ chối."""
    text = (cmd or "").strip()
    if not text:
        return SHELL_DENIED, "lệnh trống"
    if _NEVER.search(text):
        return SHELL_DENIED, "lệnh nằm trong danh sách bot không bao giờ chạy (xóa hàng loạt, xóa volume, tắt máy…)"
    if _SECRET_HINT.search(text):
        return SHELL_DENIED, "lệnh đụng tới bí mật (.env, khóa, mật khẩu, token) — kết quả sẽ lên Telegram nên em không chạy"
    if re.search(r"(?<![0-9&])>|\$\(|`|\btee\b|\bxargs\b|\bsudo\b", text):
        return SHELL_WRITE, "có ghi tệp / thay lệnh"
    parts = [p.strip() for p in _SPLIT.split(text) if p.strip()]
    for p in parts:
        low = re.sub(r"\s+", " ", p.lower())
        if not any(low == h or low.startswith(h + " ") or (h.endswith("-") and low.startswith(h)) for h in _READ_HEADS):
            return SHELL_WRITE, f"«{p[:40]}» không nằm trong danh sách lệnh chỉ đọc"
    return SHELL_READ, ""


# ---------------------------------------------------------------------------
# 2b. Câu SQL
# ---------------------------------------------------------------------------
SQL_READ = "read"
SQL_WRITE = "write"
SQL_DENIED = "denied"
_SQL_READ_HEAD = re.compile(r"^\s*(select|show|describe|desc|explain|with)\b", re.IGNORECASE)
_SQL_WRITE_HEAD = re.compile(r"^\s*(update|insert|delete|replace)\b", re.IGNORECASE)
_SQL_DENY = re.compile(r"\b(drop|truncate|grant|revoke|create\s+user|alter\s+user|set\s+password|"
                       r"rename\s+table|into\s+outfile|into\s+dumpfile|load_file|load\s+data|shutdown|"
                       r"lock\s+tables|kill)\b", re.IGNORECASE)
_SQL_TABLE = re.compile(r"\b(?:update|into|from|join)\s+`?([A-Za-z0-9_]+)`?", re.IGNORECASE)
_SQL_SECRET_COLS = re.compile(r"\b(password|password_hash|hashed_password|token\w*|\w*_secret|\w*_enc|key_enc|"
                              r"refresh_token\w*|totp\w*|otp\w*)\b", re.IGNORECASE)


def _strip_sql_literals(sql: str) -> str:
    return re.sub(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"", "''", sql)


def classify_sql(sql: str) -> tuple[str, str, list[str]]:
    """(loại, lý do, bảng). Một câu một lần (dấu `;` giữa câu = từ chối). DDL / phân quyền MySQL / ghi tệp
    = từ chối. UPDATE / DELETE không có WHERE = từ chối (đại ca muốn cả bảng thì gõ `WHERE 1=1` cho rõ ý)."""
    text = (sql or "").strip().rstrip(";").strip()
    if not text:
        return SQL_DENIED, "câu SQL trống", []
    bare = _strip_sql_literals(text)
    if ";" in bare:
        return SQL_DENIED, "mỗi lần một câu SQL thôi", []
    if re.search(r"--|/\*|#", bare):
        return SQL_DENIED, "câu SQL có chú thích — bỏ chú thích đi giúp em", []
    if _SQL_DENY.search(bare):
        return SQL_DENIED, "loại câu này bot không chạy (DROP / TRUNCATE / GRANT / ghi tệp…)", []
    if re.match(r"^\s*(alter|create)\b", bare, re.IGNORECASE):
        return SQL_DENIED, "đổi cấu trúc bảng phải qua migration, không qua bot", []
    tables = list(dict.fromkeys(m.group(1) for m in _SQL_TABLE.finditer(bare)))
    if _SQL_READ_HEAD.match(bare):
        if _SQL_SECRET_COLS.search(bare) or re.search(r"\bselect\s+\*\s+from\s+`?(tab_user|tab_agent_user_key|"
                                                     r"tab_agent_google_link|tab_agent_mcp_key|tab_setting)\b",
                                                     bare, re.IGNORECASE):
            return SQL_DENIED, "câu này đọc cột bí mật (mật khẩu / token / khóa) — chọn đúng cột cần xem", tables
        return SQL_READ, "", tables
    if _SQL_WRITE_HEAD.match(bare):
        if re.match(r"^\s*(update|delete)\b", bare, re.IGNORECASE) and not re.search(r"\bwhere\b", bare, re.IGNORECASE):
            return SQL_DENIED, "UPDATE / DELETE thiếu WHERE — muốn cả bảng thì ghi rõ `WHERE 1=1`", tables
        if not tables:
            return SQL_DENIED, "em không đọc ra được bảng nào để sao lưu trước", []
        return SQL_WRITE, "", tables
    return SQL_DENIED, "chỉ nhận SELECT / SHOW / EXPLAIN và UPDATE / INSERT / DELETE / REPLACE", []


# ---------------------------------------------------------------------------
# 3. Che bí mật trong kết quả
# ---------------------------------------------------------------------------
_MASKS = (
    (re.compile(r"(?i)\b([A-Z0-9_]*(PASSWORD|PASSWD|SECRET|TOKEN|API_KEY|PRIVATE_KEY|ACCESS_KEY)[A-Z0-9_]*)\s*[=:]\s*\S+"),
     r"\1=***"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"), "[khóa riêng đã che]"),
    (re.compile(r"\b(ghp|gho|ghs|github_pat)_[A-Za-z0-9_]{16,}"), "[token GitHub đã che]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"), "[khóa API đã che]"),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{20,}"), "[khóa Google đã che]"),
    (re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{30,}"), "[token Telegram đã che]"),
    (re.compile(r"(?i)(mysql|redis|postgres(ql)?|amqp)://[^:\s/]+:[^@\s]+@"), r"\1://***:***@"),
)


def mask_secrets(text: str) -> str:
    out = text or ""
    for pat, rep in _MASKS:
        out = pat.sub(rep, out)
    return out
