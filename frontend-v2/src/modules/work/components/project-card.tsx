import { ChevronRight } from 'lucide-react'

import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import type { WorkList } from '../types/work'
import { dotClass } from '../utils/work-colors'
import { MemberStack, ProgressCell } from './project-cells'

/**
 * Một dự án ở chế độ MÀN HẸP — xem `DataTableProps.mobileCard`.
 *
 * Bảng khai 6 cột, bề rộng tự nhiên ~1060px: trên máy 390px chỉ thấy cột *Tên
 * dự án* (đang ghim), tức chủ sở hữu · tiến độ · thành viên đều nằm sau một
 * lượt cuộn ngang — mà tiến độ mới là thứ người ta mở màn này để xem.
 *
 * ⚠️ **Tiến độ phải ở trên thẻ, không được rút gọn thành con số.** Nó là lý do
 * tồn tại của danh sách này: thanh chạy nói ngay dự án nào đang đứng im. Bỏ nó
 * cho gọn thì thẻ chỉ còn là một cái nhãn tên, và người dùng phải mở từng dự án
 * mới biết cái nào cần đụng tới.
 *
 * ⚠️ **Mỗi dòng chữ đúng MỘT hàng, dài thì «…»** (luật chung của thẻ danh mục,
 * khách chốt 10/09/2026) — thẻ cao thấp so le nhau thì mắt phải dò lại mép trên
 * của từng thẻ thay vì lướt một cột đều.
 *
 * ⚠️ **Thẻ chỉ nói cái BẤT THƯỜNG.** Huy hiệu *Đã lưu trữ* chỉ mọc khi dự án đã
 * lưu trữ — mà danh sách mặc định không có dự án nào như vậy, nó chỉ xuất hiện
 * sau khi người dùng tự bật «Hiện cả dự án lưu trữ». Dòng mô tả cũng vậy: dự án
 * không có mô tả thì bỏ hẳn dòng, đừng in một dấu «—» cho thẳng hàng.
 */
export function ProjectCard({ project }: { project: WorkList }) {
  const owner = project.owner?.employee_name

  return (
    <div className="flex items-start gap-3">
      <span className={cn('mt-1.5 size-2.5 shrink-0 rounded-full', dotClass(project.color))} />

      <div className="min-w-0 flex-1 space-y-1.5">
        <span className="flex min-w-0 items-center gap-2">
          <span className="truncate font-medium text-foreground">{project.name}</span>
          {project.is_archived === 1 && (
            <span className="shrink-0 rounded bg-muted px-1.5 py-0.5 text-[11px] text-muted-foreground">
              Đã lưu trữ
            </span>
          )}
        </span>

        {project.description && (
          <span className="block truncate text-xs text-muted-foreground">
            {project.description}
          </span>
        )}

        {/*  Chủ sở hữu là CHỮ chứ không phải một vòng tròn chữ tắt nữa: ở bảng
             avatar đứng cạnh tên nên chữ tắt chỉ là mồi nhận diện, còn trên thẻ
             chỗ này chỉ đủ cho một dòng — hai chữ cái trong vòng tròn thì phải
             đoán, mà đoán sai người phụ trách là hỏi nhầm người. */}
        <span className="flex min-w-0 items-center gap-2 text-xs text-muted-foreground">
          <span className="truncate">{owner ? `Chủ sở hữu: ${owner}` : 'Chưa có chủ sở hữu'}</span>
          <span className="shrink-0">·</span>
          <span className="shrink-0">{formatDate(project.created_at)}</span>
        </span>

        <span className="flex items-center gap-3">
          <ProgressCell done={project.task_done} total={project.task_count} className="flex-1" />
          <MemberStack members={project.members} />
        </span>
      </div>

      {/*  Mũi tên nói THẺ NÀY BẤM ĐƯỢC: màn cảm ứng không có con trỏ đổi hình khi
           rê qua, nên phải nói bằng hình. */}
      <ChevronRight className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
    </div>
  )
}
