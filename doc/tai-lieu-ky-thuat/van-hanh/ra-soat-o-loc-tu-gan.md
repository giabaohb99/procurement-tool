# Rà soát lỗi ô lọc tự dính giá trị (23/10/2026)

**Bối cảnh:** sáng 23/10 tài khoản NSU012 (nhân viên thu mua) mở *Tiến độ mua hàng* thì ô **Bộ phận** tự chọn sẵn *Kinh doanh AGC*, bảng rỗng. Lỗi cùng họ đã gặp ở bao-CR-388 (12/09, ô *NSTM phụ trách* tự gán chính người đăng nhập). Đã vá gấp ở bao-CR-657. Tài liệu này liệt kê **mọi chỗ còn có thể dính**, giải thích logic giao diện và backend, để quyết cách sửa tận gốc.

## 1. Vì sao lỗi cứ lặp lại

Lỗi xảy ra khi **hai điều kiện gặp nhau**:

1. **Giao diện tự gán khi chỉ còn một lựa chọn.** Ô chọn `SearchSelect` của giao diện thumua (`frontend/src/components/SearchSelect.tsx`, dòng 47) có luật *danh sách chỉ còn 1 lựa chọn và ô đang trống thì tự chọn luôn*, mặc định **BẬT** (`autoSelectSingle = true`). Luật này viết cho biểu mẫu, nhưng mọi ô lọc mới đều dùng lại component này; ai quên tắt là dính.
2. **Backend trả danh mục đã bị lọc theo quyền.** Ô chọn công ty, phòng ban, nhân sự gọi chính API danh sách (`/api/companies`, `/api/departments`, `/api/employees`), mà API này lọc theo phạm vi quyền của người xem (`apply_scope`). Người bị thu hẹp chỉ nhận về rất ít lựa chọn, có khi đúng 1 cái.

Hai điều kiện gặp nhau thì ô lọc tự dính vào lựa chọn duy nhất, bảng lọc theo giá trị đó và ra rỗng. Bấm X xóa xong, luật tự gán lại gán ngay.

**Đúng như đại ca nói: ô lọc không được tự gán.** Lọc dữ liệu theo quyền là việc của backend: API danh sách phiếu đã tự lọc theo phạm vi rồi, ô lọc chỉ để người dùng thu hẹp thêm.

## 2. Logic backend hiện tại

- `backend/app/core/scoping.py`, `apply_scope(query, Model, entity, user, profile)`: lấy **HỢP** các quyền mà người dùng có trên entity đó. Mỗi cặp người–vai trò có phạm vi (`own · assigned · proc · dept_proc · dept · company · all`) cộng các dòng chọn đích danh trong `tab_user_scope`. Dòng *gồm công ty* làm **HẸP** lại; dòng *gồm phòng ban* làm **RỘNG** thêm; dòng *loại trừ* làm bớt đi.
- Cột dùng để lọc của từng entity khai trong `SCOPE_FIELDS`. Với các danh mục mà ô chọn hay dùng:

| Danh mục | Lọc theo | Hệ quả |
|---|---|---|
| `company` | `id` công ty | Người thu hẹp theo công ty chỉ thấy công ty của mình |
| `department` | `company_id`, tức **công ty chính** của phòng | Phòng dùng chung khai công ty = 0 (26/27 phòng trên prod), nên người bị thu hẹp theo công ty **không thấy phòng nào**. Bảng `tab_department_company` (phòng phục vụ nhiều công ty) **không được xét**. Dòng *loại trừ phòng ban* cũng không áp được cho danh mục này. |
| `employee` | công ty, phòng, chính mình | Người phạm vi `own` chỉ thấy chính mình, nên ô *NSTM / người yêu cầu* chỉ còn 1 lựa chọn |
| `supplier`, `product`, `warehouse`, `unit`, `item_group` | `PUBLIC` (không lọc) | Không dính |

## 3. Đo trên prod (23/10, chỉ đọc)

Tổng: 13 công ty, 27 phòng ban, 268 nhân sự. Có **7 tài khoản** đang hoạt động thấy từ 0 đến 1 lựa chọn ở ít nhất một danh mục:

| Tài khoản | Công ty / phòng / nhân sự thấy được | Ghi chú |
|---|---|---|
| NSU012 (Trần Diễm Phương, nhân viên thu mua) | 13 / **1** / 3 | Phạm vi khai bằng 14 dòng *gồm công ty* (gần như mọi công ty) cộng 1 dòng loại trừ phòng 32. Vì phòng dùng chung có công ty = 0 nên chỉ còn phòng AGC. Gây lỗi sáng 23/10. |
| NSU266, NSU267, NSU268, NSU269, NSU270 (AGC) | 1 / 1 / 5 | Thu hẹp chỉ công ty AGC theo thiết kế; tự gán AGC là đúng nghĩa, nhưng ô lọc vẫn không nên khóa cứng |
| HDSD0001 | 0 / 0 / 0 | Tài khoản làm bài HDSD |

## 4. Danh sách chỗ có thể dính

### 4.1. Ô LỌC giao diện thumua (`frontend/`)

