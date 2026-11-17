import type { PurchaseRequestDetail, SupplierCluster } from '../types/purchase-request-detail'
import type { PurchasingPrintData } from '../types/purchasing-print'
import type { PrintSignatureSource } from './purchase-request-signature-cells'

/**
 * duoc-CR-777 — phần của tờ phiếu mà "Mẫu thu mua" thay khỏi dữ liệu YCMH. Mọi thứ khác (pháp nhân,
 * số phiếu, ngày, mục đích, nơi giao...) giữ nguyên theo phiếu.
 */

/** Bốn dòng mục THÔNG TIN CHUNG. Chữ "............" giữ đúng như mẫu thường khi thiếu dữ liệu. */
export interface PrintSheetGeneralInfo {
  requester: string
  position: string
  department: string
  headOfDept: string
}

const PLACEHOLDER = '............'

/** Mẫu thường: lấy từ phiếu YCMH. */
export function buildRequestGeneralInfo(
  purchaseRequest: Pick<
    PurchaseRequestDetail,
    'requester' | 'requester_position' | 'department' | 'head_of_dept'
  >,
): PrintSheetGeneralInfo {
  return {
    requester: purchaseRequest.requester,
    position: purchaseRequest.requester_position || PLACEHOLDER,
    department: purchaseRequest.department || PLACEHOLDER,
    headOfDept: purchaseRequest.head_of_dept || PLACEHOLDER,
  }
}

/** Mẫu thu mua: người đề xuất = người đang in, trưởng phòng = quản lý trực tiếp của người đó. */
export function buildPurchasingGeneralInfo(
  data: Pick<PurchasingPrintData, 'proposer' | 'manager'>,
): PrintSheetGeneralInfo {
  return {
    requester: data.proposer.name,
    position: data.proposer.position || PLACEHOLDER,
    department: data.proposer.department || PLACEHOLDER,
    headOfDept: data.manager.name || PLACEHOLDER,
  }
}

/**
 * Mục "NHÀ CUNG CẤP DO BỘ PHẬN ĐỀ XUẤT" của mẫu thu mua = NCC của ĐƠN. Đường API chỉ trả mã + tên, nên
 * MST / liên hệ chỉ giữ khi NCC của đơn ĐÚNG là NCC ghi trên phiếu (`requestSupplier`, cụm mẫu thường
 * đang in) — khác NCC thì để trống, tránh in MST của NCC này dưới tên NCC kia (khớp bản v1). NCC bị
 * che (thiếu `supplier.read`) hoặc đơn chưa có NCC thì trả cụm rỗng: tờ phiếu in chữ mặc định y như
 * mẫu thường khi không ai nhập NCC.
 */
export function buildPurchasingSupplier(
  data: Pick<PurchasingPrintData, 'supplier' | 'supplier_hidden'>,
  requestSupplier: SupplierCluster,
): SupplierCluster {
  const name = data.supplier_hidden ? '' : (data.supplier?.name ?? '')
  if (!name) return { name: '', tax_code: '', contact: '' }
  if (name === requestSupplier.name) return requestSupplier
  return { name, tax_code: '', contact: '' }
}

/**
 * Nguồn chữ ký của mẫu thu mua: ô "Người lập" = người đang in, ô "TP/BP đề xuất" = quản lý trực tiếp
 * (tên + chữ ký). Hai ô còn lại (Giám đốc / Chủ hộ, TP/BP mua hàng) GIỮ NGUYÊN như mẫu thường. Thay
 * cả hai đường: bộ ô backend trả (`print_signature_cells`, theo khóa ô) lẫn các khóa rời mà đường
 * dự phòng của bản backend cũ đọc — để "không chữ ký" vẫn đi qua đúng `resolvePrintSignatureCells`.
 */
export function buildPurchasingSignatureSource(
  source: PrintSignatureSource,
  data: Pick<PurchasingPrintData, 'proposer' | 'manager'>,
): PrintSignatureSource {
  const preparer = { name: data.proposer.name || '', signature: data.proposer.signature || '' }
  const proposer = { name: data.manager.name || '', signature: data.manager.signature || '' }
  return {
    ...source,
    requester: preparer.name,
    requester_signature: preparer.signature,
    approver_name: proposer.name,
    approver_signature: proposer.signature,
    print_signature_cells: source.print_signature_cells?.map((cell) => {
      if (cell.key === 'preparer') return { ...cell, ...preparer }
      if (cell.key === 'proposer') return { ...cell, ...proposer }
      return cell
    }),
  }
}
