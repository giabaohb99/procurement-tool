import { ArrowLeft, Loader2, Printer } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Skeleton } from '@/shared/ui/skeleton'

import { LeaveRequestPrintSheet } from '../components/leave-request-print-sheet'
import { useLeaveRequest } from '../hooks/use-leave'
import { useLeaveAttachments } from '../hooks/use-leave-attachments'
import { useLeavePrintImages } from '../hooks/use-leave-print-images'
import {
  describeAttachmentsForPrint,
  splitPrintableAttachments,
} from '../utils/leave-print-attachments'

const PRINT_STYLES = `
  @page {
    size: A4 portrait;
    margin: 0;
  }
  @media print {
    html, body {
      margin: 0 !important;
      padding: 0 !important;
      background: #fff !important;
    }
    .no-print,
    .tsqd-parent-container,
    [class*="tsqd"],
    [data-sonner-toaster] {
      display: none !important;
    }
    .a4-print-page {
      padding: 0 !important;
      background: transparent !important;
      min-height: 0 !important;
    }
    .a4-print-sheet {
      margin: 0 !important;
      padding: 20mm !important;
      box-shadow: none !important;
      border: none !important;
      width: 100% !important;
      min-height: 0 !important;
    }
    /*  Trang ảnh đính kèm (bao-CR-505): cao 296mm chứ không 297mm — làm tròn
        điểm ảnh dôi ra một phần nhỏ là trình duyệt đẻ thêm một trang trắng sau
        mỗi ảnh. */
    .a4-image-sheet {
      margin: 0 !important;
      box-shadow: none !important;
      width: 210mm !important;
      height: 296mm !important;
    }
  }
  /*  Mỗi ảnh đính kèm bắt đầu một trang MỚI — in hai mặt thì ảnh đầu tiên rơi
      đúng mặt sau của tờ đơn. Khai cả hai tên thuộc tính: page-break-* cho
      trình duyệt cũ, break-* là chuẩn hiện hành. */
  .a4-image-sheet {
    page-break-before: always;
    break-before: page;
    page-break-inside: avoid;
    break-inside: avoid;
    overflow: hidden;
  }
`

export function LeaveRequestPrintPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const requestId = Number(id) || 0
  const { data: request, isLoading } = useLeaveRequest(requestId)

  //  Ảnh đính kèm in ở mặt sau, mỗi ảnh một trang (bao-CR-505). Tệp khác chỉ
  //  ghi tên trên mặt đơn.
  const { data: attachments, isLoading: attachmentsLoading } = useLeaveAttachments(requestId)
  const { images, others } = splitPrintableAttachments(attachments)
  const { sources, ready } = useLeavePrintImages(images)
  const failed = sources.filter((s) => s.src === null)
  //  Khóa nút In tới khi mọi ảnh đã về: bấm sớm là mặt sau in ra trang trắng.
  const imagesPending = attachmentsLoading || !ready

  return (
    <main className="a4-print-page min-h-[100dvh] bg-slate-200 p-6 no-print:pb-12">
      <style>{PRINT_STYLES}</style>

      {/* Thanh công cụ (ẩn khi in) */}
      <div className="no-print mx-auto mb-4 flex max-w-[210mm] items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Button onClick={() => window.print()} disabled={imagesPending}>
            {imagesPending ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Printer className="size-4" />
            )}
            {imagesPending ? 'Đang nạp ảnh đính kèm…' : 'In đơn / Lưu PDF'}
          </Button>
          <Button
            variant="outline"
            onClick={() =>
              requestId > 0
                ? navigate(appRoutes.hr.leaveRequestDetail(requestId))
                : navigate(-1)
            }
          >
            <ArrowLeft className="size-4" />
            Quay lại
          </Button>
        </div>

        {request && (
          <span className="text-sm font-medium text-slate-700">
            {request.code || 'Đơn nghỉ phép'} · Khổ A4 chuẩn
          </span>
        )}
      </div>

      {failed.length > 0 && (
        //  Ảnh lấy không được thì KHÔNG in trang trống thay nó, nhưng phải nói ra
        //  — không thì người in tưởng đơn chỉ kèm ngần ấy ảnh.
        <p
          role="alert"
          className="no-print mx-auto mb-4 max-w-[210mm] rounded-md border border-destructive/40 bg-white px-3 py-2 text-sm text-destructive"
        >
          Không tải được ảnh đính kèm: {failed.map((s) => s.filename).join(', ')}. Bản in sẽ
          thiếu các ảnh này.
        </p>
      )}

      {isLoading || !request ? (
        <div className="mx-auto max-w-[210mm]">
          <Skeleton className="mb-4 h-10 w-48" />
          <Skeleton className="h-[297mm] w-full bg-white shadow-xl" />
        </div>
      ) : (
        <>
          <LeaveRequestPrintSheet
            request={request}
            attachmentNote={describeAttachmentsForPrint(images, others)}
          />
          {sources.map(
            (source) =>
              source.src && (
                <div
                  key={source.id}
                  className="a4-image-sheet mx-auto mt-6 flex items-center justify-center bg-white shadow-xl"
                  style={{ width: '210mm', height: '297mm', padding: '10mm', boxSizing: 'border-box' }}
                >
                  {/*  `max-*` + `object-contain`: ảnh dọc hay ngang đều co vừa
                       khung trang, giữ nguyên tỉ lệ, không cắt xén. */}
                  <img
                    src={source.src}
                    alt={source.filename}
                    className="block max-h-full max-w-full object-contain"
                  />
                </div>
              ),
          )}
        </>
      )}
    </main>
  )
}
