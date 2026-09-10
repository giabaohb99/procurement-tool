import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable } from '@/shared/data-table'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Badge } from '@/shared/ui/badge'
import { Card } from '@/shared/ui/card'
import { QuickFilterField, QuickFilterSheet } from '@/shared/ui/quick-filter-sheet'
import { SearchField } from '@/shared/ui/search-field'
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

//  Mã tình trạng BÌNH THƯỜNG của một nhân sự đang làm việc. Thẻ ở khổ hẹp im
//  lặng với mã này và chỉ lên tiếng ở ba mã còn lại — xem `mobileCard`.
//  ⚠️ `official`, KHÔNG phải `active`: bộ mã ở `shared/constants/statuses.ts`
//  (sinh từ backend) không hề có mã nào tên `active`, đoán tên là huy hiệu
//  «Chính thức» hiện trên mọi thẻ.
const STATUS_NORMAL = 'official'

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
 *
 * ⚠️ **Khổ hẹp: hai ô chọn dời vào TỜ TRƯỢT** (10/09/2026). Ba ô công cụ khai
 * bề rộng CỨNG (256 · 224 · 176) trong một thẻ chỉ rộng 322px, nên mỗi ô rớt
 * xuống một hàng riêng và ba hàng dài ngắn khác nhau xếp thành bậc thang, còn
 * nút *Tải lại* thì đứng lẻ tận mép phải hàng thứ ba — 150px đầu tab không nói
 * được gì ngoài "có ba cái ô". Bề rộng cứng nay chỉ áp từ `md` (`md:w-56`), dưới
 * ngưỡng đó ô chọn trải hết bề ngang tờ trượt.
 */
