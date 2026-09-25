"""bao-CR-488 — ô «Phòng xử lý» ẩn sau ô tick «Nhờ phòng khác xử lý» khi LẬP phiếu.

Giao diện không tick thì KHÔNG gửi ô này (`None`) → backend tra mặc định của bao-CR-480
(phòng tự mua → chính phòng lập, còn lại → 0 Thu mua chung). Tick và chọn thì gửi số, và
số đó — kể cả 0 — là lựa chọn có chủ ý, backend giữ nguyên. Trước CR này gửi 0 cũng bị tra
đè, nên nhà máy không có cách nào nhờ Thu mua chung ngay lúc lập phiếu (ca DEMO TM01).
"""
from app.modules.purchase_request import service as pr_service
from app.modules.purchase_request.schema import PRCreate
from app.modules.survey_request import service as sr_service
from app.modules.survey_request.schema import SurveyRequestCreate
from test_phong_xu_ly_cr480 import _person, two_departments  # noqa: F401 — fixture dùng chung


def test_factory_leaving_the_box_untouched_gets_its_own_department(db, seed, two_departments):
    factory_id, _ = two_departments
    _, emp = _person(db, seed, factory_id, scope="dept_proc")
    pr = pr_service.create_pr(db, PRCreate(company_id=seed.company_id, requester_id=emp.id,
                                           department_id=factory_id, purpose="không tick"),
                              user_id=seed.u_req_id)
    assert pr.handler_dept_id == factory_id


def test_factory_explicitly_choosing_shared_purchasing_is_kept(db, seed, two_departments):
    """Ca TM01: nhà máy xin, THU MUA CHUNG mua — tick rồi chọn «Thu mua chung» (0)."""
    factory_id, _ = two_departments
    _, emp = _person(db, seed, factory_id, scope="dept_proc")
    pr = pr_service.create_pr(db, PRCreate(company_id=seed.company_id, requester_id=emp.id,
                                           department_id=factory_id, handler_dept_id=0,
                                           purpose="tick, chọn Thu mua chung"),
                              user_id=seed.u_req_id)
    assert pr.handler_dept_id == 0


def test_ordinary_department_sending_zero_or_nothing_both_land_on_shared_purchasing(
        db, seed, two_departments):
    pr = pr_service.create_pr(db, PRCreate(company_id=seed.company_id, requester_id=seed.emp_req_id,
                                           purpose="phòng thường, không gửi"), user_id=seed.u_req_id)
    pr0 = pr_service.create_pr(db, PRCreate(company_id=seed.company_id, requester_id=seed.emp_req_id,
                                            handler_dept_id=0, purpose="phòng thường, gửi 0"),
                               user_id=seed.u_req_id)
    assert pr.handler_dept_id == 0 and pr0.handler_dept_id == 0


def test_survey_request_follows_the_same_rule(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    # «Phòng tự mua» nhận diện qua quyền YCMH bậc dept_proc (bao-CR-480), kể cả khi lập YCBG.
    _, emp = _person(db, seed, factory_id, scope="dept_proc")
    base = dict(company_id=seed.company_id, requester=emp.full_name, requester_id=emp.id,
                department_id=factory_id, purpose="YCBG nhà máy")
    untouched = sr_service.create_sr(db, SurveyRequestCreate(**base), user_id=seed.u_req_id)
    shared = sr_service.create_sr(db, SurveyRequestCreate(**base, handler_dept_id=0), user_id=seed.u_req_id)
    other = sr_service.create_sr(db, SurveyRequestCreate(**base, handler_dept_id=purchasing_id),
                                 user_id=seed.u_req_id)
    assert untouched.handler_dept_id == factory_id
    assert shared.handler_dept_id == 0
    assert other.handler_dept_id == purchasing_id


def test_schema_default_is_none_not_zero():
    """Mặc định của schema phải là «chưa chọn» — đổi về 0 là tắt lại cả ca TM01."""
    assert PRCreate(company_id=1, purpose="x").handler_dept_id is None
    assert SurveyRequestCreate(company_id=1, purpose="x").handler_dept_id is None
