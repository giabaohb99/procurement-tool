# -*- coding: utf-8 -*-
"""Seed Trung tâm trợ giúp cho phân hệ NHÂN SỰ — hai tính năng ra ngày 22/10/2026 (duoc-CR-670).

CHỈ viết bài cho tính năng MỚI: Sơ đồ tổ chức (CR-669) và hộp «kiểm việc đang giữ» trước khi khóa tài khoản /
cho nghỉ việc (CR-665). KHÔNG viết lại toàn bộ phân hệ hồ sơ nhân sự. Dựng 1 thẻ phân hệ + 2 bài. (Nghỉ phép đã có
bộ riêng: `seed_help_nghi_phep.py`.)

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_nhan_su.py
    docker compose exec -T api python scripts/reindex_help_rag.py     # nạp vào kho tìm kiếm của trợ lý

Idempotent: xóa nguyên cây cùng tiêu đề gốc rồi dựng lại ở đúng vị trí cũ (xem `help_seed_common.py`).

⚠️ Phải KHỚP với cẩm nang trợ lý `app/modules/ai_skill/seed_handbook/60-nhan-su-ho-so.md` (đẩy lên hệ đang chạy
bằng `scripts/publish_handbook_update.py`) và `doc/erp/hrm/01-ho-so-nhan-su.md`.
"""
from help_seed_common import rebuild_tree, ref

SO_DO = "Nhân sự — Xem Sơ đồ tổ chức"
KHOA = "Nhân sự — Khóa tài khoản hoặc cho nghỉ việc khi còn việc duyệt treo"

