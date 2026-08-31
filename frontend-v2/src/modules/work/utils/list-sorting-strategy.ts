/**
 * Chiến lược sắp xếp RỖNG cho hàng VIỆC CHA của khung nhìn Danh sách — các dòng
 * ĐỨNG YÊN trong lúc kéo, không dạt ra để chừa khe.
 *
 * ⚠️ Chỉ còn dùng cho hàng việc cha. Cụm VIỆC CON và hàng CỘT đã chuyển sang
 * `verticalListSortingStrategy` thật (xem `task-list-group.tsx` và
 * `task-list-view.tsx`): cả hai đều là hàng NGẮN — vài việc con trong một cụm,
 * dăm cột trong một dự án — nên số phần tử phải chạy hiệu ứng luôn nhỏ.
 *
 * `verticalListSortingStrategy` của dnd-kit dịch từng dòng dưới con trỏ xuống
 * một nấc để mở khe. Trên bảng này mỗi dòng cao 45px và chứa cả ô chọn, ô ngày
 * lẫn chip nhãn, nên mỗi lần đổi đích là một loạt dòng nặng cùng chạy hiệu ứng
 * — giật thấy rõ.
 *
 * Thay bằng đúng lối của Lark: chỗ sắp rơi vào được nói bằng một VỆT SÁNG trên
 * chính dòng đích (`isOver` ở `TaskListRow`, `sectionIsOver` ở `TaskListGroup`).
 * Không có gì chuyển động ngoài tấm thẻ bám con trỏ.
 *
 * ⚠️ Để ở tệp riêng chứ không nằm cạnh component dùng nó: `react-refresh` bắt
 * lỗi mọi tệp `.tsx` xuất ra thứ không phải component.
 */
export const noDisplacement = () => null
