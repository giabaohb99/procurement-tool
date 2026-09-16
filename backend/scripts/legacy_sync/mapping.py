"""Bảng tra khóa app đặt xe cũ (Firebase) sang ID bên ERP.

QĐ-K: khớp bản ghi theo KHÓA FIREBASE, không theo tên và không theo mã số thuế.
Hai bằng chứng cho luật này, đo trên bản kết xuất ngày 16/09/2026:

- Tên bên app cũ đã trôi thật: phòng `dept_kinh_doanh` giờ mang tên "Pháp Lý".
- `tab_company` bên ERP có HAI hàng cùng mã số thuế 1801722464 (id 1 "DEGO" và
  id 16 "DEGO HOLDING"). Không bản ghi nào trỏ vào id 16, nên bảng dưới chọn id 1.

Bảng này do người soát rồi mới ghi vào đây. Script không được tự đoán thêm cặp
nào ngoài bảng — thấy khóa lạ thì báo và dừng, đừng khớp mò theo tên.
"""

#  Khóa `brands` bên app cũ -> id `tab_company`. Số phiếu đo ngày 16/09/2026 ghi
#  kèm để lần sau đối chiếu lại bản kết xuất mới có lệch không.
BRAND_TO_COMPANY_ID = {
    "aFIQKCJMuLaG5geoO9qAy": 1,   # DEGO HOLDING - 1801722464   · 465 phiếu
    "dFp8B9bCoB-p7cV1hZtxZ": 2,   # IDA GLOBAL                  · 413 phiếu
    "bNWp5G8VCYA96_0L4HrGF": 3,   # SX HÓA CHẤT ABA             · 204 phiếu
    "0ih2D3OB1r3QuxHIz4Wtc": 5,   # ICARE                       · 145 phiếu
    "oTrZVEVO-y0udrtUvvE6E": 8,   # BAMBOO                      ·  94 phiếu
    "VCdzxAf97CslKsN3xyHUL": 9,   # N2SBIO                      ·  71 phiếu
    "Uq93UP_ftNNIKIJyCRqId": 11,  # HÓA CHẤT NN ABA             ·  67 phiếu
    "W3d0nCYf0tvE07gDZriAZ": 14,  # AGRICARE                    ·  56 phiếu
    "8OuHN2oYKo8RjvYvAjIM0": 10,  # HÓA CHẤT NN DEGO            ·  34 phiếu
    "7cbpgbE2ixRnfjMuy_fld": 6,   # NPP DR.XANH                 ·  28 phiếu
    "lHkjAyl9Qf3e3qWXUuXGG": 7,   # HKD DR.XANH                 ·  14 phiếu
}

#  Khóa `departments` bên app cũ -> id `tab_department` ĐÃ CÓ SẴN bên ERP.
#  Mười cặp đầu trùng tên nhau tuyệt đối sau khi bỏ dấu và chuẩn hóa hoa thường;
#  bốn cặp cuối do đại ca chốt tay (xem `DEPARTMENT_MERGED_INTO_ERP`).
DEPARTMENT_TO_ERP_ID = {
    "-GmRqStpzB_mMIyXCuzbl": 7,   # N2SBIO
    "B956VINcgQIUC-lHPwZkU": 14,  # Dr.Xanh
    "BZRVRaBc9LhaUf-k7pOpB": 17,  # Lập Trình & IT Nội Bộ
    "GF7IkeBlMQE2mc8rlCC0t": 19,  # Hành Chính
    "GGox3WkurI7OiwWJd7WeN": 11,  # iCare
    "GrOznia62mMTQTBxerkU3": 8,   # Điều Phối
    "URhjgJvbpYOIaSlbX1J67": 10,  # Thiết Kế
    "lw8ywTnkkXyU_uO14TF9v": 9,   # ABA Chemical
    "qQH8iMN2OfiyFN-LNrpBz": 12,  # IDA Global
    "z6ps_mZ_7e7D4oJuq81FY": 16,  # Nhân Sự
    #  --- BỐN cặp GỘP TAY, đại ca chốt 16/09: "gần trùng thì dùng của ERP" ---
    "dept_ky_thuat": 20,          # "Sản Xuất"            -> "Sản xuất -Thu mua"
    "dept_ke_toan": 15,           # "Kế Toán Thuế"        -> "Kế toán"
    "AB_7o-LLqPMVQqAscudjp": 13,  # "Bamboovietnam"       -> "Bamboo"
    "0VVUBFa_kKJgrn3ou6mIE": 5,   # "Nhà Máy Dego Organic" -> "Dego Organic"
}

