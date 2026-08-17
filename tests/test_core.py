# -*- coding: utf-8 -*-
"""单元测试: ai-unified-memory 核心脚本（common/promote/search/msg）"""
import os
import sys
import tempfile
import unittest
import shutil

# 指向开源包根目录
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))


class TestCommon(unittest.TestCase):
    def setUp(self):
        # 复制 CONFIG.example.json -> CONFIG.json，root 指向临时目录
        self.tmp = tempfile.mkdtemp()
        import common
        common.ROOT = self.tmp
        shutil.copy(os.path.join(ROOT, "CONFIG.example.json"),
                    os.path.join(self.tmp, "CONFIG.json"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_content_hash_stable(self):
        from common import content_hash
        self.assertEqual(content_hash("abc"), content_hash("abc"))
        self.assertNotEqual(content_hash("abc"), content_hash("abd"))

    def test_classify_category(self):
        from common import classify_category
        self.assertIn("用户画像", classify_category("姚老师 教授 高校教师"))
        self.assertIn("项目知识", classify_category("股票 决策大脑 项目"))
        self.assertIn("经验教训", classify_category("教训 黄金法则 避免"))

    def test_safe_filename(self):
        from common import safe_filename
        self.assertEqual(safe_filename("a/b:c*d?e"), "a_b_c_d_e")
        self.assertLessEqual(len(safe_filename("x" * 100)), 40)


class TestSearch(unittest.TestCase):
    def test_search_returns_list(self):
        from search import search_all
        # 无库时返回空列表不报错
        results = search_all("nothing", limit=5)
        self.assertIsInstance(results, list)


class TestMsg(unittest.TestCase):
    def test_send_and_list(self):
        import msg
        from common import cfg
        # 指向独立临时根，避免与其他测试共享状态
        self.tmp = tempfile.mkdtemp()
        import common
        common.ROOT = self.tmp
        shutil.copy(os.path.join(ROOT, "CONFIG.example.json"),
                    os.path.join(self.tmp, "CONFIG.json"))
        c = cfg()
        # 确保收件箱干净（清除任何残留消息）
        inbox = os.path.join(c["root"], c["exchange"], "INBOX", "Hermes")
        if os.path.isdir(inbox):
            for f in os.listdir(inbox):
                os.remove(os.path.join(inbox, f))
        # CONFIG.example.json 里有 Hermes
        mid = msg.send("Hermes", "测试标题", "测试内容")
        self.assertIsNotNone(mid)
        msgs = msg.list_msgs("Hermes")
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]["status"], "unread")
        r = msg.read_msg(mid)
        self.assertIsNotNone(r)
        self.assertIn("测试内容", r["content"])
        # 读后标记已读
        msgs2 = msg.list_msgs("Hermes")
        self.assertEqual(msgs2[0]["status"], "read")


if __name__ == "__main__":
    unittest.main(verbosity=2)
