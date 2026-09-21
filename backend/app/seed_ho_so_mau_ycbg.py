"""NẠP 15 HỒ SƠ MẪU vào kho Hồ sơ — dữ liệu để THỬ thay «Báo cáo thực hiện».

    docker compose exec api python -m app.seed_ho_so_mau_ycbg
    docker compose exec api python -m app.seed_ho_so_mau_ycbg --ghi-de
    docker compose exec api python -m app.seed_ho_so_mau_ycbg --ghi-de --ycbg 2931

⚠️ **Chạy TAY, cố ý không nằm trong `app/seed.py`** — cùng nếp với
`app.seed_nghi_phep`. Đây là dữ liệu của một cuộc thử nghiệm kiến trúc
(21/09/2026), chưa phải nghiệp vụ đã chốt; nhét vào seed chung là mỗi lần deploy
lại đẻ 15 tờ hồ sơ vào kho thật của khách.

⚠️ **Mặc định chỉ THÊM, chạy lại được.** Khớp theo cặp (tên · loại): tờ nào đã
có thì bỏ qua, không ghi đè — người thử có thể đã sửa tay nội dung trên giao
diện. Cờ `--ghi-de` mới áp lại kịch bản lên 15 tờ đã có.

⚠️ **`--ycbg <id>` ghi ĐÚNG kịch bản đó sang khối *Báo cáo thực hiện* của phiếu
YCBG.** Đây là cái để ĐỐI CHIẾU: hai khối nằm cạnh nhau trên cùng một trang,
cùng 15 đầu việc, cùng trạng thái, cùng mốc ngày — khác nhau chỗ nào thì đúng
chỗ đó là khác biệt THẬT giữa hai lối dựng, chứ không phải vì hai bên đang cầm
hai bộ số liệu khác nhau. Khớp theo TÊN đầu việc; đầu việc nào không có trong
bảng dưới thì để nguyên, không đụng vào.

Bối cảnh: 15 đầu việc này chép từ **bộ hồ sơ chung của báo cáo mẫu**
(`report_service` — 5 giai đoạn nhập khẩu). Chúng được gán vào đúng **Loại hồ
sơ** trùng tên giai đoạn (`PLGP` · `DHHD` · `SXVC` · `KTTQ` · `NHVK` — danh mục
đã seed sẵn đúng 5 loại này), và khai **điều kiện áp dụng = mọi Yêu cầu báo
giá**, tức bỏ trống `apply_conditions`: đây là bộ hồ sơ CHUNG, không lọc theo
mặt hàng nào. Xem `app/modules/dossier/applicability.py`.

⚠️ **Hai cột không đối chiếu được, và đó là KẾT QUẢ của cuộc thử, không phải
việc còn dở:** cờ *Bắt buộc* và *hồ sơ tiên quyết* chỉ có bên Báo cáo thực hiện;
kho Hồ sơ không có chỗ nào lưu hai thứ đó. Trạng thái cũng lệch thang — báo cáo
bốn mức (chưa bắt đầu · đang làm · chờ duyệt · hoàn thành), kho hồ sơ hai mức
(nháp · đang lưu) — nên script gộp «hoàn thành» ↔ «đang lưu», phần còn lại về
«nháp». Đừng nắn cho bằng nhau, lệch chỗ nào cứ để lệch chỗ đó.
"""
import argparse
from datetime import date, timedelta
#  ⚠️ Nạp `all_models` TRƯỚC mọi thứ khác. `Dossier` khai quan hệ chỉ-đọc tới
#  `Employee` / `Department` / `Company` bằng CHUỖI tên lớp, nên SQLAlchemy chỉ
#  dựng được mapper khi ba lớp kia đã nằm trong registry. Thiếu dòng này thì
#  script nổ `name 'Employee' is not defined` ngay ở truy vấn đầu tiên — lỗi
#  trông như sai mô hình chứ không chỉ về phía thứ tự nhập.
import app.core.all_models  # noqa: F401
from app.core.database import SessionLocal
from app.modules.dossier.constants import (DOSSIER_ACTIVE, DOSSIER_DRAFT,
                                           DP_DONE, DP_IDLE)
