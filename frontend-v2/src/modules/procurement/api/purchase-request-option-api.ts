import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'

import type {
  AvailablePrSurveyLinesParams,
  AvailablePrSurveyLinesResult,
  PrAssignSupplierPayload,
  PrOptionManualPayload,
  PrOptionSupplierPayload,
  PrGenerateOrdersResult,
  PrOptionUpdatePayload,
  PurchaseRequestOption,
} from '../types/purchase-request-options'

const BASE_URL = '/api/purchase-requests'

/**
 * Tầng API PHƯƠNG ÁN trên dòng YCMH (bao-CR-310).
 *
 * Mọi đường GHI đều đi qua `_open_line` phía backend: phiếu phải trong giai đoạn
 * mở (dispatched → purchased) và dòng phải là dòng MÌNH phụ trách (trừ người
 * thấy-hết: người yêu cầu / người giữ quyền duyệt / phạm vi rộng). Riêng XEM
 * (`listOptions`) không bị chặn theo giai đoạn — phiếu đóng vẫn xem lại được.
 */
export const purchaseRequestOptionApi = {
  /** Danh sách phương án của MỘT dòng. Thiếu `supplier:read` thì NCC bị che sẵn. */
  listOptions: (id: number, itemId: number) =>
    apiGet<{ items: PurchaseRequestOption[] }>(`${BASE_URL}/${id}/items/${itemId}/options`),

  /**
   * Kho khảo sát ĐÃ DUYỆT chọn được cho một dòng — phân trang phía server.
   * Backend đòi ít nhất một tiêu chí (NCC / phân loại / từ khóa), thiếu thì trả
   * rỗng; và đòi `supplier:read` (403) vì bảng này lộ danh tính NCC.
   */
  listAvailableSurveyLines: (id: number, itemId: number, params: AvailablePrSurveyLinesParams) =>
    apiGet<AvailablePrSurveyLinesResult>(
      `${BASE_URL}/${id}/items/${itemId}/available-survey-lines`,
      { params: { ...params } },
    ),

  /** Gắn một dòng khảo sát đã duyệt làm phương án (tối đa 5 phương án / dòng). */
  addFromSurvey: (id: number, itemId: number, productSurveyLineId: number) =>
    apiPost<PurchaseRequestOption>(`${BASE_URL}/${id}/items/${itemId}/options`, {
      product_survey_line_id: productSurveyLineId,
    }),

  /** Thêm phương án NHẬP TAY — backend đòi có NCC (mã hoặc tên) + `supplier:read`. */
  addManual: (id: number, itemId: number, payload: PrOptionManualPayload) =>
    apiPost<PurchaseRequestOption>(`${BASE_URL}/${id}/items/${itemId}/options/manual`, payload),

  /** Sửa ghi chú / các ô chụp của một phương án (KHÔNG đổi được NCC). */
  update: (id: number, itemId: number, optionId: number, payload: PrOptionUpdatePayload) =>
    apiPatch<PurchaseRequestOption>(
      `${BASE_URL}/${id}/items/${itemId}/options/${optionId}`,
      payload,
    ),

  remove: (id: number, itemId: number, optionId: number) =>
    apiDelete<null>(`${BASE_URL}/${id}/items/${itemId}/options/${optionId}`),

  /**
   * Khe H.10.4 — thu mua điền/sửa NCC (kèm giá nếu cần) trên phương án 0 / nhập
   * tay, dùng được cả SAU khi dòng đã chốt. Backend đòi write + `supplier:read`,
   * từ chối phương án lấy từ khảo sát.
   */
  setSupplier: (id: number, itemId: number, optionId: number, payload: PrOptionSupplierPayload) =>
    apiPatch<PurchaseRequestOption>(
      `${BASE_URL}/${id}/items/${itemId}/options/${optionId}/supplier`,
      payload,
    ),

  /**
   * H.10.5 — "Áp 1 NCC cho nhiều dòng" trên màn chọn: áp NCC vào phương án ĐANG
   * CHỌN của từng dòng. Cả gói ăn theo nhau — một dòng hỏng là backend hủy hết.
   */
  assignSupplierBulk: (id: number, payload: PrAssignSupplierPayload) =>
    apiPost<{ updated: number }>(`${BASE_URL}/${id}/options/assign-supplier`, payload),

  /**
   * Chốt / bỏ chốt một phương án (bấm lại phương án đang chốt là bỏ chốt).
   * Chỉ người yêu cầu hoặc người giữ `purchase_request:approve` — backend gác.
   */
  choose: (id: number, itemId: number, optionId: number) =>
    apiPost<PurchaseRequestOption>(
      `${BASE_URL}/${id}/items/${itemId}/options/${optionId}/choose`,
      {},
    ),

  /**
   * Đợt 3b — NSTM "Chốt hoàn thành xử lý" PHẦN CỦA MÌNH trên phiếu (khuôn YCBG
   * `complete_sr`): mọi dòng mình phụ trách phải có phương án hoặc nằm trong
   * `emptyItemIds` (tick chốt rỗng), thiếu thì backend trả 400 kèm số dòng còn lại.
   */
  complete: (id: number, emptyItemIds: number[]) =>
    apiPost<{ done: number; empty: number; all_done: boolean }>(
      `${BASE_URL}/${id}/options/complete`,
      { empty_item_ids: emptyItemIds },
    ),

  /**
   * H.10.6 — "Tạo đơn mua hàng theo phương án": gom dòng đã chọn phương án theo
   * NCC thành N đơn NHÁP một lượt; dòng chưa có NCC vào một đơn riêng. Backend
   * gác `purchase_order:create` + phạm vi đọc phiếu; bấm lại không sinh trùng
   * (dòng đã nằm trên đơn bị bỏ qua, hết dòng thì trả 400).
   */
  generateOrders: (id: number) =>
    apiPost<PrGenerateOrdersResult>(`${BASE_URL}/${id}/options/generate-orders`, {}),

  /** Người yêu cầu / quản lý MỞ LẠI một dòng đã chốt hoàn thành cho NSTM sửa tiếp. */
  reopenLine: (id: number, itemId: number) =>
    apiPost<{ item_id: number; options_done: boolean; no_option: boolean }>(
      `${BASE_URL}/${id}/items/${itemId}/options/reopen`,
      {},
    ),
}