export function JobPositionHoldersPanel({ positionId }: { positionId: number }) {
  const navigate = useNavigate()
  const { can } = usePermission()
  const allowed = can('employee', 'read')
  const isMobile = useIsMobile()

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

  const filtering = Boolean(search || status) || departmentId !== ALL_DEPARTMENTS

  //  ⚠️ **CHỨC VỤ MỘT NGƯỜI THÌ KHÔNG CÓ GÌ ĐỂ TÌM.** Thanh công cụ mang ô tìm
  //  + nút *Bộ lọc* + nút *Tải lại*, chân bảng mang thêm ô chọn số dòng và ba
  //  nút trang: sáu ô điều khiển vây quanh **một dòng nội dung**, phần điều
  //  khiển cao gấp ba phần đáng đọc (đo ở chức vụ *Trưởng bộ phận*, báo
  //  10/09/2026). Cùng luật với `ColumnVisibilityMenu` — thứ không điều khiển
  //  được gì thì đừng mời người ta bấm vào.
  //
  //  ⚠️ Mốc so là `data.total` LÚC KHÔNG LỌC nên không nhốt được ai: hễ đang có
  //  bộ lọc là thanh công cụ ở lại, kể cả khi lọc xong còn đúng một người —
  //  không thì đường duy nhất để bỏ lọc cũng biến mất theo.
  const showToolbar = filtering || (data ? data.total > 1 : false)

  //  ⚠️ Hai ô chọn dựng MỘT LẦN rồi bày ở HAI chỗ: hàng ngang của thanh công cụ
  //  từ `md`, tờ trượt lọc ở dưới ngưỡng đó. State nằm ở component này nên hai
  //  bản luôn nói cùng một giá trị — khuôn của `leave-balance-page`, không phải
  //  bản chép cần dọn.
  //
  //  ⚠️ Ô chọn phòng ban đòi **từ HAI phòng trở lên**, không phải "có phòng nào
  //  thì bày": cả danh sách nằm gọn trong một phòng thì «Tất cả phòng ban (5)»
  //  và «Phòng Kinh doanh (5)» trả về đúng cùng một kết quả — một ô chọn hỏi
  //  người dùng một câu mà mọi câu trả lời đều như nhau.
  const departmentSelect = departments.length > 1 && (
    <Select
      value={String(departmentId)}
      onValueChange={(value) => setDepartmentId(Number(value))}
    >
      <SelectTrigger className="h-9 w-full text-xs md:w-56" aria-label="Lọc theo phòng ban">
        <SelectValue placeholder="Phòng ban" />
      </SelectTrigger>
      <SelectContent>
        {/*  Kèm số ngay trong mục chọn: đó là thứ dãy chip cũ nói được mà một ô
             chọn trần thì không. */}
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
  )

  const statusSelect = (
    <Select
      value={status || 'all'}
      onValueChange={(value) => setStatus(value === 'all' ? '' : value)}
    >
      <SelectTrigger className="h-9 w-full text-xs md:w-44" aria-label="Lọc theo tình trạng">
        <SelectValue placeholder="Tình trạng" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all">Tất cả tình trạng</SelectItem>
        {/*  ⚠️ `value` phải là MÃ, không phải nhãn: cột `status` lưu mã chuỗi
             (B-03). Gửi nhãn thì backend vẫn nhận câu lọc, chỉ là trả về 0 dòng
             mà không báo lỗi gì — đúng bẫy CR-118. */}
        {EMPLOYEE_STATUS_OPTIONS.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  return (
    //  Lề trong hẹp lại ở khổ điện thoại — 8px lấy lại được là 8px cho ô tìm,
    //  thứ đang chật nhất trong hàng công cụ.
    <Card className="p-3 md:p-4">
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
        //  Khổ hẹp: THẺ thay bảng. Bốn cột cộng lại 780px, trên máy 390px chỉ
        //  thấy *Mã NV* + *Họ tên* — tức mất đúng hai cột trả lời câu hỏi của
        //  tab này (*họ ở phòng nào*, *còn làm việc không*).
        //
        //  Không dùng `CrudRecordCard` như màn danh sách: thẻ đó dựng cho một
        //  bản ghi DANH MỤC (tên + huy hiệu), còn ở đây thứ nhận ra một người
        //  là GƯƠNG MẶT, nên ảnh phải đứng đầu thẻ.
        mobileCard={(row: Employee) => (
          <div className="flex items-center gap-3">
            <Avatar size="sm" className="shrink-0">
              {row.avatar && <AvatarImage src={row.avatar} alt={row.full_name} />}
              <AvatarFallback className="bg-primary/10 text-[10px] font-medium text-primary">
                {nameInitials(row.full_name)}
              </AvatarFallback>
            </Avatar>

            <div className="min-w-0 flex-1">
              <span className="block truncate font-medium text-foreground">{row.full_name}</span>
              <span className="block truncate text-xs text-muted-foreground">
                {row.code} · {row.department_name || '(Chưa gắn phòng ban)'}
              </span>
            </div>

            {/*  Tình trạng chỉ nói khi KHÁC «Đang làm việc»: cả trăm hồ sơ đều
                 đang làm việc nên in ra là trăm dòng giống hệt nhau, còn người
                 đã nghỉ mới là thứ người quản lý danh mục cần nhặt ra. */}
            {row.status !== STATUS_NORMAL && row.status_label && (
              <Badge variant="outline" className="shrink-0">
                {row.status_label}
              </Badge>
            )}
          </div>
        )}
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
          showToolbar && (
            <>
              {/*  ⚠️ Câu gợi ý RÚT GỌN ở khổ hẹp — và phải đo theo lúc ĐANG LỌC,
                   không phải lúc thảnh thơi. Nút *Bộ lọc* nở thêm 24px khi mọc
                   huy hiệu số, nên phần gõ chữ tụt từ 141px xuống **117px**: bản
                   «Tìm mã NV, họ tên…» (130px) vừa khít lúc chưa lọc rồi cụt đuôi
                   ngay khi người dùng chọn một phòng ban. Bản này 110px, còn dư ở
                   cả hai trạng thái.
                   Rút bằng tay chứ không để trình duyệt cắt: chữ đứt giữa từ đọc
                   ra như lỗi vẽ, còn «…» sau một cụm trọn nghĩa thì đọc ra là
                   "còn tìm được thứ khác nữa". Bản đầy đủ giữ từ `md` — ở đó ô
                   rộng 224px. */}
              <SearchField
                value={keyword}
                onChange={setKeyword}
                placeholder={isMobile ? 'Tìm tên, mã NV…' : 'Tìm mã NV, họ tên, email, SĐT…'}
                className="md:min-w-56 md:max-w-xs"
              />

              <QuickFilterSheet
                activeCount={(departmentId !== ALL_DEPARTMENTS ? 1 : 0) + (status ? 1 : 0)}
                onClearAll={() => {
                  setDepartmentId(ALL_DEPARTMENTS)
                  setStatus('')
                }}
              >
                {departmentSelect && (
                  <QuickFilterField label="Phòng ban">{departmentSelect}</QuickFilterField>
                )}
                <QuickFilterField label="Tình trạng">{statusSelect}</QuickFilterField>
              </QuickFilterSheet>

              <div className="hidden items-center gap-3 md:flex">
                {departmentSelect}
                {statusSelect}
              </div>
            </>
          )
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