from app.modules.dossier.model import Dossier
from app.modules.dossier.progress_service import upsert as upsert_progress
from app.modules.dossier.type_model import DossierType
from app.modules.survey_request.report_constants import RD_DONE, RD_IDLE
from app.modules.survey_request.report_model import SurveyReportDoc


class DongMau:
    """MỘT đầu việc của kịch bản — nguồn chung cho cả hai khối.

    `ngay_cap` / `het_han` là SỐ NGÀY lệch so với hôm nay, không phải ngày cố
    định: ghim ngày tuyệt đối thì vài tuần nữa mọi mốc đều thành quá khứ và
    kịch bản mất sạch ý nghĩa (không còn tờ nào «sắp hết hạn» để xem màu vàng).
    `None` = bỏ trống, tức tờ vô thời hạn / chưa có ngày cấp.
    """

    def __init__(
        self,
        loai: str,
        ten: str,
        mo_ta: str,
        xong: bool,
        ngay_cap: int | None = None,
        het_han: int | None = None,
        du_dinh: int | None = None,
        truoc: tuple[str, ...] = (),
    ) -> None:
        self.loai = loai
        self.ten = ten
        self.mo_ta = mo_ta
        self.xong = xong
        self.ngay_cap = ngay_cap
        self.het_han = het_han
        #  CHỈ khối Báo cáo thực hiện có mốc «dự định hoàn tất»; kho Hồ sơ không
        #  có cột nào tương ứng. Vẫn gán để ô tổng thứ tư của bản gốc có số mà
        #  xem, chứ không phải để đối chiếu — bên kia ô đó là số dòng hàng.
        self.du_dinh = du_dinh
        #  TIÊN QUYẾT khai bằng TÊN, không bằng số thứ tự như `DEFAULT_TEMPLATE_DOCS`
        #  của bản gốc: chèn thêm một dòng vào giữa bảng là mọi số phía sau lệch
        #  một nấc, im lặng, và chuỗi tiên quyết trỏ sai chỗ.
        #
        #  ⚠️ Tờ ĐÃ XONG không được chờ một tờ CHƯA xong — backend chặn ca đó ở
        #  đường API, nhưng script ghi thẳng vào bảng nên không ai chặn hộ. Khai
        #  lệch thì ra dữ liệu mà chính giao diện không bao giờ tạo được.
        self.truoc = truoc

    def ngay(self, lech: int | None) -> date | None:
        return None if lech is None else date.today() + timedelta(days=lech)