#  Bốn phòng GẦN TRÙNG: tên hai bên lệch nhau nên phép so tên tự động không bắt
#  được, đại ca soi rồi chốt tay là GỘP VỀ PHÒNG BAN ERP (16/09/2026). Giữ bảng
#  này lại vì ba lý do: nó là hồ sơ của một quyết định do người ra chứ không
#  phải luật máy suy được; nó cho script biết dòng nào là bản trùng cần dọn nếu
#  đã lỡ tạo ở lượt chạy trước; và số phiếu kèm theo cho biết quyết định này
#  nặng cỡ nào — tổng 378/1313 phiếu, 29%.
#  Dạng: khóa app cũ -> (id ERP gộp vào, tên bên app cũ, tên bên ERP, số phiếu).
DEPARTMENT_MERGED_INTO_ERP = {
    "dept_ky_thuat": (20, "Sản Xuất", "Sản xuất -Thu mua", 226),
    "dept_ke_toan": (15, "Kế Toán Thuế", "Kế toán", 134),
    "AB_7o-LLqPMVQqAscudjp": (13, "Bamboovietnam", "Bamboo", 12),
    "0VVUBFa_kKJgrn3ou6mIE": (5, "Nhà Máy Dego Organic", "Dego Organic", 6),
}

#  --------------------------------------------------------------------------
#  XE và TÀI XẾ
#  --------------------------------------------------------------------------
#  `tab_vehicle` và `tab_driver` bên ERP được dựng theo đúng danh sách app cũ nên
#  cả 13 xe lẫn 13 tài xế đều ra 1-1 (đo 16/09/2026). Bảng dưới do soát tay rồi
#  chốt, không để script tự dò lúc chạy — hai chỗ dò sẽ sai:
#
#  - Ba xe thuê ngoài mang biển số rác bên app cũ ("xe thuê", "xe thê",
#    "XE THUÊ NGOÀI"); ERP lại lưu chính TÊN loại xe vào ô biển số
#    ("Xe 4 chỗ thuê"...). Khớp biển số thì ba xe này rơi hết.
#  - Hai tài xế app cũ dùng CHUNG số 0971445134 ("Tài xế thuê ngoài" và
#    "Tự lái"); ERP cũng có đúng hai hồ sơ đó với cùng số ấy. Khớp theo số điện
#    thoại là hòa, phải người nhìn tên mới tách được.
VEHICLE_TO_ERP_ID = {
    "3aB4g6h59k7jVrg6Kz1gR": 1,    # 51L-423.31  BMW
    "i9LOn1CWdJPeEYR5iZOZv": 2,    # 51M-15735   Vinfast Limo Green
    "veh_04": 3,                   # 65C-172.76  Toyota Hilux
    "veh_05": 4,                   # 51D-465.49  MAZDA BT50
    "veh_06": 5,                   # 51D-668.25  Mazda BT50
    "veh_07": 6,                   # 51D-629.48  MAZDA BT50
    "veh_08": 7,                   # 51D-982.44  Toyota Hilux
    "veh_09": 8,                   # 65A-096.81  Toyota Vios
    "veh_10": 9,                   # 51D-895.00  ISUZU
    "veh_11": 10,                  # 51D-853.97  HYUNDAI
    "4OjI7ApKmYWHZtTfUIgbg": 11,   # thue ngoai: Xe 4 cho thue
    "BLVWBQSrihlI5y_3LR9jJ": 12,   # thue ngoai: Xe tai thue
    "P-i76cI8rKRZrw0QhSzog": 13,   # thue ngoai: Xe 7 cho thue
}

