import type {
  PrintSignatureCell,
  PurchaseRequestDetail,
} from '../types/purchase-request-detail'

/** Phần dữ liệu phiếu mà cụm ký cần — hẹp hơn cả phiếu để bài kiểm dựng được dễ. */
export type PrintSignatureSource = Pick<
  PurchaseRequestDetail,
  | 'print_signature_cells'
  | 'requester'
  | 'requester_signature'
  | 'approver_name'
  | 'approver_signature'
  | 'purchasing_head_name'
  | 'purchasing_head_signature'
>

/**
 * Bốn ô cũ dựng từ các khóa rời — chỉ dùng khi backend chưa gửi `print_signature_cells`
 * (backend cũ). Giữ đúng hành vi trước bao-CR-531: «Giám đốc» luôn trống để ký tay.
 */
function buildLegacyCells(source: PrintSignatureSource): PrintSignatureCell[] {
  return [
    { key: 'director', role: 'Giám đốc', name: '', signature: '' },
    {
      key: 'purchasing_head',
      role: 'TP/BP mua hàng',
      name: source.purchasing_head_name ?? '',
      signature: source.purchasing_head_signature ?? '',
    },
    {
      key: 'proposer',
      role: 'TP/BP đề xuất',
      name: source.approver_name ?? '',
      signature: source.approver_signature ?? '',
    },
    {
      key: 'preparer',
      role: 'Người lập',
      name: source.requester ?? '',
      signature: source.requester_signature ?? '',
    },
  ]
}

/**
 * Bộ ô ký cụm «XÉT DUYỆT» sẽ vẽ — bao-CR-531, luật bộ ô đổi ở bao-CR-536.
 *
 * BỘ Ô (mấy ô, nhãn gì, ai ở ô nào) do backend quyết (`print_signature_cells.py`): công ty luôn
 * 4 ô; hộ kinh doanh cũng 4 ô, chỉ đổi nhãn ô đầu thành «Chủ hộ» (bao-CR-539); ô trùng người đại
 * diện để trống.
 * Ở đây chỉ áp hai chế độ phía máy khách:
 *  · «Không chữ ký» → bỏ CẢ ảnh LẪN tên — đây là nút người dùng tự bấm khi muốn ẩn tên;
 *  · «Mẫu thuế» → để trống hết, nhưng vẫn theo đúng bộ ô backend trả.
 */
export function resolvePrintSignatureCells(
  source: PrintSignatureSource,
  { taxMode, showSignature }: { taxMode: boolean; showSignature: boolean },
): PrintSignatureCell[] {
  const cells = source.print_signature_cells?.length
    ? source.print_signature_cells
    : buildLegacyCells(source)
  const blank = taxMode || !showSignature
  return cells.map((cell) => ({
    key: cell.key,
    role: cell.role,
    name: blank ? '' : cell.name || '',
    signature: blank ? '' : cell.signature || '',
  }))
}