#  ⚠️ **Trạng thái và mốc ngày cố ý HỖN HỢP, không phải cho vui.** Seed tất cả ở
#  mức «Đang lưu» thì thẻ hiện 15/15 · 100%, mọi dòng gạch ngang, tiến trình
#  xanh hết — nhìn thì đẹp nhưng KHÔNG đánh giá được gì: không thấy thanh tiến
#  độ chạy, không thấy điểm «đang ở đây» nhấp nháy, không thấy viên ngày đổi
#  màu, tức đúng mấy thứ cuộc thử cần soi. Kịch bản dưới đây dựng một thương vụ
#  đang dở ở giai đoạn 2, với đủ BA mức khẩn của hạn hiệu lực:
#    · −3 ngày  → quá hạn      (đỏ ở cả hai khối)
#    · +5 ngày  → sắp hết hạn  (vàng ở cả hai: báo cáo cảnh báo ≤7 ngày, kho hồ sơ ≤30)
#    · +60 trở lên → còn xa    (xám)
#
#  ⚠️ Ngưỡng cảnh báo của hai bên KHÁC NHAU (7 ngày và 30 ngày) nên một mốc rơi
#  vào khoảng giữa — ví dụ +20 — sẽ ra vàng bên kho hồ sơ mà xám bên báo cáo.
#  Đó là khác biệt thật, không phải lỗi; tránh mốc như vậy trong bảng này để lúc
#  đối chiếu không phải giải thích một thứ chẳng liên quan tới bố cục.
#
#  ⚠️ **HAI MỐC KHẨN PHẢI NẰM Ở ĐẦU VIỆC CHƯA XONG.** Ô tổng «Hết hiệu lực gần
#  nhất» của Báo cáo thực hiện CỐ Ý bỏ qua đầu việc đã Hoàn thành (`nearestExpiry`
#  trong `survey-report-helpers.ts`) — xong rồi thì hạn không còn là lời cảnh
#  báo. Kho Hồ sơ thì ngược lại, tính cả tờ đã có giấy, vì ở đó hạn là hạn của
#  chính TỜ GIẤY: giấy đã nộp mà sắp hết hiệu lực đúng là thứ phải kêu lên.
#  Khác biệt ngữ nghĩa thật, không nắn. Nhưng nếu dồn hết mốc khẩn vào mấy tờ đã
#  xong thì ô của Báo cáo ra gạch ngang còn ô của Hồ sơ ra ngày đỏ, và lúc đối
#  chiếu nó đọc ra như một bên tính sai. Nên: tờ ĐÃ XONG nhận hạn XA, hai mốc
#  khẩn (−3 và +5) đặt vào tờ CHƯA XONG — khi đó hai ô ra đúng cùng một ngày.
MAU: list[DongMau] = [
    DongMau("PLGP", "Giấy đăng ký kinh doanh của NCC",
            "Bản sao còn hiệu lực, đối chiếu ngành nghề với mặt hàng cung cấp.",
            True, ngay_cap=-400, het_han=240),
    DongMau("PLGP", "Hồ sơ năng lực của NCC",
            "Khách hàng tham chiếu, công suất, chứng nhận chất lượng (ISO...).",
            True, ngay_cap=-300, het_han=365),
    DongMau("PLGP", "Giấy phép / chứng nhận của sản phẩm",
            "Giấy phép lưu hành, kiểm định, COA... nếu mặt hàng thuộc diện quản lý.",
            True, ngay_cap=-200, het_han=180),
    DongMau("DHHD", "Báo giá chính thức có ký, đóng dấu",
            "Ghi rõ đơn giá, VAT, điều kiện giao hàng và thời hạn hiệu lực.",
            True, ngay_cap=-20, het_han=60),
    DongMau("DHHD", "Hợp đồng mua bán / hợp đồng nguyên tắc",
            "Điều khoản thanh toán, phạt chậm giao, bảo hành.",
            True, ngay_cap=-14, het_han=400,
            truoc=("Báo giá chính thức có ký, đóng dấu",)),
    #  QUÁ HẠN 3 ngày — mốc đỏ của cả hai khối.
    DongMau("DHHD", "Đơn mua hàng (PO) phát hành",
            "Phát hành sau khi hợp đồng ký xong.",
            False, ngay_cap=-7, het_han=-3, du_dinh=-5,
            truoc=("Hợp đồng mua bán / hợp đồng nguyên tắc",)),
    #  SẮP HẾT HẠN, còn 5 ngày — mốc vàng của cả hai khối.
    DongMau("DHHD", "Xác nhận đơn hàng của NCC",
            "NCC xác nhận số lượng, đơn giá, ngày giao bằng văn bản.",
            False, het_han=5, du_dinh=3,
            truoc=("Đơn mua hàng (PO) phát hành",)),
    DongMau("SXVC", "Lịch sản xuất & ngày giao dự kiến",
            "NCC gửi lịch chia lô nếu giao nhiều đợt.", False, du_dinh=20,
            truoc=("Xác nhận đơn hàng của NCC",)),
    DongMau("SXVC", "Chứng từ vận chuyển",
            "Vận đơn / phiếu xuất kho kiêm vận chuyển, biển số xe, tên tài xế.",
            False, du_dinh=35,
            truoc=("Lịch sản xuất & ngày giao dự kiến",)),
    DongMau("KTTQ", "Biên bản kiểm tra chất lượng",
            "Kiểm quy cách, số lượng theo lô; ghi rõ số lượng không đạt nếu có.",
            False, du_dinh=45,
            truoc=("Chứng từ vận chuyển",)),
    DongMau("KTTQ", "Chứng từ thông quan",
            "Tờ khai hải quan, C/O, kiểm dịch... chỉ áp dụng hàng nhập khẩu.",
            False, het_han=120, du_dinh=45,
            truoc=("Chứng từ vận chuyển",)),
    DongMau("NHVK", "Biên bản giao nhận có ký hai bên",
            "Ký sau khi kiểm tra xong, ghi số lượng thực nhận.", False, du_dinh=55,
            truoc=("Biên bản kiểm tra chất lượng",)),
    DongMau("NHVK", "Phiếu nhập kho",
            "Nhập đúng mã hàng, đối chiếu với đơn mua hàng.", False, du_dinh=55,
            truoc=("Biên bản giao nhận có ký hai bên",)),
    DongMau("NHVK", "Hóa đơn GTGT",
            "Kiểm tên, mã số thuế, đơn giá trước khi chuyển kế toán.", False, du_dinh=60,
            truoc=("Phiếu nhập kho",)),
    DongMau("NHVK", "Biên bản đối chiếu công nợ",
            "Đối chiếu trước khi đề nghị thanh toán phần còn lại.", False, du_dinh=70,
            truoc=("Hóa đơn GTGT",)),
]