TREE = {
    "title": "Hướng dẫn sử dụng Nhân sự — Hồ sơ và tổ chức",
    "icon": "users",
    "summary": "Sơ đồ tổ chức tự vẽ từ dữ liệu; kiểm và chuyển việc duyệt đang treo trước khi khóa tài khoản hay cho nghỉ việc",
    "content": f"""<h2>Nhân sự — Hồ sơ và tổ chức</h2>
<p>Phân hệ <strong>Nhân sự</strong> giữ hồ sơ nhân viên, phòng ban, chức vụ và (ở bộ hướng dẫn riêng) nghỉ phép. Bộ hướng dẫn này hiện chỉ gom hai tính năng <strong>mới</strong>:</p>
<ul>
<li>Muốn xem ai thuộc phòng nào, ai quản lý ai: {ref(SO_DO, "Xem Sơ đồ tổ chức")}.</li>
<li>Sắp khóa tài khoản hay cho một người nghỉ việc mà người đó còn phiếu cần duyệt: {ref(KHOA, "Khóa tài khoản hoặc cho nghỉ việc khi còn việc duyệt treo")}.</li>
</ul>
<p>Nghỉ phép có bộ hướng dẫn riêng ở thẻ <strong>Hướng dẫn sử dụng Nghỉ phép</strong>.</p>""",
    "children": [
        {
            "title": SO_DO,
            "icon": "building",
            "summary": "Menu Nhân sự > Danh mục > Sơ đồ tổ chức: cây pháp nhân, phòng ban, người; chỉ hiện người trong phạm vi bạn được xem",
            "content": f"""<h2>Sơ đồ tổ chức</h2>
<p>Vào <strong>Nhân sự ▸ Danh mục ▸ Sơ đồ tổ chức</strong>. Màn này <strong>không phải bản vẽ nhập tay</strong>: mỗi lần mở, hệ thống tự dựng từ dữ liệu phòng ban, trưởng phòng và ô <strong>«Người quản lý trực tiếp»</strong> trên hồ sơ. Đổi phòng cho một người hay đổi người quản lý xong, sơ đồ tự đúng ở lần mở sau — không có gì phải vẽ lại.</p>

<h2>Đọc sơ đồ</h2>
<ul>
<li>Cấp trên cùng là <strong>pháp nhân</strong> (tên công ty, kèm tổng số người). Người chưa gán pháp nhân nằm trong nhóm <em>«Chưa gán pháp nhân»</em>.</li>
<li>Dưới pháp nhân là các <strong>phòng ban</strong>, phòng con thụt vào dưới phòng cha. Mỗi phòng là một thẻ: tên phòng, <strong>Trưởng phòng: …</strong> và số người ở góc phải (đã gồm cả các phòng con).</li>
<li>Bấm vào thẻ phòng để <strong>mở hoặc thu gọn</strong>. Hai tầng đầu mở sẵn, các tầng sâu hơn thu lại cho gọn.</li>
<li>Bên trong phòng là <strong>cây quản lý trực tiếp</strong>: cấp dưới thụt vào dưới người quản lý của họ (cùng phòng). Mỗi người hiện tên, nhãn <strong>«Trưởng phòng»</strong> nếu là trưởng phòng, chức vụ và mã nhân sự.</li>
<li>Bấm vào <strong>tên một người</strong> để mở hồ sơ của họ.</li>
</ul>

<h2>Ai xem được, thấy những gì</h2>
<ul>
<li>Cần quyền <strong>xem hồ sơ nhân sự</strong>. Không có thì màn báo <em>«Không có quyền xem sơ đồ tổ chức»</em>; liên hệ quản trị để được cấp.</li>
<li>⚠️ Sơ đồ <strong>chỉ hiện những người trong phạm vi dữ liệu của bạn</strong> (xem cùng một sơ đồ, người thấy nhiều người thấy ít là bình thường). Một trưởng phòng hay quản lý <em>nằm ngoài phạm vi</em> của bạn thì tên họ <strong>không hiện</strong>, kể cả khi họ là cấp trên của người bạn xem được. Tên phòng ban thì vẫn hiện để cây liền mạch, nhưng không lộ người.</li>
<li>Người đã <strong>nghỉ việc</strong> hoặc đã ngưng hoạt động thì không có trên sơ đồ.</li>
<li>Con số «N người» cũng chỉ đếm người bạn được thấy, nên đừng dùng nó làm quân số chính thức của phòng.</li>
</ul>

<h2>Thấy sơ đồ sai thì sửa ở đâu</h2>
<table>
<thead><tr><th>Sơ đồ đang sai</th><th>Sửa ở</th></tr></thead>
<tbody>
<tr><td>Người nằm nhầm phòng</td><td>Hồ sơ nhân sự ▸ ô <strong>Phòng ban</strong></td></tr>
<tr><td>Người báo cáo nhầm sếp</td><td>Hồ sơ nhân sự ▸ ô <strong>Người quản lý trực tiếp</strong></td></tr>
<tr><td>Sai trưởng phòng</td><td>Nhân sự ▸ Danh mục ▸ <strong>Phòng ban</strong> ▸ chọn lại trưởng phòng</td></tr>
<tr><td>Phòng con nằm nhầm phòng cha</td><td>Nhân sự ▸ Danh mục ▸ <strong>Phòng ban</strong> ▸ ô phòng cha</td></tr>
<tr><td>Màn trống</td><td>Chưa có phòng ban hay nhân sự nào trong phạm vi của bạn — màn ghi đúng câu này</td></tr>
</tbody>
</table>
<p>Hệ chặn người dùng gán vòng lặp (A quản lý B, B quản lý A) ngay lúc lưu hồ sơ; nếu dữ liệu cũ vẫn còn vòng lặp thì sơ đồ vẫn hiển thị được, không bị treo.</p>
<p>Liên quan: {ref(KHOA, "Khóa tài khoản hoặc cho nghỉ việc khi còn việc duyệt treo")}.</p>""",
        },
        {
            "title": KHOA,
            "icon": "key-round",
            "summary": "Hộp «việc đang giữ» hiện trước khi khóa tài khoản hoặc lưu hồ sơ nghỉ việc; chuyển từng việc hoặc chuyển hết; ai được chuyển",
            "content": f"""<h2>Khóa tài khoản hoặc cho nghỉ việc khi còn việc duyệt treo</h2>
<p>Khóa tài khoản hay cho nghỉ việc mà người đó còn phiếu đang chờ họ duyệt thì <strong>phiếu sẽ kẹt</strong>: không ai khác thấy việc đó để làm. Từ ngày 22/10/2026, trước khi khóa hệ thống luôn mở hộp <strong>kiểm các việc người đó đang giữ</strong> để bạn chuyển đi trước.</p>

<h2>Hộp này hiện khi nào</h2>
<table>
<thead><tr><th>Bạn làm</th><th>Tên hộp</th></tr></thead>
<tbody>
<tr><td>Lưu hồ sơ nhân sự và đổi trạng thái sang <strong>nghỉ việc</strong> (hoặc bỏ tick đang hoạt động)</td><td><em>«Lưu hồ sơ nghỉ việc?»</em> — nút xác nhận <strong>«Lưu và chuyển nghỉ việc»</strong></td></tr>
<tr><td>Hồ sơ nhân sự ▸ tab <strong>«Tài khoản»</strong> ▸ bấm <strong>«Khóa tài khoản + đăng xuất mọi thiết bị»</strong></td><td><em>«Khóa tài khoản»</em></td></tr>
<tr><td>Quản trị ▸ Phân quyền tài khoản ▸ tab <strong>«Người dùng»</strong> ▸ biểu tượng ổ khóa <strong>«Khóa tài khoản»</strong> ở dòng người đó</td><td><em>«Khóa tài khoản …?»</em></td></tr>
<tr><td>Hồ sơ nhân sự ▸ tab <strong>«Quá trình công tác»</strong> ▸ thêm hoặc áp dòng <strong>«Thôi việc»</strong> vào hồ sơ</td><td><em>«Chuyển hồ sơ sang nghỉ việc?»</em></td></tr>
</tbody>
</table>
<p>Tài khoản chưa gắn với hồ sơ nhân sự nào thì không có việc duyệt để kiểm, nên bước này bị bỏ qua.</p>

<h2>Trong hộp có gì</h2>
<ul>
<li><strong>Việc duyệt đang chờ người này</strong>: mỗi dòng là một phiếu (loại phiếu, số phiếu, tiêu đề), bước đang chờ, người trình, <em>hạn</em> và nhãn <em>(quá hạn)</em> nếu đã quá. Bấm vào số phiếu để mở phiếu ở thẻ mới. Phiếu mà <em>bạn</em> không có quyền xem thì chỉ hiện <em>«(bạn không có quyền xem phiếu này)»</em>, không lộ số hay tên phiếu.</li>
<li><strong>Bước trong luồng duyệt chỉ đích danh người này</strong>: phiếu <em>mới</em> sau này sẽ lùi sang người dự phòng hoặc kẹt. Mỗi dòng dẫn tới luồng duyệt để bạn đổi người ở đó (hộp chỉ nêu, không sửa luồng tại chỗ).</li>
<li>Không còn việc nào thì hộp ghi <em>«Người này không còn việc duyệt nào đang treo.»</em></li>
</ul>

<h2>Chuyển việc cho người khác</h2>
<ol>
<li>Ở ô <strong>«Chuyển cho…»</strong>, tìm theo tên hoặc mã rồi chọn người nhận.</li>
<li>Bấm <strong>«Chuyển»</strong> ở từng dòng để chuyển <strong>riêng việc đó</strong>, hoặc <strong>«Chuyển hết (N)»</strong> để chuyển <strong>mọi việc</strong> đang chờ (kể cả những việc hộp chưa liệt kê hết vì quá dài).</li>
<li>Danh sách tự làm mới sau mỗi lần chuyển. Chuyển hết thì dòng cảnh báo biến mất.</li>
</ol>
<p>⚠️ <strong>Chỉ người có quyền ghi «Luồng duyệt»</strong> (thường là quản trị luồng duyệt) mới chuyển được. Nếu bạn không có quyền này, hộp vẫn liệt kê việc nhưng ghi <em>«Bạn không có quyền chuyển việc duyệt … — nhờ quản trị luồng chuyển giúp trước khi khóa.»</em> Hãy nhờ họ chuyển rồi quay lại khóa.</p>

<h2>Còn việc treo mà vẫn muốn khóa</h2>
<p>Hệ <strong>không chặn cứng</strong>, vì có người nghỉ đột xuất cần khóa ngay. Khi còn việc treo, nút xác nhận đổi chữ thành <strong>«Vẫn khóa … (còn việc treo)»</strong> để bạn biết mình đang để phiếu kẹt. Bấm xác nhận thì tài khoản vẫn bị khóa và người đó bị đăng xuất khỏi mọi thiết bị như thường; việc treo phải xử lý sau bằng cách nhờ quản trị luồng duyệt chuyển.</p>
<p>Nếu hộp ghi <em>«Không xem được danh sách việc đang giữ (thiếu quyền hoặc lỗi)»</em> thì bạn chưa đọc được danh sách; hãy tự kiểm ở màn Báo cáo duyệt trước khi khóa.</p>
<p>Xem thêm: {ref(SO_DO, "Xem Sơ đồ tổ chức")}.</p>""",
        },
    ],
}

if __name__ == "__main__":
    rebuild_tree(TREE)
