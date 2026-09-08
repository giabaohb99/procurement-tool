import { Search } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable } from '@/shared/data-table'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { nameInitials } from '@/shared/utils/name-initials'
import { useEmployees } from '../hooks/use-employees'
import { useJobPositionStats } from '../hooks/use-job-positions'
import { EMPLOYEE_STATUS_OPTIONS } from '../types/employee'
import type { Employee } from '../types/employee'

/** Không lọc phòng ban nào cả — xem chú thích ở `departmentId`. */
const ALL_DEPARTMENTS = -1

/**
 * Tab «Người đang giữ» của một chức vụ (duoc-CR-322) — đếm ngược từ hồ sơ.
 *
 * Trả lời hai câu người quản lý danh mục thực sự hỏi trước khi sửa hay dẹp một
 * chức vụ: *bao nhiêu người đang mang chức danh này* và *họ nằm ở phòng nào*.
 * Không có nó thì việc duy nhất làm được là bấm Xóa rồi đọc câu từ chối.
 *
 * ⚠️ Đây là tab MƯỢN dữ liệu của phân hệ khác, nên phải tự tắt khi thiếu quyền
 * `employee.read` — cứ mount là gọi thì người dùng ăn toast 403 ngay lúc mở tab
 * (bẫy đã dính ở tab «Công nợ» của Nhà cung cấp).
 *
 * ⚠️ Danh sách này **lọc theo phạm vi dữ liệu** của người đang xem, y như màn
 * Nhân sự. Nên nó có thể ngắn hơn con số backend nêu khi từ chối xóa — câu chặn
 * đó nói rõ «trên toàn công ty» đúng vì lý do này.
 *
 * ⚠️ **Phân trang THẬT, không cắt trần rồi thôi** (08/09/2026). Bản đầu lấy 200
 * dòng một lượt và chỉ ghi một dòng chú thích khi vượt — nghĩa là chức vụ đông
 * người thì phần đuôi **không có cách nào xem được từ màn này**, phải sang màn
 * Nhân sự mà lọc lại từ đầu. «Nhân viên» là chức vụ mà cả công ty cùng mang,
 * nên đó không phải trường hợp hiếm.
 *
 * ⚠️ MỘT thẻ, bộ lọc phòng ban nằm trong THANH CÔNG CỤ của bảng. Bản trước tách
 * một thẻ tóm tắt riêng ở trên với dãy chip phòng ban: nó chiếm nguyên một khối
 * chỉ để nói con số mà chân bảng đã nói (*«Tổng 11 người»*), và dãy chip dài ra
 * theo số phòng ban — công ty mười phòng là nó tràn hai dòng, đẩy bảng xuống
 * dưới mép màn hình. Ô chọn thì cao bằng nhau bất kể bao nhiêu phòng.
 */
