import type { CSSProperties } from 'react'

import { cn } from '@/shared/utils/cn'

/**
 * Biến CSS của FullCalendar, nối vào token giao diện (v6 tự nhúng CSS nên chỉ
 * cần đặt biến, không phải nạp tệp .css nào).
 *
 * `--fc-today-bg-color` để TRONG SUỐT: Google Calendar không tô cả ô hôm nay,
 * nó chỉ khoanh tròn con số — phần khoanh tròn làm bằng lớp Tailwind bên dưới.
 * Nút điều hướng đổi sang dáng "outline" nhạt thay vì khối xanh đặc.
 */
export const FC_THEME_VARS = {
  '--fc-border-color': 'color-mix(in oklab, var(--border) 70%, transparent)',
  '--fc-page-bg-color': 'transparent',
  '--fc-neutral-bg-color': 'var(--muted)',
  '--fc-today-bg-color': 'transparent',
  '--fc-button-bg-color': 'transparent',
  '--fc-button-border-color': 'var(--border)',
  '--fc-button-text-color': 'var(--foreground)',
  '--fc-button-hover-bg-color': 'var(--muted)',
  '--fc-button-hover-border-color': 'var(--border)',
  '--fc-button-active-bg-color': 'var(--muted)',
  '--fc-button-active-border-color': 'var(--border)',
  //  Vạch "bây giờ" mặc định của FC là ĐỎ NGUYÊN (#f00) — chói hơn mọi màu khác
  //  trên trang, kể cả màu trạng thái đậm nhất. Đổi sang đỏ Google Calendar.
  '--fc-now-indicator-color': '#EA4335',
} as CSSProperties

/**
 * Lớp style lưới lịch theo lối Google Calendar. Gom vào một chỗ vì toàn bộ là
 * ghi đè DOM của FullCalendar (không có prop nào làm được), mỗi dòng một ý.
 */
