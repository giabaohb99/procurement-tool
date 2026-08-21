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
CONTRACT_TYPES = [
    {"value": "purchase",  "label": "Hợp đồng mua bán"},
    {"value": "principle", "label": "Hợp đồng nguyên tắc"},
    {"value": "economic",  "label": "Hợp đồng kinh tế"},
    {"value": "template",  "label": "Hợp đồng khuôn mẫu"},
    {"value": "transport", "label": "Hợp đồng vận chuyển"},
    {"value": "service",   "label": "Hợp đồng dịch vụ"},
    {"value": "other",     "label": "Khác"},
]

CONTRACT_TYPE_VALUES = {t["value"] for t in CONTRACT_TYPES}
CONTRACT_TYPE_LABEL = {t["value"]: t["label"] for t in CONTRACT_TYPES}