def _next_code(db) -> str:
    """Cấp mã `HSxxxx` tiếp theo — bộ sinh CRUD không chạy ở đường script này."""
    last = (
        db.query(Dossier.code)
        .filter(Dossier.code.like("HS%"))
        .order_by(Dossier.id.desc())
        .first()
    )
    n = 0
    if last and last[0][2:].isdigit():
        n = int(last[0][2:])
    return f"HS{n + 1:04d}"


def _nap_kho_ho_so(db, ghi_de: bool) -> str:
    """Dựng / áp lại 15 tờ hồ sơ mẫu trong kho. Trả về câu tóm tắt."""
    types = {t.code: t for t in db.query(DossierType).all()}
    thieu = sorted({dong.loai for dong in MAU} - set(types))
    if thieu:
        raise SystemExit(
            "Danh mục Loại hồ sơ thiếu: " + ", ".join(thieu)
            + ". Chạy `python -m app.seed` trước."
        )

    them = sua = bo_qua = 0
    for dong in MAU:
        loai = types[dong.loai]
        #  Khớp theo cặp (tên · loại), KHÔNG theo mã: mã do máy cấp nên chạy
        #  lại lần hai sẽ ra mã khác và tờ nào cũng thành "chưa có".
        #
        #  ⚠️ Tên biến phải KHÁC cờ `xong` của dòng mẫu. Đè lên nó thì cờ «đã có
        #  giấy» lấy từ `MAU` biến mất, và dòng gán `status` bên dưới đọc phải
        #  kết quả truy vấn — vốn luôn `None` ở nhánh thêm mới — nên MỌI tờ ra
        #  «Nháp». Đúng lỗi từng mắc khi sửa tệp này bằng script thay-chuỗi.
        trong_kho = (
            db.query(Dossier)
            .filter(Dossier.name == dong.ten, Dossier.dossier_type_id == loai.id)
            .first()
        )
        if trong_kho is not None and not ghi_de:
            bo_qua += 1
            continue

        trang_thai = DOSSIER_ACTIVE if dong.xong else DOSSIER_DRAFT
        if trong_kho is not None:
            trong_kho.status = trang_thai
            trong_kho.note = dong.mo_ta
            trong_kho.issued_date = dong.ngay(dong.ngay_cap)
            trong_kho.expiry_date = dong.ngay(dong.het_han)
            sua += 1
            continue

        db.add(Dossier(
            code=_next_code(db),
            name=dong.ten,
            dossier_type_id=loai.id,
            dossier_type_name=loai.name,
            status=trang_thai,
            note=dong.mo_ta,
            issued_date=dong.ngay(dong.ngay_cap),
            expiry_date=dong.ngay(dong.het_han),
            #  Áp cho MỌI Yêu cầu báo giá: `apply_conditions` rỗng là cố ý,
            #  đây là bộ hồ sơ chung, không lọc theo mặt hàng.
            apply_doc_kinds=["survey_request"],
            apply_conditions=[],
            custom_fields=[],
            extra_fields={},
        ))
        #  Flush từng tờ: `_next_code` đọc lại bảng nên phải thấy tờ vừa thêm,
        #  không thì 15 tờ dùng chung một mã và vỡ ràng buộc duy nhất.
        db.flush()
        them += 1

    return f"Kho hồ sơ: thêm {them}, sửa {sua}, bỏ qua {bo_qua} (đã có)."