export const CALENDAR_GRID_CLASSES = cn(
  //  Thẻ chiếm hết chiều cao còn lại của khung; `min-h-0` để nó CO được trong
  //  flex cha (thiếu là nội dung đẩy thẻ dài ra và trang lại sinh cuộn).
  //  Lề trong mỏng (p-2/p-3) để ô ngày to nhất có thể — lịch là toàn bộ nội
  //  dung của trang này nên không cần chừa lề rộng như thẻ biểu mẫu.
  'min-h-0 flex-1 gap-0 p-2 sm:p-3',
  //  Gốc FullCalendar cũng phải giãn theo, `height="100%"` mới có mốc để chia đều.
  '[&>.fc]:min-h-0 [&>.fc]:flex-1',
  //  Hàng tiêu đề: chữ hoa nhỏ, nhạt, không viền dọc chia cột.
  //
  //  Bắt buộc `!`: FC v6 nhồi `.fc-theme-standard td, th { border: 1px … }` vào
  //  <head> LÚC CHẠY, tức sau Tailwind — cùng độ ưu tiên thì nó thắng vì đứng sau.
  //  (Dòng này viết `border-0` không `!` từ đầu nên suốt thời gian qua KHÔNG ăn.)
  '[&_.fc-col-header-cell]:!border-0 [&_.fc-col-header-cell]:py-2',
  '[&_.fc-col-header-cell-cushion]:text-[11px] [&_.fc-col-header-cell-cushion]:font-semibold',
  '[&_.fc-col-header-cell-cushion]:uppercase [&_.fc-col-header-cell-cushion]:tracking-wide',
  '[&_.fc-col-header-cell-cushion]:text-muted-foreground',

  //  ================= Khám THÁNG (dayGrid) =================
  //  Ô ngày KHÔNG có lề trong: chip chạy hết bề ngang ô, dính sát viền lưới.
  //  Chiều cao do `height="100%"` chia đều 6 hàng nên không đặt `min-h` ở đây
  //  (đặt là hàng phình ra và trang lại sinh cuộn).
  '[&_.fc-daygrid-day-frame]:p-0',
  //  Lề của số ngày dựng riêng, vì ô đã bỏ lề trong.
  '[&_.fc-daygrid-day-top]:pt-1 [&_.fc-daygrid-day-top]:pb-0.5',

  //  Số ngày: nhỏ, căn giữa ở đỉnh ô — FC mặc định xếp ngược về bên phải.
  '[&_.fc-daygrid-day-top]:justify-center',
  '[&_.fc-daygrid-day-number]:px-0 [&_.fc-daygrid-day-number]:py-0.5',
  '[&_.fc-daygrid-day-number]:text-[11px] [&_.fc-daygrid-day-number]:font-semibold',
  '[&_.fc-daygrid-day-number]:text-muted-foreground',
  //  Hôm nay: con số nằm trong vòng tròn đặc (dấu hiệu của Google Calendar).
  '[&_.fc-day-today_.fc-daygrid-day-number]:flex [&_.fc-day-today_.fc-daygrid-day-number]:size-[22px]',
  '[&_.fc-day-today_.fc-daygrid-day-number]:items-center [&_.fc-day-today_.fc-daygrid-day-number]:justify-center',
  '[&_.fc-day-today_.fc-daygrid-day-number]:rounded-full',
  '[&_.fc-day-today_.fc-daygrid-day-number]:bg-primary [&_.fc-day-today_.fc-daygrid-day-number]:!text-primary-foreground',
  //  Ngày của tháng khác: mờ hẳn đi cho tháng đang xem nổi lên.
  '[&_.fc-day-other_.fc-daygrid-day-number]:opacity-45',
  //  Khe 3px giữa các chip — đặt bằng `margin-bottom` của CHÍNH CHIP, KHÔNG
  //  bằng `margin-top` của harness.
  //
  //  Lý do (bug đã gặp 15/09/2026): FullCalendar tự ghi `margin-top` INLINE lên
  //  các harness nằm trong luồng để chèn tầng (vd `29px` cho chip xếp dưới một
  //  thanh nhiều ngày), và inline style đó ĐÈ lớp Tailwind. Kết quả: khe chỉ
  //  hiện ở chip định vị tuyệt đối (chuyến nhiều ngày), còn chip trong ngày thì
  //  dán sát nhau — cùng một tháng mà hai ô hiện hai kiểu.
  //
  //  FC tính BƯỚC TẦNG từ chiều cao chip nó đo được. Cho chip chừa 3px dưới thì
  //  bước tầng thành 31px trong khi phần tô màu vẫn 28px → khe 3px đều khắp,
  //  cả hai loại chip, không phải giành với inline style nào.
  '[&_.fc-daygrid-event]:!mt-0 [&_.fc-daygrid-event]:!mb-[3px]',
  //  Thụt 3px khỏi mép ô, đúng như Google Calendar — dán sát viền lưới thì chip
  //  trông như tràn ra khỏi ngày của nó. Đặt trên `harness` chứ không trên
  //  `day-events`: chip NHIỀU NGÀY nằm ngoài khối đó (FC định vị tuyệt đối
  //  theo hàng), nên lề đặt ở `day-events` chỉ ăn cho chip trong ngày.
  '[&_.fc-daygrid-event-harness]:mx-[3px]',
  '[&_.fc-daygrid-day-events]:mt-0 [&_.fc-daygrid-day-events]:mb-0',
  //  Link "+N nữa": chữ nhỏ nhạt, không in đậm như mặc định.
  '[&_.fc-daygrid-more-link]:mt-0.5 [&_.fc-daygrid-more-link]:px-1',
  '[&_.fc-daygrid-more-link]:text-[11px] [&_.fc-daygrid-more-link]:font-medium',
  '[&_.fc-daygrid-more-link]:text-muted-foreground [&_.fc-daygrid-more-link]:hover:underline',
  //  Chữ trong chip do chip tự lo màu — chặn màu link mặc định của FC.
  '[&_.fc_a]:!text-inherit',

  //  --- Hộp "+N chuyến nữa" (popover khám Tháng) ---
  //  NỀN ĐẶC là bắt buộc, không phải trang trí: FC khai
  //  `.fc-theme-standard .fc-popover { background: var(--fc-page-bg-color) }`, mà
  //  biến đó ở `FC_THEME_VARS` để `transparent` (cố ý — lưới ngồi thẳng trên mặt
  //  Card). Hệ quả: hộp này TRONG SUỐT, chip và chữ "+N chuyến nữa" của lưới phía
  //  sau xuyên qua, chữ chồng chữ. Không sửa bằng cách đổi biến chung — biến đó
  //  còn là nền của cả lưới; ghi đè đúng một mình hộp popover.
  //
  //  Mọi dòng phải có `!`: FC v6 nhồi CSS vào <head> LÚC CHẠY, tức sau Tailwind,
  //  nên cùng độ ưu tiên thì FC thắng vì đứng sau.
  '[&_.fc-popover]:!bg-popover [&_.fc-popover]:!text-popover-foreground',
  '[&_.fc-popover]:!border-border [&_.fc-popover]:!rounded-lg',
  '[&_.fc-popover]:!overflow-hidden [&_.fc-popover]:!shadow-lg',
  //  z-index 40, KHÔNG để nguyên 9999 của FC: chip trong hộp có thẻ hover
  //  (HoverCard), mà Radix cắm thẻ đó ra `document.body` với `z-50` — 50 < 9999
  //  nên thẻ chi tiết chui XUỐNG DƯỚI hộp, người dùng trỏ vào chuyến mà không
  //  thấy gì. 40 vừa đủ nằm trên lưới (lưới không khai z-index) và nằm dưới mọi
  //  lớp nổi của shadcn (hover card · popover · dialog đều z-50), đúng thứ tự.
  '[&_.fc-popover]:!z-40',
  //  Đầu hộp: nền theo mặt hộp (FC mặc định tô `--fc-neutral-bg-color` thành một
  //  dải xám), ngăn cách bằng một kẻ mảnh. Chữ về 13px như mọi tiêu đề phụ khác.
  '[&_.fc-popover-header]:!bg-transparent [&_.fc-popover-header]:!border-b',
  '[&_.fc-popover-header]:!px-3 [&_.fc-popover-header]:!py-2',
  '[&_.fc-popover-title]:!m-0 [&_.fc-popover-title]:!text-[13px]',
  '[&_.fc-popover-title]:!font-semibold',
  //  Nút đóng: FC để một glyph mờ 65% không có vùng bấm — nới thành ô 24px có
  //  nền khi trỏ vào, đủ khổ chạm trên màn cảm ứng.
  '[&_.fc-popover-close]:!grid [&_.fc-popover-close]:!size-6',
  '[&_.fc-popover-close]:!place-items-center [&_.fc-popover-close]:!rounded-md',
  '[&_.fc-popover-close]:!opacity-100 [&_.fc-popover-close]:!text-muted-foreground',
  '[&_.fc-popover-close]:hover:!bg-muted [&_.fc-popover-close]:hover:!text-foreground',
  //  Thân hộp: TRẦN CHIỀU CAO + cuộn. Thiếu trần thì ngày 20 chuyến ra hộp cao
  //  hơn cửa sổ và mấy chuyến cuối nằm ngoài màn, không cách nào với tới.
  '[&_.fc-popover-body]:!p-2 [&_.fc-popover-body]:!min-w-[260px]',
  '[&_.fc-popover-body]:!max-h-[min(340px,60vh)] [&_.fc-popover-body]:!overflow-y-auto',
  //  Chip trong hộp bám lề của thân hộp, bỏ 3px thụt vốn dành cho ô ngày.
  '[&_.fc-popover_.fc-daygrid-event-harness]:!mx-0',

  //  ================= Khám NGÀY · TUẦN (timeGrid) =================
  //  --- Đường kẻ dưới hàng tiêu đề, và luật "mỗi ranh giới đúng MỘT kẻ" ---
  //
  //  Lưới giờ CUỘN được (`expandRows: false`), mà FC dựng hàng tiêu đề ở một khối
  //  riêng KHÔNG cuộn theo. Nên kẻ dưới chân tiêu đề phải là của CHÍNH hàng tiêu
  //  đề: mượn mép trên của lưới thì kẻ đó trôi mất ngay khi người dùng cuộn xuống
  //  một chút, và tiêu đề lơ lửng trên nội dung đang chạy qua dưới nó.
  //
  //  Đặt trên `<th>` bao cả khối (không trên từng ô) để kẻ chạy suốt bề ngang,
  //  qua cả cột trục giờ — đặt trên `.fc-col-header-cell` thì đoạn trên cột trục
  //  bị hụt, nhìn ra như tiêu đề mất viền.
  '[&_.fc-timegrid_.fc-scrollgrid-section-header>th]:!border-b',
  //  Ô GÓC trên-trái là `<th.fc-timegrid-axis>`, KHÔNG mang lớp `.fc-col-header-cell`
  //  nên luật bỏ viền của hàng tiêu đề không với tới nó: nó giữ nguyên viền mặc
  //  định của FC và vẽ thêm một kẻ nữa, lệch 1.5px so với kẻ chính — góc trái
  //  thành ba kẻ chồng nhau trong 3px.
  '[&_.fc-col-header_.fc-timegrid-axis]:!border-0',
  //  …và mọi thứ nằm DƯỚI kẻ đó đều bỏ mép trên của mình đi, nếu không là hai kẻ
  //  cách nhau 1px — mắt đọc thành một viền dày bị nhòe. Ranh giới dưới của dải
  //  "Cả ngày" thì do CHÍNH nó vẽ (`border-b`), nên dải ẩn đi là kẻ đó biến mất
  //  theo, không để lại kẻ mồ côi.
  '[&_.fc-timegrid_tr:has(.fc-daygrid-body)_td]:!border-t-0',
  '[&_.fc-timegrid_tr:has(.fc-daygrid-body)_td]:!border-b',
  //  Lưới giờ có HAI bảng chồng nhau — `.fc-timegrid-slots` (kẻ ngang từng giờ)
  //  và `.fc-timegrid-cols` (cột chứa chuyến). Cả hai đều có mép trên riêng, bỏ
  //  một cái thì cái còn lại vẫn vẽ kẻ. Phải gỡ cả hai.
  '[&_.fc-timegrid-slots_tr:first-child_td]:!border-t-0',
  '[&_.fc-timegrid-col]:!border-t-0',
  //  --- Chiều cao mỗi giờ: GHIM, phần dôi thì cuộn ---
  //  48px/giờ = mốc của Google Calendar, và là mức thấp nhất còn đọc được cả giờ
  //  lẫn mục đích trên một chuyến 1 tiếng (sàn chip là 28px).
  '[&_.fc-timegrid-slot]:!h-12',
  //  Cả khối này thiếu hẳn cho tới 16/09/2026: hai khám đó dựng sau khám Tháng
  //  và chạy nguyên dáng mặc định của FC, nên chữ trên trục giờ TO HƠN cả tiêu
  //  đề cột (16px, màu xanh đen đặc) trong khi mọi chữ phụ khác trên trang là
  //  11px nhạt.
  '[&_.fc-timegrid-slot-label-cushion]:text-[11px] [&_.fc-timegrid-slot-label-cushion]:font-medium',
  '[&_.fc-timegrid-slot-label-cushion]:tabular-nums [&_.fc-timegrid-slot-label-cushion]:text-muted-foreground',
  //  Nhãn giờ nằm ĐÈ LÊN ĐƯỜNG KẺ của chính giờ đó (Google Calendar), không nằm
  //  giữa hai đường. Nằm giữa thì mắt phải đoán con số đang nói mốc trên hay
  //  mốc dưới — mà chuyến xe là một MỐC giờ, không phải một dải.
  //
  //  `align-top` + kéo ngược nửa thân chữ là CHƯA ĐỦ, và sai lặng lẽ: khối bọc
  //  nhãn kế thừa `line-height: 24px` / `font-size: 16px` của bảng, nên con chữ
  //  11px nằm lọt trong một dòng cao 24px và đã bị đẩy sẵn ~5.5px xuống TRƯỚC
  //  khi kéo — kéo nửa thân chữ xong vẫn thấp hơn đường kẻ đúng 6px. Bẻ khối bọc
  //  thành `flex` + `items-start` để bỏ khoảng đệm dòng đó; đo lại còn lệch 0px.
  //  Vẫn để nhãn là `inline-block` (không đổi sang `block`) vì FC đo bề rộng cột
  //  trục từ bề rộng TỰ NHIÊN của chính phần tử này.
  '[&_.fc-timegrid-slot-label]:!align-top',
  '[&_.fc-timegrid-slot-label-frame]:!flex [&_.fc-timegrid-slot-label-frame]:!items-start',
  '[&_.fc-timegrid-slot-label-frame]:!justify-end',
  '[&_.fc-timegrid-slot-label-cushion]:inline-block [&_.fc-timegrid-slot-label-cushion]:-translate-y-1/2',
  //  …trừ nhãn ĐẦU TIÊN: đường kẻ của nó chính là mép trên lưới, kéo lên nửa thân
  //  chữ là nửa trên bị khung cuộn xén mất. Ẩn đi, đúng như Google Calendar (giờ
  //  đầu dải của họ cũng không có nhãn). Dùng `invisible` chứ không `hidden`:
  //  phần tử phải còn chiếm chỗ để FC đo bề rộng cột trục.
  '[&_.fc-timegrid-slots_tr:first-child_.fc-timegrid-slot-label-cushion]:invisible',
  //  Cột trục giờ KHÔNG kẻ vạch nào — dọc thì trục trông như một cột dữ liệu,
  //  ngang thì đường kẻ chạy qua dưới chân con số và mắt đọc ra hai thứ rời nhau
  //  ("giờ" ở trên, "một đường" ở dưới) thay vì "đường kẻ NÀY là giờ đó".
  //  Google Calendar cũng chỉ bắt đầu kẻ từ mép lưới trở đi.
  '[&_.fc-timegrid-slot-label]:!border-0 [&_.fc-timegrid-axis]:!border-r-0',
  //  Chữ "Cả ngày" ẨN KHỎI MẮT nhưng GIỮ trong DOM (`sr-only`) — Google Calendar
  //  không dán nhãn cho dải này, người dùng nhận ra nó qua chính mấy thanh chuyến
  //  dài ngày nằm đó.
  //  Giữ lại cho trình đọc màn hình vì với họ dải này KHÔNG có dấu hiệu nào khác:
  //  không nhìn thấy thanh nào trải ngang thì "cả ngày" là manh mối duy nhất.
  '[&_.fc-timegrid-axis-cushion]:sr-only',
  //  Dải "Cả ngày" ẨN HẲN khi tầm nhìn không có chuyến dài ngày nào — Google
  //  Calendar làm đúng vậy. Trước 16/09/2026 nó luôn chiếm một dải trắng 26px
  //  trống trơn ngay dưới hàng tiêu đề, và dải đó ăn mất chỗ của lưới giờ.
  //
  //  Điều kiện tính bằng CSS (`:has`) chứ không bằng prop `allDaySlot`: gác bằng
  //  prop thì lúc dữ liệu chưa về `allDaySlot=false` và FC VỨT LUÔN các chuyến
  //  dài ngày khi chúng tới, còn ở đây hàng vẫn dựng đủ, chỉ không hiện.
  //  `tr:has(.fc-daygrid-body)` = hàng cả-ngày; KHÔNG dùng `tbody > tr:first-child`
  //  vì các hàng của bảng khung giờ cũng khớp, và hàng 04:00 biến mất theo.
  //
  //  Mốc "rỗng" là KHÔNG CÓ `.fc-event` nào. Không lấy "ô ngày không có phần tử
  //  con" làm mốc: FC dựng sẵn `.fc-daygrid-day-events` + `.fc-daygrid-day-bottom`
  //  cho mọi ô kể cả khi rỗng, nên điều kiện đó không bao giờ đúng (đã đo).
  '[&_.fc-timegrid_tr:has(.fc-daygrid-body):not(:has(.fc-event))]:hidden',
  //  Khi CÓ chuyến dài ngày thì dải hiện lại: FC ghim `min-height: 2em` +
  //  `margin-bottom: 1em` cho khối chứa chip, kéo về 26px cho khít một chip.
  //  Đây là min, không phải max — nhiều chuyến thì nó tự cao lên.
  //
  //  Bắt buộc có `!`: FC v6 tự nhồi CSS của nó vào <head> LÚC CHẠY, tức là sau
  //  Tailwind, nên cùng độ ưu tiên (0,2,0) thì FC thắng vì đứng sau.
  '[&_.fc-timegrid_.fc-daygrid-day-events]:!mt-0 [&_.fc-timegrid_.fc-daygrid-day-events]:!mb-0',
  '[&_.fc-timegrid_.fc-daygrid-day-events]:!min-h-[26px]',
  '[&_.fc-timegrid-axis-frame]:min-h-[26px]',
  //  Dải ngăn giữa hàng cả-ngày và trục giờ: FC vẽ một THANH XÁM dày 3px, đậm hơn
  //  mọi đường lưới khác nên mắt đọc ra như thanh cuộn. XÓA HẲN, không thay bằng
  //  kẻ 1px: hàng giờ đầu tiên ngay dưới nó đã có viền trên của chính nó, nên kẻ
  //  thêm ở đây là hai đường sát nhau.
  '[&_.fc-timegrid-divider]:!bg-transparent [&_.fc-timegrid-divider]:!p-0',
  '[&_.fc-timegrid-divider]:!border-0',
  //  Ô ngày ĐẦU TIÊN của dải "Cả ngày" bỏ viền trái — cùng lý do cột trục giờ
  //  không kẻ vạch dọc: có vạch thì trục đọc ra như một cột dữ liệu. `:first-of-type`
  //  KHÔNG dùng được vì ô trục cũng là `<td>`, nó mới là ô đầu cùng loại.
  '[&_.fc-timegrid-axis+.fc-daygrid-day]:!border-l-0',
  //  --- Vạch "bây giờ" ---
  //  Vạch dày 2px cho thấy rõ trên nền lưới nhạt, đầu trái có CHẤM TRÒN như
  //  Google Calendar.
  '[&_.fc-timegrid-now-indicator-line]:!border-t-2',
  //  Chấm là `::before` CỦA CHÍNH VẠCH, không dùng mũi tên riêng của FC. FC luôn
  //  đặt mũi tên ở cột TRỤC GIỜ, trong khi vạch nằm trong cột HÔM NAY — ở khám
  //  Tuần hai thứ cách nhau nửa màn hình, đọc ra một chấm đỏ lạc lõng chứ không
  //  ra "bây giờ". Gắn vào vạch thì chấm luôn dính đầu vạch, khám nào cũng đúng.
  //  (Bản trước né bằng cách ẩn chấm ở khám Tuần — mất luôn dấu hiệu.)
  '[&_.fc-timegrid-now-indicator-arrow]:!hidden',
  "[&_.fc-timegrid-now-indicator-line]:before:content-['']",
  '[&_.fc-timegrid-now-indicator-line]:before:absolute',
  //  Khối bọc vạch của FC ghim `overflow:hidden` và mép trái của nó TRÙNG mép
  //  cột, nên chấm lùi ra ngoài bị XÉN MẤT NỬA TRÁI — ở mọi khám, không riêng
  //  cột đầu. Mở khóa đúng khối đó; nó chỉ chứa vạch (`left:0;right:0`, không
  //  tràn) với mũi tên đã ẩn, nên không có gì khác lọt ra.
  '[&_.fc-timegrid-now-indicator-container]:!overflow-visible',
  //  Chấm 10px, lùi trái 5px cho tâm chấm trùng đầu vạch.
  //
  //  Dọc thì `-6px` chứ KHÔNG phải `-5px` như phép tính "nửa chấm": vạch là một
  //  `border-top: 2px`, mà `top` của con định vị tuyệt đối đo từ PADDING BOX —
  //  tức từ mép DƯỚI của đường viền đó. Nên mốc 0 đã tụt sẵn 2px so với dải màu
  //  mắt nhìn thấy; lùi 5px chỉ đưa tâm chấm xuống dưới tâm vạch đúng 2px.
  '[&_.fc-timegrid-now-indicator-line]:before:-left-[5px]',
  '[&_.fc-timegrid-now-indicator-line]:before:-top-[6px]',
  '[&_.fc-timegrid-now-indicator-line]:before:size-[10px]',
  '[&_.fc-timegrid-now-indicator-line]:before:rounded-full',
  '[&_.fc-timegrid-now-indicator-line]:before:bg-[var(--fc-now-indicator-color)]',
  //  Khối chuyến chừa 2px hai bên cho khỏi dính viền cột (chip tự lo phần còn lại).
  '[&_.fc-timegrid-event-harness]:mx-[2px]',
  //  Khám NGÀY: tiêu đề dạt TRÁI, ngay đầu cột — Google Calendar để vậy vì chỉ
  //  có một cột, căn giữa thì khối chữ trôi ra giữa màn hình, cách xa trục giờ
  //  mà nó đang nói về. Khám TUẦN vẫn căn giữa: 7 cột thì mỗi tiêu đề phải nằm
  //  giữa cột của nó.
  '[&_.fc-timeGridDay-view_.fc-col-header-cell_.fc-scrollgrid-sync-inner]:text-left',
  '[&_.fc-timeGridDay-view_.fc-col-header-cell-cushion]:!pl-2',

  //  --- Dấu + gợi ý tạo phiếu (phần tử do `dayCellDidMount` chèn) ---
  '[&_.fc-daygrid-day-frame]:cursor-pointer',
  '[&_[data-create-hint]]:pointer-events-none [&_[data-create-hint]]:absolute',
  '[&_[data-create-hint]]:bottom-1 [&_[data-create-hint]]:left-1/2',
  '[&_[data-create-hint]]:-translate-x-1/2 [&_[data-create-hint]]:grid',
  '[&_[data-create-hint]]:size-5 [&_[data-create-hint]]:place-items-center',
  '[&_[data-create-hint]]:rounded-full [&_[data-create-hint]]:bg-muted',
  '[&_[data-create-hint]]:text-sm [&_[data-create-hint]]:leading-none',
  '[&_[data-create-hint]]:text-muted-foreground',
  '[&_[data-create-hint]]:opacity-0 [&_[data-create-hint]]:transition-opacity',
  //  Sáng lên khi trỏ vào ô…
  '[&_.fc-daygrid-day-frame:hover_[data-create-hint]]:opacity-100',
  //  …nhưng TẮT khi đang trỏ vào một chip: bấm chip là mở chi tiết chuyến, không
  //  phải tạo phiếu — để dấu + sáng lúc đó là hứa sai việc sắp xảy ra.
  '[&_.fc-daygrid-day-frame:has(.fc-daygrid-event-harness:hover)_[data-create-hint]]:opacity-0',
  '[&_.fc-daygrid-day-frame:has(.fc-daygrid-event-harness:hover)]:cursor-default',
)