DRIVER_TO_ERP_ID = {
    "2IElXDzKNSTdZGHS3nwt9Fc88ey2": 1,    # Tran Minh Sang
    "Br4YIj5p5hhfWZp27wdXNMImfNI3": 2,    # Le Minh Thong
    "Ckafxq5l1hfiApdV3dg80SPaG7m1": 3,    # Luu Nhut Minh
    "EyzP5mTjU6TZNbNqoSsKoKx1kmz1": 4,    # Vo Huynh Nhat Khoa
    "GC3ivYJVe2kzpH0XGTOZd": 5,           # Tai xe thue ngoai
    "XjNr249FGKRQBVNZb14dyt1t6DC2": 6,    # Tran Quoc Thai
    "ZWbcQhHdqfVZjC4rXJAelUwZLH62": 7,    # Le Tan Nhut
    "gPGshxKxlEeg0UbEC8K7wt1r0yn1": 8,    # Tran Quang Huy
    "jF2MvijUc7TNM1SAv28DXpzu3Tn2": 9,    # Le Vy Khang
    "nyIiuwamemc4bSd2TeYyVBv7DBc2": 10,   # Dao Quoc Trieu
    "qFwvBX0xb1bgn6QuQKnpxRYAeaW2": 11,   # Huynh Quang Tin
    "s5aCVhE7CegSErAL1alNDdm4Tyl2": 12,   # Le Lam Tung
    "vRKAfizJgj_fdJFkSLWrL": 13,          # Tu lai
}

#  --------------------------------------------------------------------------
#  NGƯỜI DÙNG app cũ -> `tab_employee`
#  --------------------------------------------------------------------------
#  Khớp tự động đi bằng EMAIL, và chỉ nhận ca 1-1 tuyệt đối. Ba tình huống dưới
#  đây phá thế 1-1 nên script KHÔNG tự đoán, phải người chốt rồi ghi vào đây:
#
#  1. Một email app cũ trỏ tới HAI hồ sơ nhân sự ERP (đo 16/09: id 38 và 201 đều
#     là "Nguyễn Thị Kiều Trang", cùng `ntktrang.idagroup@gmail.com`, cùng
#     `official`, khác phòng ban 5 với 15 — hồ sơ trùng thật bên ERP).
#  2. Một email app cũ đứng tên HAI tài khoản Firebase (`pltgiang@live.com`).
#     `legacy_id` là một cột nên một hồ sơ chỉ nhận được một khóa; khóa còn lại
#     phải khai ở `USER_SKIPPED` kèm lý do.
#  3. Email hai bên khác nhau nhưng tên trùng. KHÔNG khớp theo tên — cùng lý do
#     đã cấm ở QĐ-K, và bản đo cho thấy tên trùng không chắc là một người
#     (`assistant.n2sbiovn@gmail.com` mang tên một nhân viên nhưng là hộp thư
#     dùng chung).
#
#  Dạng: UID Firebase -> id `tab_employee`. Người chốt, script chỉ thi hành.
USER_MANUAL_MAP: dict[str, int] = {
    #  Đại ca chốt 16/09: "1 id bị trùng thì lấy id nhỏ nhất". Hồ sơ 38 và 201 là
    #  cùng một người (trùng tên, trùng email, cùng `official`, chỉ khác phòng
    #  ban 5 với 15). Đã rà: id 201 KHÔNG dính chứng từ nào — không đơn hàng,
    #  không yêu cầu, chỉ có tài khoản 210 và một dòng `tab_employee_department`.
    #  Nên chọn 38 là chọn xong, không có gì phải cập nhật lại.
    "xp90m5L0upSWzpkpO9uApZf0Puv2": 38,   # Nguyễn Thị Kiều Trang · 24 phiếu

    #  ---- 14 ca "tên trùng mà email khác", đại ca chốt 16/09: "dùng của ERP" --
    #  Gợi ý do `_norm_name` dựng ra, đại ca duyệt cả cụm. Email app cũ khác email
    #  ERP nên phép khớp tự động không nhận; từ đây trở đi hồ sơ ERP là bản chính,
    #  email app cũ KHÔNG chép đè sang (QĐ-K: ERP đúng).
    "3FhPQvW2UvRXtFcTQncrCohKYBw2": 235,  # Trần Phước Hoàng Khang · 21 phiếu
    "P2RIuJ39GBdAbvkFrzevY6nYI993": 211,  # Trần Ngọc Thảo Ly      · 21 phiếu
    "ST9uCXKzZdRjadBW0O4k4JzkgzT2": 236,  # Lê Thị Trúc Thơ        · 16 phiếu
    #  ⚠️ Ca DUY NHẤT trong 14 ca mà em đã cảnh báo ngược lại: email app cũ
    #  `assistant.n2sbiovn@gmail.com` là HỘP THƯ DÙNG CHUNG đang mang tên một
    #  nhân viên thật. Đại ca vẫn chốt dùng hồ sơ ERP, nên 12 phiếu đó về id 75.
    #  Ghi lại đây để nếu sau này thấy phiếu "lạ" đứng tên chị Trang thì biết
    #  ngay chỗ phải lật lại, đừng đi tìm lỗi ở chỗ khác.
    "P1ntSMDKFYdIYmvSjVgF0MvVQNF2": 75,   # Nguyễn Thị Thuỳ Trang  · 12 phiếu
    "Qdp0FdyDlCZB9XQBTDMi3ld2wUq2": 246,  # Lâm Bích Dư            · 12 phiếu
    "bZGIbgpTV1aQo2Oui8IfkiiXCGd2": 187,  # Thái Thị Yến Nhi       ·  6 phiếu
    "xW6OTueBY4VMHnZCcIkvR5TdbCm2": 243,  # Nguyễn Ngọc Bảo Thi    ·  6 phiếu
    "q2lSXedBK8PjN377nnZd9NLm4HG3": 205,  # Nguyễn Thị Ngọc Thảo   ·  5 phiếu
    "tjkX4WBq4xWIENYGPisiCjQBOtS2": 168,  # Nguyễn Thị Anh Thư     ·  2 phiếu
    "Mz30uR98TLgQtNNwXANk3u6g5fy2": 174,  # Mai Thi Hiểu           ·  1 phiếu
    "PC7UsdkRHwaNwkyH2PUgeBIZrvk1": 199,  # Danh Nhật Hào          ·  1 phiếu
    #  BA UID cùng trỏ về hồ sơ 221 "Phạm Lê Triết Giang", mà `legacy_id` là MỘT
    #  cột. Chọn UID này làm khóa chính vì nó là UID duy nhất còn lại sau khi loại
    #  hai UID dùng chung `pltgiang@live.com` (xem `USER_SKIPPED`). Cả ba đều 0
    #  phiếu nên không mất dữ liệu; nhưng bộ nạp phiếu PHẢI tra người tạo qua
    #  `USER_MANUAL_MAP` rồi mới tới `legacy_id`, chứ tra mỗi `legacy_id` thì
    #  phiếu của hai UID kia rơi mất — hôm nay là 0, mai người ta đặt xe thì khác.
    "EL1KRQfUkqhIwYWJHpluRr733CB2": 221,  # Phạm Lê Triết Giang    ·  0 phiếu
}

