# -*- coding: utf-8 -*-
"""单元测试: memory_engine v2.0（语义检索/冲突消解/热度/时间线）"""
import os
import sys
import shutil
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import common
import memory_engine as me


class TestSemanticSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        common.ROOT = cls.tmp
        # 复制配置模板
        shutil.copy(os.path.join(ROOT, "CONFIG.example.json"),
                    os.path.join(cls.tmp, "CONFIG.json"))
        # 建立最小公用库
        os.makedirs(os.path.join(cls.tmp, "01_公用库", "00_用户画像"), exist_ok=True)
        os.makedirs(os.path.join(cls.tmp, "01_公用库", "01_项目知识"), exist_ok=True)
        common.write_text(
            os.path.join(cls.tmp, "01_公用库", "01_项目知识", "股票记忆.md"),
            "---\ntitle: 股票记忆\n---\n\n# 股票投资\n姚老师持有立讯精密、中信证券等股票，主板only。"
        )
        common.write_text(
            os.path.join(cls.tmp, "01_公用库", "00_用户画像", "用户档案.md"),
            "---\ntitle: 用户档案\n---\n\n# 用户\n高校教授，研究方向是建筑节能与热舒适。"
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_direct_match(self):
        r = me.semantic_search("股票", limit=5)
        self.assertTrue(any("股票记忆" in x["title"] for x in r))

    def test_synonym_expansion(self):
        # "证券" 应通过同义词扩展命中 "股票"
        r = me.semantic_search("证券", limit=5)
        self.assertTrue(any("股票记忆" in x["title"] for x in r))

    def test_no_match(self):
        r = me.semantic_search("完全不存在的东西xyz", limit=5)
        self.assertEqual(len(r), 0)

    def test_score_ordering(self):
        r = me.semantic_search("股票 立讯", limit=5)
        self.assertGreaterEqual(r[0]["score"], r[-1]["score"])


class TestConflictResolution(unittest.TestCase):
    def test_merge_similar(self):
        tmp = tempfile.mkdtemp()
        common.ROOT = tmp
        shutil.copy(os.path.join(ROOT, "CONFIG.example.json"),
                    os.path.join(tmp, "CONFIG.json"))
        cat = os.path.join(tmp, "01_公用库", "00_用户画像")
        os.makedirs(cat, exist_ok=True)
        # 两个标题相似的文件（模拟重复快照）
        common.write_text(os.path.join(cat, "profile_a_1111111111111111.md"), "# 内容A")
        common.write_text(os.path.join(cat, "profile_a_2222222222222222.md"), "# 内容B")
        result = me.resolve_conflicts()
        self.assertEqual(result["merged"], 1)
        # 归档目录应有一个文件
        archive = os.path.join(cat, "_archived")
        self.assertTrue(os.path.isdir(archive))
        shutil.rmtree(tmp, ignore_errors=True)


class TestHeat(unittest.TestCase):
    def test_record_and_hot(self):
        tmp = tempfile.mkdtemp()
        common.ROOT = tmp
        shutil.copy(os.path.join(ROOT, "CONFIG.example.json"),
                    os.path.join(tmp, "CONFIG.json"))
        path = os.path.join(tmp, "01_公用库", "test.md")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        common.write_text(path, "# test")
        me.record_hit(path)
        me.record_hit(path)
        hot = me.hot_memories(5)
        self.assertTrue(any(h["path"].replace("\\", "/") == path.replace("\\", "/")
                            and h["count"] == 2 for h in hot))
        shutil.rmtree(tmp, ignore_errors=True)


class TestTimeline(unittest.TestCase):
    def test_timeline_current(self):
        tmp = tempfile.mkdtemp()
        common.ROOT = tmp
        shutil.copy(os.path.join(ROOT, "CONFIG.example.json"),
                    os.path.join(tmp, "CONFIG.json"))
        path = os.path.join(tmp, "01_公用库", "test.md")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        common.write_text(path, "# test")
        tl = me.timeline(path)
        self.assertEqual(tl[0]["version"], "current")
        self.assertIn("modified", tl[0])
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
