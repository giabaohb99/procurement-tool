import { ArrowLeft, Printer } from 'lucide-react'
import { type CSSProperties } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { usePurchaseRequestAttachments } from '@/modules/procurement/hooks/use-purchase-request-support'
import type { AttachmentFile } from '@/modules/procurement/api/purchase-request-support-api'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDateTime } from '@/shared/utils/format-date'

import { useSealRequest } from '../hooks/use-seal-requests'
import type { SealRequest } from '../types/seal-request'

const DOTS = '..............................'

const cell: CSSProperties = { border: '1px solid #888', padding: '4px 8px', fontSize: 12, verticalAlign: 'top' }
const cellLabel: CSSProperties = { ...cell, width: '28%', color: '#334155', fontWeight: 600, background: '#f1f5f9' }
const section: CSSProperties = {
  background: '#dbe5f1',
  fontWeight: 700,
  padding: '4px 8px',
  fontSize: 12.5,
  margin: '12px 0 4px',
  border: '1px solid #c6d4e6',
}

function row(label: string, value: string) {
  return (
    <tr>
      <td style={cellLabel}>{label}</td>
      <td style={cell}>{value || DOTS}</td>
    </tr>
  )
}

/**
 * Bản in phiếu yêu cầu đóng dấu (A4). Nút In gọi `window.print()`; thanh thao tác
 * tự ẩn khi in (class `print:hidden`). Dữ liệu chỉ đọc — dùng lại đúng hook chi
 * tiết + hook đính kèm dùng chung của phân hệ Mua hàng để in kèm ảnh chứng từ đã ký.
 */
export function SealRequestPrintPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const requestId = Number(id)
  const validId = Number.isFinite(requestId) ? requestId : null
  const { data, isLoading } = useSealRequest(validId)
  const { data: attachments } = usePurchaseRequestAttachments('seal_request', validId ?? 0)

  return (
    <div className="mx-auto w-full max-w-[820px] p-4">
      <div className="mb-4 flex items-center gap-2 print:hidden">
        <Button onClick={() => window.print()}>
          <Printer className="size-4" />
          In phiếu
        </Button>
        <Button
          variant="ghost"
          onClick={() => navigate(appRoutes.approvalSeal.detail(requestId))}
        >
          <ArrowLeft className="size-4" />
          Quay lại
        </Button>
      </div>

      {isLoading || !data ? (
        <Skeleton className="h-96" />
      ) : (
        <PrintSheet request={data} attachments={attachments ?? []} />
      )}
    </div>
  )
}

function PrintSheet({
  request,
  attachments,
}: {
  request: SealRequest
  attachments: AttachmentFile[]
}) {
  const images = attachments.filter((f) => f.content_type?.startsWith('image/') && f.url)
  const others = attachments.filter((f) => !f.content_type?.startsWith('image/'))

  return (
    <div style={{ background: '#fff', color: '#0f172a', padding: 24, fontFamily: 'Arial, sans-serif' }}>
      <div style={{ textAlign: 'center', marginBottom: 12 }}>
        <div style={{ fontSize: 13, fontWeight: 700, textTransform: 'uppercase' }}>DEGO HOLDING</div>
        <h1 style={{ fontSize: 18, fontWeight: 700, margin: '10px 0 2px' }}>PHIẾU YÊU CẦU ĐÓNG DẤU</h1>
        <div style={{ fontSize: 12, color: '#475569' }}>
          Số: {request.code || '— (phiếu nháp)'}
        </div>
      </div>

      <div style={section}>A. Thông tin yêu cầu</div>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <tbody>
          {row('Mục đích sử dụng', request.purpose)}
          {row('Tên chứng từ', request.title)}
          {row('Loại con dấu', request.seal_type_name)}
          {row('Công ty cần đóng dấu', request.company_name)}
          {row('Mã số thuế', request.company_tax_code)}
          {row('Số bản', String(request.copies))}
          {row('Trưởng bộ phận phê duyệt', request.approver_name)}
          {row('Trạng thái', request.status_label)}
          {row('Ngày tạo', formatDateTime(request.created_at) || '')}
        </tbody>
      </table>

      <div style={section}>B. Người tạo</div>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <tbody>
          {row('Tên', request.requester)}
          {row('Email', request.requester_email)}
          {row('Số điện thoại', request.requester_phone)}
          {row('Vai trò', request.requester_role)}
        </tbody>
      </table>

      {request.note ? (
        <>
          <div style={section}>C. Ghi chú</div>
          <div style={{ ...cell, whiteSpace: 'pre-wrap' }}>{request.note}</div>
        </>
      ) : null}

      <div style={section}>Chứng từ đính kèm</div>
      {attachments.length === 0 ? (
        <div style={{ ...cell, color: '#64748b', fontStyle: 'italic' }}>Chưa có chứng từ đính kèm.</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {images.map((file) => (
            <figure key={file.id} style={{ margin: 0, breakInside: 'avoid' }}>
              <img
                src={file.url}
                alt={file.filename}
                style={{ width: '100%', maxHeight: 900, objectFit: 'contain', border: '1px solid #cbd5e1' }}
              />
              <figcaption style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{file.filename}</figcaption>
            </figure>
          ))}
          {others.length > 0 ? (
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12 }}>
              {others.map((file) => (
                <li key={file.id}>{file.filename}</li>
              ))}
            </ul>
          ) : null}
        </div>
      )}

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 12,
          marginTop: 28,
          textAlign: 'center',
          fontSize: 12,
        }}
      >
        {['Người yêu cầu', 'Trưởng bộ phận', 'Văn thư'].map((label) => (
          <div key={label}>
            <div style={{ fontWeight: 700 }}>{label}</div>
            <div style={{ color: '#64748b', fontStyle: 'italic' }}>(Ký, ghi rõ họ tên)</div>
            <div style={{ height: 56 }} />
          </div>
        ))}
      </div>
    </div>
  )
}
