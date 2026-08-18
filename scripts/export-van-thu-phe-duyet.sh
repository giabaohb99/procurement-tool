#!/usr/bin/env bash
#
# Xuất DỮ LIỆU hai phân hệ VĂN THƯ và PHÊ DUYỆT ra một tệp .sql để đồng bộ sang
# môi trường khác (dev-UAT / prod).
#
#   ./scripts/export-van-thu-phe-duyet.sh            # ra db-export/van-thu-phe-duyet-<ngày>.sql
#   ./scripts/export-van-thu-phe-duyet.sh /tmp/a.sql # chỉ định tệp
#
# ⚠️ CHỈ DỮ LIỆU, KHÔNG có CREATE TABLE — sơ đồ bảng do Alembic quản lý. Chạy
#    `alembic upgrade head` ở đích TRƯỚC khi nạp tệp này.
#
# ⚠️ Tệp sinh ra XÓA SẠCH dữ liệu hai phân hệ ở đích rồi nạp lại (DELETE + INSERT
#    trong một giao dịch). Đây là đồng bộ MỘT CHIỀU: mọi văn bản, luồng duyệt,
#    phiên duyệt đang có ở đích sẽ mất.
#
# ⚠️ Dữ liệu tham chiếu sang phân hệ khác bằng ID: `company_id`, `department_id`,
#    `owner_employee_id`, `approver_ref`… Nếu đích có bộ pháp nhân / nhân sự
#    KHÁC id, văn bản sẽ trỏ nhầm người. Kiểm tra trước khi nạp.
set -euo pipefail

DICH="${1:-db-export/van-thu-phe-duyet-$(date +%Y%m%d-%H%M).sql}"
mkdir -p "$(dirname "$DICH")"

#  Thứ tự bảng = thứ tự NẠP: danh mục trước, bản ghi nghiệp vụ sau. Tệp có tắt
#  kiểm khóa ngoại nên thứ tự không bắt buộc, nhưng giữ đúng để đọc tệp ra còn
#  hiểu được phân hệ dựng từ đâu, và để nạp từng phần cũng chạy được.
BANG=(
  # ── Danh mục Văn thư ────────────────────────────────────────────────────
  tab_doc_type
  tab_doc_type_link_rule
  tab_document_book
  tab_document_book_member
  tab_document_numbering_rule
  tab_document_numbering_rule_doc_type
  tab_document_numbering_rule_book
  tab_external_party
  tab_document_template
  tab_number_sequence
  # ── Bản ghi Văn thư ─────────────────────────────────────────────────────
  tab_document
  tab_document_version
  tab_document_link
  tab_document_scope
  tab_document_access
  tab_document_recipient
  tab_document_request
  tab_document_clone_plan
  tab_incoming_register
  # ── Phê duyệt ───────────────────────────────────────────────────────────
  tab_approval_flow
  tab_approval_node
  tab_approval_switch
  tab_delegation
  tab_approval_instance
  tab_approval_task
  tab_approval_action
)

echo "Đang xuất ${#BANG[@]} bảng…"

{
  echo "-- Dữ liệu phân hệ VĂN THƯ + PHÊ DUYỆT"
  echo "-- Sinh lúc: $(date '+%d/%m/%Y %H:%M')"
  echo "-- Chỉ dữ liệu; chạy 'alembic upgrade head' ở đích trước khi nạp."
  echo "-- Tệp này XÓA dữ liệu hai phân hệ ở đích rồi nạp lại."
  echo
  echo "SET NAMES utf8mb4;"
  echo "SET FOREIGN_KEY_CHECKS = 0;"
  echo "START TRANSACTION;"
  echo
  #  Xóa theo thứ tự NGƯỢC với thứ tự nạp: bản ghi con trước, danh mục sau.
  for (( i=${#BANG[@]}-1; i>=0; i-- )); do
    echo "DELETE FROM ${BANG[$i]};"
  done
  echo
} > "$DICH"

#  `--complete-insert` ghi kèm tên cột: đích thêm cột mới (Alembic chạy trước)
#  thì tệp vẫn nạp được, thay vì đổ lỗi lệch số cột.
#  `--default-character-set=utf8mb4` là bắt buộc — thiếu nó tiếng Việt thành
#  mojibake ngay trong tệp xuất, và lỗi đó không cứu được sau khi đã nạp.
docker compose exec -T db sh -lc '
  mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" \
    --default-character-set=utf8mb4 \
    --no-create-info --skip-add-locks --skip-disable-keys \
    --skip-add-drop-table --complete-insert --single-transaction \
    --set-gtid-purged=OFF \
    "$MYSQL_DATABASE" '"${BANG[*]}"' 2>/dev/null
' >> "$DICH"

{
  echo
  echo "COMMIT;"
  echo "SET FOREIGN_KEY_CHECKS = 1;"
} >> "$DICH"

echo "Xong: $DICH ($(du -h "$DICH" | cut -f1))"
echo
echo "Nạp ở đích:"
echo "  docker compose exec -T db sh -lc 'mysql -uroot -p\"\$MYSQL_ROOT_PASSWORD\" \"\$MYSQL_DATABASE\"' < $DICH"
