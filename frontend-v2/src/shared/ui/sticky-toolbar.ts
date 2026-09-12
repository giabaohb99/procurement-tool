/**
 * Dải THANH CÔNG CỤ ghim đầu danh sách ở khổ điện thoại — cho những màn nằm
 * trong một `Card` có đệm `p-4`.
 *
 * ⚠️ **Đừng chép chuỗi này sang màn mới, hãy import.** Ba luật bên dưới đều là
 * lỗi đã trả giá rồi (ghi chú gốc ở `hr/utils/list-sticky.ts`, nơi giữ hệ mốc
 * `top` cộng dồn của mấy màn ba tab bên Nhân sự — hằng ở đây tách riêng vì
 * chúng bám đệm `p-4` của `Card`, không phải `p-3`):
 *
 * - **Nền ĐỤC + lề âm/đệm bù** (`-mx-4 px-4`) để phủ hết bề ngang. Nền trong
 *   suốt thì chữ của thẻ hiện xuyên qua chữ của ô tìm; thiếu lề âm thì hai mép
 *   trái/phải chừa hai khe cho nội dung trôi qua.
 * - **Khoảng hở dưới dải là ĐỆM, không phải LỀ** (`mb-0` + `pb-3`). Lề nằm
 *   NGOÀI vùng được tô nền, nên thẻ cuộn qua hiện nguyên một vạch chữ cụt
 *   trong khe đó — trông đúng như lỗi vẽ.
 * - **Bóng đổ + vạch chân CHỈ vẽ khi đã cuộn** (`group-data-[scrolled]`). Đổ
 *   sẵn từ lúc chưa cuộn thì dải nổi lên giữa một trang đứng yên: bóng là câu
 *   nói *"có nội dung đang trôi bên dưới"*, nói lúc chưa có gì trôi là nói sai.
 *
 * ⚠️ Bóng đòi tổ tiên mang `group` + `data-scrolled` (xem `useScrolled`). Thiếu
 * thì dải vẫn ghim, chỉ là không bao giờ đổ bóng — và lỗi đó im lặng.
 *
 * ⚠️ **CHỈ dải DƯỚI CÙNG được đổ bóng.** Màn nào ghim thêm một dải nữa Ở TRÊN
 * dải này thì dải trên phải bỏ bóng: nó nằm ở lớp cao hơn nên bóng sẽ vẽ ĐÈ lên
 * mặt thanh công cụ, ra một vệt xám ngang giữa hai dải chứ không ra chiều sâu.
 */
export const STICKY_TOOLBAR_BASE =
  'max-md:sticky max-md:z-20 max-md:-mx-4 max-md:-mt-4 max-md:mb-0 max-md:border-b max-md:border-transparent max-md:bg-card max-md:px-4 max-md:pt-4 max-md:pb-3 max-md:transition-[box-shadow,border-color] max-md:duration-200 max-md:group-data-[scrolled]:border-border max-md:group-data-[scrolled]:shadow-[0_6px_12px_-8px_rgb(0_0_0/0.35)]'

/**
 * Thanh công cụ ghim SÁT ĐỈNH khung cuộn — dùng ở màn không có dải nào ghim
 * phía trên (tiêu đề trang và nút *Thêm…* cuộn đi bên trên nó).
 */
export const STICKY_TOOLBAR_TOP = `${STICKY_TOOLBAR_BASE} max-md:top-0`
