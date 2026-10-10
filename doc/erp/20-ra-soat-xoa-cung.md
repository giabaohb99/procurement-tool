# Rà soát xóa cứng trong backend ERP (10/10/2026)

Đại ca yêu cầu 10/10/2026: chuyển xóa phiếu sang **xóa mềm** (cột ghi nhận đã xóa / thời điểm xóa) và kiểm còn chỗ nào xóa
cứng. Bản rà đọc mã `backend/app/modules/` + `core/` trên nhánh `agent-hub-bac-1` (= `erp-v2` cùng ngày), chỉ đọc, chưa sửa gì.

## 1. Đã xóa mềm sẵn

| Chứng từ | Cột |
|---|---|
| Yêu cầu mua hàng (YCMH) | `is_deleted` |
| Đơn nghỉ phép | `is_deleted` |
| Đặt phòng họp | `is_deleted` |
| Duyệt dấu | `is_deleted` |
| Đặt xe | `is_deleted` (nhưng vẫn xóa cứng lịch sử duyệt qua `approval.instance_service.delete_by_entity`) |
| Việc Dự án | `deleted_at` |
| Phiếu hỗ trợ | không có đường xóa |

## 2. Rủi ro cao — vá trước (đợt 1)

**Tiến độ:** cả 7 mục đã vá ở ai-CR-169 (10/10). Hợp đồng «nháp» = chưa ký và chưa tới ngày bắt đầu, hoặc đã hủy (model không có trạng thái nháp riêng — muốn chặt hơn sửa `delete_block_reason`). Phiếu nhập / phát sinh kho chưa chặn vì không có cột cho biết đã có giao dịch kế tiếp.

| # | Chỗ | Vấn đề |
|---|---|---|
| 1 | `contract/controller.py` `delete_` + `bulk_delete_contracts` | **Không kiểm trạng thái**: xóa được hợp đồng đang hiệu lực / đã ký, kèm tệp |
| 2 | `import_tool` hoàn tác lô (`POST /api/imports/{bid}/revert`) | Xóa cứng mọi YCBG / YCMH / PKS / ĐMH / đặt xe / duyệt dấu của lô **ở mọi trạng thái** (kể cả đã duyệt sau khi nhập), và mọi YCTT của ĐMH đó |
| 3 | `purchase_order` sửa dòng / đợt giao → `_cleanup_delivery` | Xóa cứng phiếu nhập, xuất nhập kho, **công nợ đã thanh toán** (`payable.remove` không kiểm đã trả) — YCTT mồ côi |
| 4 | `supplier` xóa một / xóa nhiều | Không kiểm phạm vi, không kiểm đang được dùng |
| 5 | `product` xóa nhiều | Không kiểm phạm vi |
| 6 | `core/crud.py` nhập CSV hành động *xóa* | Không gọi `before_delete` → vượt rào *đang dùng* của loại hồ sơ, chức vụ, mức mật |
| 7 | `agent_hub/ops_runner.py` | Bot vận hành chạy được một câu `UPDATE/INSERT/DELETE … WHERE` do AI viết lên bảng ERP sau thẻ duyệt |

## 3. Chứng từ chính đang xóa cứng — chuyển sang xóa mềm (đợt 2)

**Tiến độ:** đợt 2a (ai-CR-170, 10/10) đã làm `SoftDeleteMixin` + lọc tập trung ở `apply_scope` / `get_scoped` và áp cho **YCBG** (migration grp11). Còn lại đợt 2b: ĐMH · YCTT · PKS · hợp đồng NCC · văn bản nháp · HĐLĐ · hồ sơ · báo cáo thực hiện.

Yêu cầu báo giá (YCBG) · Đơn mua hàng (ĐMH) · Yêu cầu thanh toán (YCTT) · Phiếu khảo sát (PKS) · Hợp đồng NCC · Văn bản
(bản nháp) · Hợp đồng lao động · Hồ sơ (dossier, qua CRUD chung) · báo cáo thực hiện (mục / giai đoạn / tài liệu).

