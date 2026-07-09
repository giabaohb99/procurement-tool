# -*- coding: utf-8 -*-
"""
Tạo các task hôm nay (09/07/2026) thành GitHub Issues, gắn vào Project #1 (Thumua), đặt cột Done.
Chạy được thẳng trong CMD/PowerShell (KHÔNG cần bash/WSL):

    python scripts/create_github_tasks.py

Yêu cầu: đã cài gh CLI và đăng nhập (gh auth login) + có quyền project:
    gh auth refresh -s project

LƯU Ý: chạy 2 lần sẽ tạo issue TRÙNG. Chỉ chạy 1 lần.
"""
import json
import shutil
import subprocess
import sys

OWNER = "giabaohb99"
REPO = "giabaohb99/procurement-tool"
PROJ = "1"

TASKS = [
    ("Mã SP hệ thống: option khảo sát → Yêu cầu mua hàng",
     "Gắn mã SP hệ thống cho option khảo sát, tự chảy sang dòng PYC. Chuyển mã vào popup dòng khảo sát, "
     "back-propagate chỉ điền khi rỗng; bỏ mã SP trên item (header đã có Mã VTBB/VL). "
     "Commits: 9388603, 5879e62, f2fd812, 384a398, 35ed3c4."),
    ("Đính kèm file khảo sát: upload ngay + tách 2 bảng",
     "Upload ngay khi chọn + thanh progress, giới hạn 10MB. Tách tab_file (file) + tab_file_link (liên kết), "
     "clear data cũ; fix gắn file chờ đúng dòng sau khi lưu. Commits: aa804c2, c3e5a89, 0376955, 40c9626."),
    ("Nháp khảo sát: cho lưu dòng dở dang + fix 422",
     "Cho lưu dòng chưa đủ (không bắt buộc chọn NCC/Tên SP khi Lưu). Fix lỗi 422 do vat rỗng khiến cả phiếu SP "
     "không lưu được. Commits: 6206c83, e643296."),
    ("Thông báo: thay alert() bằng toast dùng chung",
     "Thay toàn bộ alert() trình duyệt bằng hệ thống toast chung (CrudList, AppLayout, Dashboard, Payables, "
     "SurveyReport). Commit: f5ba789."),
    ("Xác nhận: modal chung thay confirm()/prompt()",
     "Modal xác nhận / nhập lý do dùng chung (askConfirm/askPrompt) thay tất cả confirm()/prompt() trình duyệt "
     "ở 12 file. Commit: b46f791."),
    ("Validate Gửi duyệt: tô đỏ ô thiếu + báo theo dòng",
     "Gom tất cả ô bắt buộc còn trống, báo theo dòng (VD: 'Khảo sát Sản phẩm dòng 1,2,3 còn thiếu…'), "
     "tô đỏ nhẹ trong bảng + popup chi tiết. Commits: f5ba789, ab6d2ac, 388d184."),
    ("Luật nút phiếu khảo sát theo trạng thái",
     "Nháp: bỏ badge + Hủy phiếu, chỉ Lưu/Gửi duyệt/Xóa. Chờ duyệt: Duyệt/Từ chối/Trả lại. "
     "'Bị trả lại' cho sửa lại + gửi duyệt lại. Commit: ab6d2ac."),
    ("Fix lệch giờ +7 (hiển thị giờ VN)",
     "Container chạy UTC, timestamp naive bị hiểu là giờ local → lệch 7h. Thêm util fmtDateTime "
     "(coi naive là UTC → Asia/Ho_Chi_Minh), áp cho lịch sử ở Survey/PO/PR/SurveyRequest/CrudDetail. Commit: ab6d2ac."),
    ("Fix UI khảo sát: ô Duyệt lòi cột, bỏ Thành tiền, số 0, NCC",
     "Ô trong bảng dùng width 100% (hết lòi cột Duyệt). Bỏ cột + Tổng 'Thành tiền' ở bảng ngoài (giữ trong popup). "
     "Số 0 để trống + hết dính số 0 đầu. NCC không bắt buộc; tô đỏ nhẹ; bỏ tự mở popup. Commits: 388d184, 671d1c6."),
    ("Báo cáo khảo sát (giao diện)",
     "Xây giao diện màn Báo cáo khảo sát. Commit: 0d03c9e/532b78a."),
    ("Yêu cầu mua hàng: xóa nhiều + popup xác nhận + chặn xóa",
     "API xóa nhiều item trong purchase-requests, cập nhật UI input/custom select, popup xác nhận xóa, "
     "chặn xóa đơn không phải nháp. Commits: 9cd7216, 6bcfc7d, 4dfd46d, 5a90a7f."),
]

GH = shutil.which("gh")


def run(args, check=True):
    """Chạy gh, trả về stdout (đã strip)."""
    r = subprocess.run([GH] + args, capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)}\n{(r.stderr or r.stdout).strip()}")
    return (r.stdout or "").strip(), (r.stderr or "").strip(), r.returncode


def main():
    if not GH:
        sys.exit("✗ Chưa tìm thấy gh CLI trong PATH. Cài: winget install --id GitHub.cli, rồi mở lại cửa sổ dòng lệnh.")

    # kiểm tra đăng nhập
    _, err, code = run(["auth", "status"], check=False)
    if code != 0:
        sys.exit("✗ gh chưa đăng nhập. Chạy: gh auth login  (rồi gh auth refresh -s project)")

    print("→ Lấy thông tin Project #%s (%s)…" % (PROJ, OWNER))
    proj_out, _, _ = run(["project", "view", PROJ, "--owner", OWNER, "--format", "json"])
    proj_id = json.loads(proj_out)["id"]

    fields_out, _, _ = run(["project", "field-list", PROJ, "--owner", OWNER, "--format", "json"])
    fdata = json.loads(fields_out)
    fields = fdata["fields"] if isinstance(fdata, dict) else fdata
    status_fid = done_oid = None
    for f in fields:
        if f.get("name") == "Status":
            status_fid = f["id"]
            for o in f.get("options", []):
                if o["name"].lower() == "done":
                    done_oid = o["id"]
            break
    if not status_fid or not done_oid:
        sys.exit("✗ Không tìm thấy field 'Status' hoặc option 'Done' trong project.")
    print("  project=%s  status_field=%s  done=%s" % (proj_id, status_fid, done_oid))

    print("→ Tạo %d issue + gắn board (Done)…" % len(TASKS))
    ok = 0
    for title, body in TASKS:
        try:
            url, _, _ = run(["issue", "create", "--repo", REPO, "--title", title, "--body", body])
            url = url.splitlines()[-1].strip()  # dòng cuối là URL issue
            add_out, _, _ = run(["project", "item-add", PROJ, "--owner", OWNER, "--url", url, "--format", "json"])
            item_id = json.loads(add_out)["id"]
            run(["project", "item-edit", "--id", item_id, "--project-id", proj_id,
                 "--field-id", status_fid, "--single-select-option-id", done_oid])
            # Bỏ comment dòng dưới nếu muốn ĐÓNG issue luôn:
            # run(["issue", "close", url])
            ok += 1
            print("  ✓ %s\n     %s" % (title, url))
        except Exception as e:
            print("  ✗ LỖI ở: %s\n     %s" % (title, e))

    print("\n✅ Xong %d/%d. Mở board: https://github.com/users/%s/projects/%s/views/3"
          % (ok, len(TASKS), OWNER, PROJ))


if __name__ == "__main__":
    main()
