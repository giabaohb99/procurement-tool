"""DANH MỤC NỀN của Nghỉ phép — V1-6: loại nghỉ, bậc thâm niên, lịch ngày lễ.

Ba bảng ở đây là thứ biến "luật nghỉ phép" từ **mã nguồn** thành **dữ liệu**.
Trước đợt này 7 loại nghỉ là hằng số chuỗi trong `core/leave_codes.py`, nên đổi
hạn mức phép năm từ 12 lên 14 ngày là sửa code + deploy. Sau đợt này là sửa một
ô trên màn danh mục.

Vì sao vẫn giữ cột `code` chuỗi: giấy GNP (`tab_document.metadata`) đã lưu mã
chuỗi từ CR-159, và luồng duyệt seed sẵn cũng rẽ nhánh theo mã đó. `code` là mối
nối giữa hai thế giới — xem `constants.py` đầu tệp.
"""
from datetime import date

from sqlalchemy import (BigInteger, Boolean, Date, Float, Index, Integer,
                        SmallInteger, String, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import AuditMixin, Base

from .constants import GENDER_UNKNOWN


class LeaveType(Base, AuditMixin):
    """Một loại nghỉ (Phép năm, Nghỉ ốm, Thai sản…) — cấu hình được, không hardcode.

    ~15 cột chứ không phải 50: doc `10-de-xuat-ap-dung.md` chốt bản 1 chỉ cần
    *tính công · theo ca · hạn mức năm · bậc thâm niên*. Thêm cột thì dễ, bỏ cột
    đã có dữ liệu thì không — nên bắt đầu hẹp.
    """

    __tablename__ = "tab_leave_type"

    #  Mã ỔN ĐỊNH, không đổi sau khi tạo. Đây là thứ ghi sang metadata của giấy
    #  GNP và là thứ seed dựa vào để nhận ra loại đã có hay chưa.
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(100))

    #  Nghỉ có tính công (hưởng lương) hay không — `tinhCong` của doc DT1.
    is_paid: Mapped[bool] = mapped_column(Boolean, default=True)

    #  Có TRỪ vào quỹ phép năm không. Phép năm thì có; nghỉ ốm / không lương /
    #  cưới hỏi thì không — chúng có hạn mức riêng hoặc không có hạn mức nào.
    #  Tách khỏi `is_paid` vì hai thứ không đi đôi: nghỉ cưới hỏi vẫn hưởng
    #  lương nhưng không ăn vào 12 ngày phép năm.
    counts_balance: Mapped[bool] = mapped_column(Boolean, default=False)

    #  Hạn mức cơ bản mỗi năm, trước khi cộng bậc thâm niên. `0` = không có hạn
    #  mức (nghỉ không lương), lúc đó `counts_balance` phải là False.
    annual_quota_days: Mapped[float] = mapped_column(Float, default=0.0)

    #  Trần cho MỘT đơn. `0` = không giới hạn. Dùng cho các loại có luật cứng
    #  (cưới hỏi 3 ngày, tang chế 3 ngày) mà không cần lập quỹ riêng.
    max_days_per_request: Mapped[float] = mapped_column(Float, default=0.0)

    #  Q2 của kế hoạch — chuyển phép thừa sang năm sau. MẶC ĐỊNH TẮT, vì bật rồi
    #  tắt lại thì phải đi gỡ số đã chuyển, còn tắt rồi bật thì không mất gì.
    carry_over: Mapped[bool] = mapped_column(Boolean, default=False)
    carry_over_max_days: Mapped[float] = mapped_column(Float, default=0.0)
    #  Phép chuyển sang hết hạn cuối tháng thứ mấy của năm sau (thông lệ: 3).
    carry_over_expire_month: Mapped[int] = mapped_column(SmallInteger, default=3)

    #  Lọc theo giới tính — thai sản chỉ hiện với nữ. `0` = mọi giới.
    #  ⚠️ Nhân sự CHƯA khai giới tính (`gender = 0`) thì vẫn cho qua, xem ghi chú
    #  ở `constants.GENDER_UNKNOWN`.
    gender: Mapped[int] = mapped_column(SmallInteger, default=GENDER_UNKNOWN)

    #  Phải nộp trước mấy ngày. `0` = nộp lúc nào cũng được (nghỉ ốm — không ai
    #  báo trước được là mai mình ốm).
    min_notice_days: Mapped[int] = mapped_column(SmallInteger, default=0)
    #  Bắt đính kèm (giấy khám bệnh, giấy đăng ký kết hôn…).
    require_attachment: Mapped[bool] = mapped_column(Boolean, default=False)

    #  Tính số ngày có trừ T7/CN và ngày lễ không. Phép năm thì CÓ; thai sản thì
    #  KHÔNG (nghỉ 6 tháng liên tục, tính cả cuối tuần).
    exclude_holiday: Mapped[bool] = mapped_column(Boolean, default=True)

    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    note: Mapped[str] = mapped_column(String(500), default="")

    seniority_tiers = relationship(
        "LeaveTypeSeniority",
        primaryjoin="foreign(LeaveTypeSeniority.leave_type_id) == LeaveType.id",
        order_by="LeaveTypeSeniority.years_from",
        uselist=True,
        viewonly=True,
    )


