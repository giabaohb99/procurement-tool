"""Test service bình luận: resolve tên (batch), list theo (entity,entity_id), gom người nhận."""
from app.modules.comment import service as C
from app.modules.comment.model import Comment


def _add(db, entity, entity_id, body, created_by, parent_id=None, mention=None):
    c = Comment(entity=entity, entity_id=entity_id, body=body, parent_id=parent_id,
                mention_user_ids=mention, created_by=created_by, updated_by=created_by)
    db.add(c)
    db.flush()
    return c


class TestCommentService:
    def test_list_filters_by_entity_and_orders_asc(self, db, seed):
        _add(db, "survey", 1, "A", seed.u_req_id)
        _add(db, "survey", 1, "B", seed.u_nstm_id)
        _add(db, "survey", 2, "khác phiếu", seed.u_req_id)          # entity_id khác → loại
        _add(db, "survey_line", 1, "khác entity", seed.u_req_id)     # entity khác → loại
        items = C.list_comments(db, "survey", 1)
        assert [c.body for c in items] == ["A", "B"]                 # đúng thứ tự id tăng

    def test_resolve_names_batch(self, db, seed):
        names = C.resolve_names(db, {seed.u_nstm_id, seed.u_req_id, 999999})
        assert names[seed.u_nstm_id] == "NSTM Chính"                 # từ Employee.full_name
        assert names[seed.u_req_id] == "Người YC"
        assert 999999 not in names                                  # user không tồn tại → bỏ

    def test_resolve_names_empty(self, db):
        assert C.resolve_names(db, set()) == {}

    def test_collect_recipients_owner_parent_mention_minus_self(self, db, seed):
        MENTION = 9001
        parent = _add(db, "survey", 1, "gốc", seed.u_req_id)
        reply = _add(db, "survey", 1, "trả lời", seed.u_nstm_id,
                     parent_id=parent.id, mention=[MENTION])
        rec = set(C.collect_recipients(db, reply, survey_created_by=seed.u_req_id))
        # owner(u_req) + parent author(u_req) + mention(9001); trừ chính người reply(u_nstm)
        assert rec == {seed.u_req_id, MENTION}
        assert seed.u_nstm_id not in rec

    def test_collect_recipients_excludes_self_as_owner(self, db, seed):
        c = _add(db, "survey", 1, "tự bình luận", seed.u_req_id)
        rec = C.collect_recipients(db, c, survey_created_by=seed.u_req_id)
        assert rec == []                                            # chỉ mình → không báo ai

    def test_allowed_entities(self):
        assert C.ALLOWED_ENTITIES == {"survey", "survey_line"}

    def test_resolve_survey_id(self, db, seed):
        # entity='survey' → chính nó
        assert C.resolve_survey_id(db, "survey", 777) == 777
        # entity='survey_line' → survey_id của dòng (psl_nhan_1 thuộc sv_nhan)
        assert C.resolve_survey_id(db, "survey_line", seed.psl_nhan_1_id) == seed.sv_nhan_id
        # dòng không tồn tại → None
        assert C.resolve_survey_id(db, "survey_line", 999999) is None

    def test_valid_mention_ids_filters_inactive_and_unknown(self, db, seed):
        got = set(C.valid_mention_ids(db, [seed.u_req_id, seed.u_nstm_id, 999999]))
        assert got == {seed.u_req_id, seed.u_nstm_id}    # bỏ id không tồn tại
        assert C.valid_mention_ids(db, None) == []
        assert C.valid_mention_ids(db, []) == []

    def test_check_parent_same_thread_and_one_level(self, db, seed):
        root = _add(db, "survey", 1, "gốc", seed.u_req_id)
        C.check_parent(db, "survey", 1, root.id)                 # hợp lệ → không raise
        C.check_parent(db, "survey", 1, None)                    # không có parent → OK
        # khác luồng (entity_id khác) → lỗi
        try:
            C.check_parent(db, "survey", 2, root.id); assert False
        except ValueError:
            pass
        # trả lời của trả lời (2 cấp) → lỗi
        reply = _add(db, "survey", 1, "trả lời", seed.u_nstm_id, parent_id=root.id)
        try:
            C.check_parent(db, "survey", 1, reply.id); assert False
        except ValueError:
            pass
