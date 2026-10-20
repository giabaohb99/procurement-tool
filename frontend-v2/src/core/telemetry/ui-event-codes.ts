/**
 * Mã sự kiện / mã biểu mẫu của bộ thu hành vi (duoc-CR-641). KHÔNG chép tay số (luật R2): hai hằng nguồn
 * `UI_EVENT_TYPE_CODE` / `UI_FORM_CODE` do `backend/scripts/gen_status_ts.py` sinh từ `backend/app/core/usage_codes.py`
 * (sửa mã ở Python rồi sinh lại). Tệp này chỉ đặt tên ngắn và kiểu cho phía thu thập.
 */
import { UI_ACTION_CODE, UI_EVENT_TYPE_CODE, UI_FORM_CODE } from '@/shared/constants/statuses'

export { UI_ACTION_CODE, UI_FORM_CODE }
export const UI_EVENT = UI_EVENT_TYPE_CODE

/** 0 = sự kiện KHÔNG thuộc biểu mẫu nào (không nằm trong bộ mã `ui_form` của backend, backend cũng chấp nhận riêng số 0). */
export const UI_FORM_NONE = 0

export type UiEventCode = (typeof UI_EVENT_TYPE_CODE)[keyof typeof UI_EVENT_TYPE_CODE]
export type UiFormCode = (typeof UI_FORM_CODE)[keyof typeof UI_FORM_CODE]
export type UiActionCode = (typeof UI_ACTION_CODE)[keyof typeof UI_ACTION_CODE]