export function JobPositionHoldersPanel({ positionId }: { positionId: number }) {
  const navigate = useNavigate()
  const { can } = usePermission()
  const allowed = can('employee', 'read')

  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  //  ⚠️ Sentinel «mọi phòng ban» là `-1`, KHÔNG phải `0`. Nhóm giả «(Chưa gắn
  //  phòng ban)» mang đúng `id = 0` — lấy `0` làm «tất cả» thì chọn chính nhóm
  //  đó lại ra toàn bộ danh sách, và những hồ sơ chưa gắn phòng thành thứ duy
  //  nhất không lọc ra được. `department_id=0` là một bộ lọc THẬT: `apply_filters`
  //  so khớp chính xác nên nó trả về đúng nhóm chưa gắn.
  const [departmentId, setDepartmentId] = useState(ALL_DEPARTMENTS)
  //  `''` = mọi tình trạng. Ở đây mã tình trạng là CHUỖI (`EMPLOYEE_STATUS`,
  //  ngoại lệ lịch sử B-03) nên chuỗi rỗng làm sentinel được, khác `departmentId`.
  const [status, setStatus] = useState('')
  const [keyword, setKeyword] = useState('')
  //  Gõ tới đâu gọi API tới đó thì mỗi ký tự một request.
  const search = useDebouncedValue(keyword)

  //  ⚠️ Đổi BẤT KỲ bộ lọc nào cũng phải về trang 1 — đứng ở trang 4 rồi lọc còn
  //  3 người thì backend trả rỗng, và người dùng đọc ra «phòng này không có ai».
  //
  //  Dùng hook chung chứ không `useEffect(() => setPage(1), [...])`: effect chạy
  //  SAU khi commit, nên lượt render đầu sau khi đổi bộ lọc vẫn gọi API với số
  //  trang cũ — một request thừa vào trang không còn tồn tại. Hook so ngay trong
  //  lúc render nên không có lượt gọi đó (và ESLint cũng chặn setState trong
  //  effect).
  //
  //  ⚠️ Theo dõi `search` (giá trị ĐÃ HOÃN), không theo `keyword`: theo `keyword`
  //  là mỗi ký tự gõ ra một lần đặt lại trang, kể cả khi truy vấn chưa hề đổi.
  const [page, setPage] = usePageResetOnFilterChange([search, status, departmentId])

  const { data: stats } = useJobPositionStats(allowed)
  const departments = stats?.get(positionId)?.departments ?? []

  const { data, isLoading, isError } = useEmployees(
    {
      position_id: positionId,
      page,
      page_size: pageSize,
      ...(departmentId === ALL_DEPARTMENTS ? {} : { department_id: departmentId }),
      ...(status ? { status } : {}),
      //  `search` quét đồng thời mã NV / họ tên / email / điện thoại (OR) —
      //  xem `apply_keyword_search`. Khác `apply_filters`: ở đó mỗi tham số lọc
      //  riêng một cột rồi ghép AND.
      ...(search ? { search } : {}),
    },
    { enabled: allowed },
  )

  if (!allowed) {
    return (
      <Card className="p-5 text-sm text-muted-foreground">
        Bạn không có quyền xem hồ sơ nhân sự nên không xem được ai đang giữ chức vụ này.
      </Card>
    )
  }

  const grandTotal = departments.reduce((sum, dept) => sum + dept.count, 0)

  return (
    <Card className="p-4">
      <DataTable
        columns={[
          {
            key: 'code',
            header: 'Mã NV',
            width: 130,
            cell: (row: Employee) => (
              <span className="font-semibold text-primary">{row.code}</span>
            ),
          },
          {
            key: 'full_name',
            header: 'Họ tên',
            width: 260,
            cell: (row: Employee) => (
              <span className="flex items-center gap-2">
                <Avatar size="sm">
                  {row.avatar && <AvatarImage src={row.avatar} alt={row.full_name} />}
                  <AvatarFallback className="bg-primary/10 text-[10px] font-medium text-primary">
                    {nameInitials(row.full_name)}
                  </AvatarFallback>
                </Avatar>
                <span className="font-medium">{row.full_name}</span>
              </span>
            ),
          },
          {
            key: 'department_name',
            header: 'Phòng ban',
            width: 240,
            cell: (row: Employee) => row.department_name || '(Chưa gắn phòng ban)',
          },
          {
            key: 'status',
            header: 'Tình trạng',
            width: 150,
            //  Đọc `status_label` backend gửi kèm, đừng tự dịch mã ở đây — bộ mã
            //  đổi thì chỉ một chỗ phải sửa.
            cell: (row: Employee) => row.status_label || '—',
          },
        ]}
        rows={data?.items}
        getRowId={(row: Employee) => String(row.id)}
        isLoading={isLoading}
        isError={isError}
        emptyMessage={
          //  Nói rõ RỖNG VÌ BỘ LỌC hay rỗng vì thật sự chưa ai giữ. Một câu
          //  chung cho cả hai thì người vừa gõ nhầm một chữ trong ô tìm kiếm
          //  đọc ra «chức vụ này chưa ai giữ» và tin là vậy.
          keyword || status || departmentId !== ALL_DEPARTMENTS
            ? 'Không có hồ sơ nào khớp bộ lọc đang đặt.'
            : 'Chưa có hồ sơ nào giữ chức vụ này.'
        }
        onRowClick={(row: Employee) => navigate(appRoutes.hr.employeeDetail(row.id))}
        toolbar={
          <>
            <div className="relative w-64 max-w-sm">
              <Search className="absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Tìm mã NV, họ tên, email, SĐT…"
                value={keyword}
                onChange={(event) => setKeyword(event.target.value)}
                className="h-9 bg-background pl-8 text-xs"
              />
            </div>

            {/*  Ô chọn phòng ban chỉ dựng khi CÓ người giữ: chức vụ chưa ai giữ
                 thì danh sách phòng rỗng, bày ra một ô chọn không có mục nào. */}
            {departments.length > 0 && (
              <Select
                value={String(departmentId)}
                onValueChange={(value) => setDepartmentId(Number(value))}
              >
                <SelectTrigger className="h-9 w-56 text-xs">
                  <SelectValue placeholder="Phòng ban" />
                </SelectTrigger>
                <SelectContent>
                  {/*  Kèm số ngay trong mục chọn: đó là thứ dãy chip cũ nói được
                       mà một ô chọn trần thì không. */}
                  <SelectItem value={String(ALL_DEPARTMENTS)}>
                    Tất cả phòng ban ({grandTotal})
                  </SelectItem>
                  {departments.map((dept) => (
                    <SelectItem key={dept.id} value={String(dept.id)}>
                      {dept.name} ({dept.count})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}

            <Select
              value={status || 'all'}
              onValueChange={(value) => setStatus(value === 'all' ? '' : value)}
            >
              <SelectTrigger className="h-9 w-44 text-xs">
                <SelectValue placeholder="Tình trạng" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tất cả tình trạng</SelectItem>
                {/*  ⚠️ `value` phải là MÃ, không phải nhãn: cột `status` lưu mã
                     chuỗi (B-03). Gửi nhãn thì backend vẫn nhận câu lọc, chỉ là
                     trả về 0 dòng mà không báo lỗi gì — đúng bẫy CR-118. */}
                {EMPLOYEE_STATUS_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </>
        }
        pagination={{
          page,
          pageSize,
          total: data?.total ?? 0,
          onPageChange: setPage,
          onPageSizeChange: (size) => {
            setPageSize(size)
            setPage(1)
          },
          unitLabel: 'người',
        }}
      />
    </Card>
  )
}