def _dong_bo_tien_do(db, ycbg_id: int) -> str:
    """Ghi kịch bản vào TIẾN ĐỘ hồ sơ của phiếu (`tab_dossier_progress`).

    ⚠️ Từ 21/09/2026, thẻ «Hồ sơ cần hoàn thành» đo bằng bảng NÀY chứ không đo
    bằng `tab_dossier.status`. Chỉ nạp kho hồ sơ thôi thì thẻ ra `0/15` trên
    mọi phiếu — đúng về nghiệp vụ (chưa ai làm gì cho phiếu đó) nhưng không đối
    chiếu được với khối Báo cáo thực hiện.

    Ghi theo cặp (tên · loại) như khi nạp kho, rồi tra ngược ra `dossier_id`.
    """
    types = {t.code: t for t in db.query(DossierType).all()}

    #  Tra TÊN → id một lượt: chuỗi tiên quyết khai bằng tên, mà bảng lưu bằng id.
    id_theo_ten: dict[str, int] = {}
    for dong in MAU:
        loai = types.get(dong.loai)
        if loai is None:
            continue
        tokho = (
            db.query(Dossier)
            .filter(Dossier.name == dong.ten, Dossier.dossier_type_id == loai.id)
            .first()
        )
        if tokho is not None:
            id_theo_ten[dong.ten] = tokho.id

    sua = 0
    for dong in MAU:
        dossier_id = id_theo_ten.get(dong.ten)
        if dossier_id is None:
            continue
        upsert_progress(db, "survey_request", ycbg_id, dossier_id, {
            "status": DP_DONE if dong.xong else DP_IDLE,
            "required": True,
            "planned_date": dong.ngay(dong.du_dinh),
            "note": "",
        })
        sua += 1
    return f"Tiến độ hồ sơ của YCBG {ycbg_id}: ghi {sua} dòng."