class LeaveTypeSeniority(Base, AuditMixin):
    """Bậc phép cộng thêm theo THÂM NIÊN — luật khai bằng dữ liệu, không bằng mã.

    Luật lao động *"cứ 5 năm làm việc thì được thêm 1 ngày phép"* nếu viết thành
    `extra = years // 5` trong `balance_service` thì tới lúc công ty đổi thành
    3 năm, hoặc thành bậc không đều (5 năm +1, 10 năm +3), phải sửa mã và deploy.
    Ở dạng bảng thì Nhân sự tự thêm dòng.

    Khoảng là **nửa mở**: khớp khi `years_from <= thâm_niên` và
    (`years_to = 0` hoặc `thâm_niên < years_to`). Lấy bậc CAO NHẤT khớp được —
    xem `balance_service.seniority_days`.
    """

    __tablename__ = "tab_leave_type_seniority"
    __table_args__ = (
        Index("ix_leave_seniority_type", "leave_type_id", "years_from"),
    )

    leave_type_id: Mapped[int] = mapped_column(BigInteger, default=0)
    years_from: Mapped[int] = mapped_column(SmallInteger, default=0)
    #  `0` = không có trần trên (bậc cuối cùng, "từ 20 năm trở lên").
    years_to: Mapped[int] = mapped_column(SmallInteger, default=0)
    extra_days: Mapped[float] = mapped_column(Float, default=0.0)
    note: Mapped[str] = mapped_column(String(255), default="")


class Holiday(Base, AuditMixin):
    """Một ngày nghỉ lễ. Dùng để KHÔNG tính nó vào số ngày phép đã dùng.

    `suggested_days()` của CR-159 cố ý không trừ T7/CN/lễ vì lúc đó chưa có bảng
    này. Nay có rồi thì `workday_service` là nơi duy nhất tính, và tệp cũ chỉ
    còn phục vụ giấy GNP nhập tay.
    """

    __tablename__ = "tab_holiday"
    __table_args__ = (
        #  Trùng ngày trong CÙNG pháp nhân là dữ liệu hỏng — hai dòng "Tết
        #  Dương lịch" thì đếm hai lần nếu chỗ nào lỡ dùng COUNT thay vì DISTINCT.
        UniqueConstraint("company_id", "date", name="uq_holiday_company_date"),
        Index("ix_holiday_date", "date"),
    )

    #  `0` = áp cho MỌI pháp nhân. Pháp nhân nào có lịch riêng (nhà máy nghỉ bù
    #  khác văn phòng) thì thêm dòng của riêng nó — `workday_service` gộp cả hai.
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)
    date: Mapped[date] = mapped_column(Date)
    name: Mapped[str] = mapped_column(String(150), default="")

    #  Lặp lại hằng năm theo ngày/tháng (Tết Dương lịch, Quốc khánh). Tết Âm và
    #  Giỗ Tổ **không** lặp được vì trôi theo lịch âm — mỗi năm nhập một lần.
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