Cách làm đề xuất: một `SoftDeleteMixin` (`is_deleted` 0/1 · `deleted_at` · `deleted_by`) + lọc **tập trung** trong
`core/scoping.apply_scope` và `get_scoped` (model có `is_deleted` thì tự thêm điều kiện chưa xóa) — phủ được phần lớn chỗ đọc
mà không phải sửa từng truy vấn. Các chỗ đọc thẳng không qua phạm vi phải lọc tay; riêng YCBG có danh sách đủ ở §5. Sinh mã
phiếu (`_gen_code`) GIỮ cả phiếu đã xóa để không tái dùng mã. Tệp đính kèm, bình luận, lịch sử duyệt của phiếu xóa mềm: giữ
nguyên. Xóa đính kèm hiện commit trước cha (`attachment.delete_attachments_for`) — không nguyên khối; xóa mềm thì bỏ luôn bước này.

## 4. Danh mục — đề xuất *ngưng dùng* thay vì xóa (đợt 3)

NCC · sản phẩm · công ty · phòng ban · nhân sự · người dùng · vai trò · danh mục CRUD chung (kho, đơn vị, nhóm hàng, thương hiệu,
loại văn bản, đối tác ngoài, ngày lễ, loại dấu, xe, tài xế…) · cấu hình (luồng duyệt, thư mục, mẫu, quy tắc đánh số…).
Đề xuất: đang được chứng từ tham chiếu thì CHẶN xóa, chỉ cho *ngưng dùng*; chưa ai dùng thì vẫn xóa được.

## 5. YCBG — mọi chỗ truy vấn phải lọc phiếu đã xóa

- `survey_request/service.py`: `get_sr` (:38), `_auto_complete_sr` (:962), `unlink_deleted_pr` (:1018), đọc lại phiếu trong
  `delete_option` (:732); `_gen_code` (:83) GIỮ phiếu đã xóa.
- `survey_request/controller.py`: `scope_condition` / `_in_scope` (:50–79), `_list_query` (:296, dùng cho danh sách + xuất
  Excel), `get_` (:383), `clone_` (:419), xóa nhiều (:440), `result_view_` (:955); báo cáo thực hiện `report_controller.py`.
- `core`: `scoping.py` (SCOPE_FIELDS :47, phạm vi *của tôi* :534–545), `attachment_scope.py` (:77–83, :297),
  `comment_registry.py` (:55), `entity_models.py` (:27, nhật ký), `file_registry.py` (:20).
- Trang chủ / tiến độ / báo cáo / xuất: `dashboard/controller.py` (:286, :514), `survey_progress/controller.py` `_build_query`
  (:205–310) và xuất Excel, `report/service.py` (:352–389 — đã tự lọc khi model có `is_deleted`), `export_log/registry.py` (:77).
- Phân hệ khác: `purchase_request/controller.py` (:322–338), `purchase_request/service.py` (:314), `survey/service.py`
  (:69, :73), `attachment/controller.py` (:461), `dossier/applicability.py` (:197, :265), `import_tool/doc_import.py` (:208),
  `legacy_datxe/mapping.py` (:208).
- Trợ lý / bot: `assistant/tools/procurement_doc_tool.py` (:105–111, :294, :312, :453, :476–482, :569–579, :624),
  `assistant/tools/update_tool.py` (:190–216, :767, :832, :943–955), `agent_hub/draft_create.py` (:474, :633–648).
- YCBG không đi qua bộ máy duyệt chung (không có lịch sử duyệt chung để giữ).

## 6. Dọn dẹp chấp nhận được (không đổi)

Thay dòng con khi sửa phiếu cha; thông báo, nhật ký, sao lưu, phiên đăng nhập, bộ đệm; bảng nội bộ của bot; các nhập / hoàn
tác có bản chụp (dòng hải quan, nhập danh mục).