def _nap_tien_quyet(db) -> str:
    """Khai chuỗi TIÊN QUYẾT lên chính các TỜ HỒ SƠ (`tab_dossier.depends`).

    ⚠️ Không thuộc nhánh `--ycbg`: ràng buộc là của TỜ GIẤY, dùng chung cả kho,
    nên nạp cùng lúc với kho hồ sơ chứ không nạp theo từng phiếu. Bản trước ghi
    nó vào bảng tiến độ (theo phiếu) — đại ca đổi lại 21/09/2026.
    """
    types = {t.code: t for t in db.query(DossierType).all()}
    id_theo_ten: dict[str, int] = {}
    ho_so_theo_ten: dict[str, Dossier] = {}
    for dong in MAU:
        loai = types.get(dong.loai)
        if loai is None:
            continue
        tokho = (
            db.query(Dossier)
            .filter(Dossier.name == dong.ten, Dossier.dossier_type_id == loai.id)
            .first()
        )
        if tokho is not None:
            id_theo_ten[dong.ten] = tokho.id
            ho_so_theo_ten[dong.ten] = tokho

    sua = 0
    for dong in MAU:
        tokho = ho_so_theo_ten.get(dong.ten)
        if tokho is None:
            continue
        #  Tên nào không tra ra id thì BỎ, đừng ghi id rác: id chết được lọc ở
        #  chỗ đọc nên không khóa gì cả, nhưng nó vẫn nằm dưới DB và sẽ sống lại
        #  thành khóa nếu ai đó bỏ bước lọc đó.
        tokho.depends = [id_theo_ten[t] for t in dong.truoc if t in id_theo_ten]
        sua += 1
    return f"Tiên quyết trên tờ hồ sơ: ghi {sua} tờ."


def _dong_bo_bao_cao(db, ycbg_id: int) -> str:
    """Ghi cùng kịch bản sang khối *Báo cáo thực hiện* của một phiếu YCBG.

    Khớp theo TÊN đầu việc. Đầu việc nào không nằm trong `MAU` thì để nguyên —
    người thử có thể đã tự thêm dòng riêng, xóa của họ thì mất dữ liệu thật để
    đổi lấy một màn hình cho đẹp.
    """
    docs = (
        db.query(SurveyReportDoc)
        .filter(SurveyReportDoc.survey_request_id == ycbg_id)
        .all()
    )
    if not docs:
        raise SystemExit(
            f"Phiếu YCBG {ycbg_id} chưa có Báo cáo thực hiện. "
            "Mở phiếu, bấm «Khởi tạo báo cáo mẫu» rồi chạy lại."
        )

    theo_ten = {dong.ten: dong for dong in MAU}
    sua = bo_qua = 0
    for doc in docs:
        dong = theo_ten.get(doc.title)
        if dong is None:
            bo_qua += 1
            continue
        #  Thang trạng thái của báo cáo có BỐN mức, kho hồ sơ chỉ hai. Gộp
        #  «hoàn thành» ↔ «đang lưu»; phần còn lại về «chưa bắt đầu» chứ không
        #  rải sang «đang làm»/«chờ duyệt» — hai mức đó không có bên kia, bày ra
        #  là lúc đối chiếu lại phải giải thích một khác biệt của DỮ LIỆU chứ
        #  không phải của bố cục.
        doc.status = RD_DONE if dong.xong else RD_IDLE
        doc.description = dong.mo_ta
        doc.start_date = dong.ngay(dong.ngay_cap)
        doc.expires_at = dong.ngay(dong.het_han)
        doc.planned_date = dong.ngay(dong.du_dinh)
        sua += 1

    return f"Báo cáo thực hiện của YCBG {ycbg_id}: sửa {sua}, bỏ qua {bo_qua} (đầu việc riêng)."


def run(ghi_de: bool = False, ycbg_id: int = 0) -> None:
    db = SessionLocal()
    try:
        print(_nap_kho_ho_so(db, ghi_de))
        if ghi_de:
            print(_nap_tien_quyet(db))
        if ycbg_id:
            print(_dong_bo_bao_cao(db, ycbg_id))
            print(_dong_bo_tien_do(db, ycbg_id))
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ghi-de",
        action="store_true",
        help="Áp lại kịch bản lên 15 tờ hồ sơ đã có (mặc định chỉ thêm tờ thiếu).",
    )
    parser.add_argument(
        "--ycbg",
        type=int,
        default=0,
        help="Ghi cùng kịch bản sang Báo cáo thực hiện VÀ tiến độ hồ sơ của phiếu này.",
    )
    args = parser.parse_args()
    run(ghi_de=args.ghi_de, ycbg_id=args.ycbg)