#  UID app cũ CỐ Ý không gắn vào hồ sơ nào, kèm lý do. Khác với "chưa xét": đã
#  xét rồi và quyết định là bỏ. Dạng: UID -> lý do.
USER_SKIPPED: dict[str, str] = {
    #  Hai UID này dùng chung email `pltgiang@live.com` và cùng là hồ sơ 221 với
    #  UID đã chọn ở trên. Không phải bỏ người — bỏ KHÓA, vì một hồ sơ chỉ đeo
    #  được một `legacy_id`. Cả hai 0 phiếu.
    "5fchIn78bSSSnfbIC42K41V7SiY2":
        "Phạm Lê Triết Giang — UID thứ hai của hồ sơ 221, legacy_id chỉ giữ được một",
    "vdDAfwSs5HWF8TKYuszcxbyeqb22":
        "Phạm Lê Triết Giang — UID thứ ba của hồ sơ 221, legacy_id chỉ giữ được một",
}

#  Cột `department_id` nằm rải khắp hệ. Dùng để kiểm TRƯỚC khi xóa một phòng ban
#  trùng: còn dòng nào trỏ vào thì KHÔNG xóa, báo ra cho người xử.
DEPARTMENT_REFERENCE_COLUMNS = [
    ("tab_department", "parent"),
    ("tab_department_company", "department_id"),
    ("tab_document", "department_id"),
    ("tab_document_request", "department_id"),
    ("tab_document_scope", "department_id"),
    ("tab_employee", "department_id"),
    ("tab_employee_department", "department_id"),
    ("tab_forum_post", "dept_id"),
    ("tab_job_position", "department_id"),
    ("tab_leave_request", "department_id"),
    ("tab_purchase_order", "department_id"),
    ("tab_purchase_request", "department_id"),
    ("tab_room_booking", "department_id"),
    ("tab_seal_request", "department_id"),
    ("tab_survey_request", "department_id"),
    ("tab_vehicle_booking", "department_id"),
    ("tab_work_group_member", "department_id"),
    ("tab_work_list_member", "department_id"),
]