**Đã vá ở bao-CR-657 (prod 23/10):** 19 ô có placeholder *Tất cả* ở `PurchaseProgress.tsx`, `SurveyProgress.tsx`, `Inventory.tsx`, `Payables.tsx`, `Reports.tsx` (2), `PrLinesReportPage.tsx`, `supplier-payables-filters.tsx` (aging), `warehouse-purchase-lines.tsx`. Đã vá từ trước (bao-CR-388): `FilterBar.tsx`, `conditional-filter/ui/value-input.tsx`, `customs/CustomsConfigTab.tsx`.

**CÒN SÓT, vẫn tự gán** (placeholder không đúng chữ *Tất cả* nên lượt vá gấp chưa bắt được):

| Chỗ | Ô | Nguồn lựa chọn | Mức |
|---|---|---|---|
| `components/PrLinesReport.tsx:60` | NSTM | nhân sự, **lọc theo quyền** | **Cao**: người phạm vi `own` bị dính chính mình (đúng ca bao-CR-388) |
| `components/MatrixPivotTab.tsx:135` | Đối tượng của bảng ma trận | dữ liệu báo cáo | Trung bình |
| `pages/Reports.tsx:421` | Đơn vị vận chuyển | dữ liệu | Trung bình |
| `components/PrLinesReport.tsx:50, 55` | Tiến độ, Trạng thái | danh sách cố định | Thấp (luôn > 1 lựa chọn) |
| `components/supplier-payables-filters.tsx:38` | Khoản nợ | danh sách cố định | Thấp |
| `pages/Reports.tsx:314, 426` | Kỳ, Tháng | danh sách cố định | Thấp |

### 4.2. BIỂU MẪU thumua tự điền từ danh mục bị lọc theo quyền

Biểu mẫu tự điền khi chỉ có một lựa chọn là cố ý. Nhưng nếu danh mục bị lọc sai thì nó điền **sai mà không báo**:

| Chỗ | Ô | Rủi ro |
|---|---|---|
| `pages/SurveyRequestDetail.tsx:832` | Bộ phận (YCBG) | **Cao**: NSU012 tạo YCBG sẽ bị tự điền *Kinh doanh AGC* |
| `pages/PurchaseRequestDetail.tsx:1069, 1075, 1161` | Công ty, Người yêu cầu, Người duyệt | Trung bình |
| `pages/PurchaseOrderDetail.tsx:1225, 1289, 1304` | Công ty, NSPT, Người duyệt | Trung bình |
| `pages/SurveyRequestDetail.tsx:908, 1047, 1449` | Người duyệt, Gán NSTM | Trung bình |
| `pages/PaymentRequestDetail.tsx:251`, `ContractDetail.tsx:93`, `Inventory.tsx:247` | Công ty | Thấp |

Các ô còn lại (nhà cung cấp, sản phẩm, kho, ĐVT, phân loại, danh sách cố định) lấy từ danh mục PUBLIC, không dính.

### 4.3. Giao diện ERP v2 (`frontend-v2/`)

- **Không có** luật tự gán khi còn một lựa chọn ở ô lọc (bộ `conditional-filter` không có luật này).
- Chỗ lấy mặc định từ người đăng nhập chỉ nằm ở **biểu mẫu tạo mới** (văn bản mới mặc định phòng của mình, YCMH và YCBG mới mặc định công ty của mình). Đúng ý, không phải ô lọc.
- Cần nhớ: từ kh-NT2-2, bốn màn Thu mua v2 **nhớ bộ lọc** trong phiên làm việc. Bảng rỗng do lọc thì đã có câu báo, nhưng người dùng vẫn có thể thấy bộ lọc *tự có sẵn* khi quay lại màn.
- Danh mục phòng ban, nhân sự ở v2 gọi cùng API nên vẫn bị thiếu lựa chọn (mục 2). Không tự dính, nhưng ô chọn phòng sẽ rỗng hoặc thiếu.

## 5. Đề xuất sửa tận gốc

1. **Giao diện thumua:**
   - Đổi mặc định `autoSelectSingle` sang **TẮT**; biểu mẫu nào thật sự cần tự điền thì khai `autoSelectSingle` rõ ràng.
   - Thêm bài kiểm quét mã: một ô lọc nào bật tự gán là bài đỏ.
   - Vá 8 ô còn sót ở mục 4.1.
2. **Backend:**
   - Danh mục dùng cho ô chọn (công ty, phòng ban, nhân sự dạng mã + tên) **không lọc theo phạm vi dữ liệu**; dữ liệu phiếu vẫn lọc như cũ.
   - Hoặc tối thiểu: phòng ban xét cả `tab_department_company` và coi phòng công ty = 0 là phòng dùng chung.
   - Thay đổi này thuộc khu phân quyền, cần anh Dược duyệt.
3. **Dữ liệu NSU012:** 14 dòng *gồm công ty* tương đương *mọi công ty* nhưng làm rơi phòng dùng chung. Gỡ 14 dòng đó (giữ dòng loại trừ phòng 32) thì chị thấy đủ 27 phòng. Đây là đổi quyền người dùng thật, cần đại ca gật.
