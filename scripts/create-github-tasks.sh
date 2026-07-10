#!/usr/bin/env bash
# Tạo các task hôm nay (09/07/2026) thành GitHub Issues, gắn vào Project #1 (Thumua), đặt cột Done.
# Yêu cầu: gh CLI đã đăng nhập + có quyền project.
#   gh auth login                 # nếu chưa đăng nhập
#   gh auth refresh -s project    # cấp thêm quyền Projects
# Chạy:  bash scripts/create-github-tasks.sh
# LƯU Ý: chạy 2 lần sẽ tạo issue TRÙNG. Chỉ chạy 1 lần.
set -euo pipefail

OWNER="giabaohb99"
REPO="giabaohb99/procurement-tool"
PROJ=1

command -v gh >/dev/null || { echo "Chưa cài gh CLI: https://cli.github.com/"; exit 1; }
command -v python >/dev/null || command -v python3 >/dev/null || { echo "Cần python để parse JSON"; exit 1; }
PY=$(command -v python || command -v python3)

echo "→ Lấy thông tin Project #$PROJ ($OWNER)…"
PROJID=$(gh project view $PROJ --owner "$OWNER" --format json | "$PY" -c "import sys,json;print(json.load(sys.stdin)['id'])")
read -r STATUS_FID DONE_OID < <(gh project field-list $PROJ --owner "$OWNER" --format json | "$PY" -c "
import sys,json
d=json.load(sys.stdin)
for f in d.get('fields',[]):
    if f.get('name')=='Status':
        done=[o['id'] for o in f.get('options',[]) if o['name']=='Done']
        if done: print(f['id'], done[0]); break
")
[ -n "${STATUS_FID:-}" ] || { echo "Không tìm thấy field Status/Done"; exit 1; }
echo "  project=$PROJID status_field=$STATUS_FID done=$DONE_OID"

add() {  # $1=title  $2=body
  local url itemid
  url=$(gh issue create --repo "$REPO" --title "$1" --body "$2" | tail -1)
  itemid=$(gh project item-add $PROJ --owner "$OWNER" --url "$url" --format json | "$PY" -c "import sys,json;print(json.load(sys.stdin)['id'])")
  gh project item-edit --id "$itemid" --project-id "$PROJID" --field-id "$STATUS_FID" --single-select-option-id "$DONE_OID" >/dev/null
  # gh issue close "$url" >/dev/null   # bỏ dấu # nếu muốn đóng luôn issue
  echo "  ✓ $1"
  echo "     $url"
}

echo "→ Tạo issues + gắn board (Done)…"
add "Mã SP hệ thống: option khảo sát → Yêu cầu mua hàng" \
"Gắn mã SP hệ thống cho option khảo sát, tự chảy sang dòng PYC. Chuyển mã vào popup dòng khảo sát, back-propagate chỉ điền khi rỗng; bỏ mã SP trên item (header đã có Mã VTBB/VL). Commits: 9388603, 5879e62, f2fd812, 384a398, 35ed3c4."

add "Đính kèm file khảo sát: upload ngay + tách 2 bảng" \
"Upload ngay khi chọn + thanh progress, giới hạn 10MB. Tách tab_file (file) + tab_file_link (liên kết), clear data cũ; fix gắn file chờ đúng dòng sau khi lưu. Commits: aa804c2, c3e5a89, 0376955, 40c9626."

add "Nháp khảo sát: cho lưu dòng dở dang + fix 422" \
"Cho lưu dòng chưa đủ (không bắt buộc chọn NCC/Tên SP khi Lưu). Fix lỗi 422 do vat=\"\" khiến cả phiếu SP không lưu được. Commits: 6206c83, e643296."

add "Thông báo: thay alert() bằng toast dùng chung" \
"Thay toàn bộ alert() trình duyệt bằng hệ thống toast chung (CrudList, AppLayout, Dashboard, Payables, SurveyReport). Commit: f5ba789."

add "Xác nhận: modal chung thay confirm()/prompt()" \
"Modal xác nhận / nhập lý do dùng chung (askConfirm/askPrompt) thay tất cả confirm()/prompt() trình duyệt ở 12 file. Commit: b46f791."

add "Validate Gửi duyệt: tô đỏ ô thiếu + báo theo dòng" \
"Gom tất cả ô bắt buộc còn trống, báo theo dòng (VD: 'Khảo sát Sản phẩm dòng 1,2,3 còn thiếu…'), tô đỏ nhẹ trong bảng + popup chi tiết. Commits: f5ba789, ab6d2ac, 388d184."

add "Luật nút phiếu khảo sát theo trạng thái" \
"Nháp: bỏ badge + Hủy phiếu, chỉ Lưu/Gửi duyệt/Xóa. Chờ duyệt: Duyệt/Từ chối/Trả lại. 'Bị trả lại' cho sửa lại + gửi duyệt lại. Commit: ab6d2ac."

add "Fix lệch giờ +7 (hiển thị giờ VN)" \
"Container chạy UTC, timestamp naive bị hiểu là giờ local → lệch 7h. Thêm util fmtDateTime (coi naive là UTC → Asia/Ho_Chi_Minh), áp cho lịch sử ở Survey/PO/PR/SurveyRequest/CrudDetail. Commit: ab6d2ac."

add "Fix UI khảo sát: ô Duyệt lòi cột, bỏ Thành tiền, số 0, NCC" \
"Ô trong bảng dùng width 100% (hết lòi cột Duyệt). Bỏ cột + Tổng 'Thành tiền' ở bảng ngoài (giữ trong popup). Số 0 để trống + hết dính số 0 đầu. NCC không bắt buộc; tô đỏ nhẹ; bỏ tự mở popup. Commits: 388d184, 671d1c6."

add "Báo cáo khảo sát (giao diện)" \
"Xây giao diện màn Báo cáo khảo sát. Commit: 0d03c9e/532b78a."

add "Yêu cầu mua hàng: xóa nhiều + popup xác nhận + chặn xóa" \
"API xóa nhiều item trong purchase-requests, cập nhật UI input/custom select, popup xác nhận xóa, chặn xóa đơn không phải nháp. Commits: 9cd7216, 6bcfc7d, 4dfd46d, 5a90a7f."

echo "✅ Xong. Mở board: https://github.com/users/$OWNER/projects/$PROJ/views/3"
