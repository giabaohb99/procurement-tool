# Loại hợp đồng (CỐ ĐỊNH trong code). value = MÃ lưu DB, label = nhãn hiển thị.
#
# Trước CR-118 cột `tab_contract.contract_type` là VARCHAR(50) chữ tự do tiếng Việt, mỗi nơi
# khai một bộ khác nhau (`frontend/src/config/cruds.tsx` 3 giá trị · `ContractDetail.tsx` 5 ·
# `frontend-v2` 5) trong khi dữ liệu thật lại lưu bộ thứ tư — kể cả bản gõ SAI
# "Hơp đồng nguyên tắc" (thiếu dấu nặng ở "Hợp"). Hệ quả: bộ lọc chỉ với tới vài giá trị,
# và ô chọn mở ra là trống trơn dù bản ghi có dữ liệu.
#
# Nay DB lưu MÃ tiếng Anh, tiếng Việt chỉ còn ở tầng hiển thị. Đổi nhãn = sửa đúng một chỗ,
# không phải chạy migration đổi dữ liệu như lần này.
#
# B-01 (QĐ-9): bộ này chuyển sang khai bằng khung chung `status_catalog`. Đây là bài thử của
# khung — ba tên cũ bên dưới giữ NGUYÊN kiểu và NGUYÊN thứ tự, nên endpoint
# `/contracts/meta/types` trả về y hệt trước.
from app.core.status_catalog import Code, CodeSet, register

CONTRACT_TYPE_SET = register(CodeSet("contract_type", "Loại hợp đồng", [
    Code("purchase",  "Hợp đồng mua bán"),
    Code("principle", "Hợp đồng nguyên tắc"),
    Code("economic",  "Hợp đồng kinh tế"),
    Code("template",  "Hợp đồng khuôn mẫu"),
    Code("transport", "Hợp đồng vận chuyển"),
    Code("service",   "Hợp đồng dịch vụ"),
    Code("other",     "Khác"),
]))

# Ba tên cũ — nơi gọi hiện tại vẫn dùng, đừng bỏ.
CONTRACT_TYPES = CONTRACT_TYPE_SET.options
CONTRACT_TYPE_VALUES = CONTRACT_TYPE_SET.values
CONTRACT_TYPE_LABEL = CONTRACT_TYPE_SET.labels
