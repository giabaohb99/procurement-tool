/**
 * Mã sự kiện / biểu mẫu / ứng dụng của bộ thu hành vi trên app cũ thumua (bao-CR-649, chép từ ERP v2 duoc-CR-641).
 *
 * Nguồn số là `backend/app/core/usage_codes.py` (UiEventType, UiForm, UiApp). App cũ không có tệp `statuses.ts`
 * sinh tự động như v2, nên số ở đây chép tay MỘT LẦN và được bài kiểm backend
 * `test/backend/test_thu_su_kien_thumua_cr649.py` đọc tệp này đối chiếu với Python — lệch một số là đỏ.
 * Thêm mã: sửa Python trước rồi chép sang đây, không tự đặt số.
 */
export const UI_EVENT = {
  PAGE_VIEW: 1,
  PAGE_LEAVE: 2,
  FORM_OPEN: 3,
  FORM_SUBMIT: 4,
  FORM_ABANDON: 5,
  SEARCH: 6,
  CLIENT_ERROR: 7,
} as const

export const UI_FORM_CODE = {
  PURCHASE_REQUEST: 1,
  QUOTE_REQUEST: 2,
  PURCHASE_ORDER: 3,
} as const

/** Ứng dụng gửi lô — thumua là 2 (ERP v2 không khai = 1). */
export const UI_APP_THUMUA = 2

/** 0 = sự kiện KHÔNG thuộc biểu mẫu nào (backend chấp nhận riêng số 0). */
export const UI_FORM_NONE = 0

export type UiEventCode = (typeof UI_EVENT)[keyof typeof UI_EVENT]
export type UiFormCode = (typeof UI_FORM_CODE)[keyof typeof UI_FORM_CODE]
