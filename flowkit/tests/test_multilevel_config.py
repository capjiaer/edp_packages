"""
测试多级配置

此模块测试多级配置系统，特别是 get_flow_var 函数的行为。
"""

import unittest
import sys
import os

# 添加父目录到 Python 路径，以便能够导入 flowkit 模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from flowkit.run_graph import get_flow_var
from flowkit.step import Step


class TestMultilevelConfig(unittest.TestCase):
    """测试多级配置系统"""

    def setUp(self):
        """每个测试前的设置"""
        # 创建测试配置
        self.config = {
            "edp": {
                "lsf": 1,
                "cpu_num": 4,
                "memory": 8000,
                "queue": "normal"
            },
            "pnr_innovus": {
                "default": {
                    "lsf": 1,
                    "cpu_num": 8,
                    "memory": 16000,
                    "queue": "pnr_normal"
                },
                "floorplan": {
                    "cpu_num": 16,
                    "memory": 32000
                },
                "place": {
                    "cpu_num": 32,
                    "memory": 64000,
                    "queue": "pnr_high"
                }
            },
            "pv_calibre": {
                "default": {
                    "lsf": 1,
                    "cpu_num": 16,
                    "memory": 32000,
                    "queue": "pv_normal"
                },
                "drc": {
                    "cpu_num": 32
                }
            },
            # 注意：我们不再支持顶层变量
        }

        # 创建测试步骤
        self.step1 = Step("pnr_innovus.floorplan", "floorplan.tcl")
        self.step2 = Step("pnr_innovus.place", "place.tcl")
        self.step3 = Step("pnr_innovus.route", "route.tcl")
        self.step4 = Step("pv_calibre.drc", "drc.tcl")
        self.step5 = Step("pv_calibre.lvs", "lvs.tcl")
        self.step6 = Step("other_flow.step", "step.tcl")

    def test_step_level_config(self):
        """测试步骤级别配置"""
        # pnr_innovus.floorplan 有自己的 cpu_num 和 memory 配置
        self.assertEqual(get_flow_var(self.step1, "cpu_num", self.config), 16)
        self.assertEqual(get_flow_var(self.step1, "memory", self.config), 32000)

        # pnr_innovus.place 有自己的 cpu_num、memory 和 queue 配置
        self.assertEqual(get_flow_var(self.step2, "cpu_num", self.config), 32)
        self.assertEqual(get_flow_var(self.step2, "memory", self.config), 64000)
        self.assertEqual(get_flow_var(self.step2, "queue", self.config), "pnr_high")

        # pv_calibre.drc 只有自己的 cpu_num 配置
        self.assertEqual(get_flow_var(self.step4, "cpu_num", self.config), 32)

    def test_tool_default_config(self):
        """测试工具默认级别配置"""
        # pnr_innovus.route 没有自己的配置，应该使用 pnr_innovus.default 的配置
        self.assertEqual(get_flow_var(self.step3, "cpu_num", self.config), 8)
        self.assertEqual(get_flow_var(self.step3, "memory", self.config), 16000)
        self.assertEqual(get_flow_var(self.step3, "queue", self.config), "pnr_normal")

        # pnr_innovus.floorplan 没有自己的 queue 配置，应该使用 pnr_innovus.default 的配置
        self.assertEqual(get_flow_var(self.step1, "queue", self.config), "pnr_normal")

        # pv_calibre.drc 没有自己的 memory 配置，应该使用 pv_calibre.default 的配置
        self.assertEqual(get_flow_var(self.step4, "memory", self.config), 32000)

        # pv_calibre.lvs 没有自己的配置，应该使用 pv_calibre.default 的配置
        self.assertEqual(get_flow_var(self.step5, "cpu_num", self.config), 16)
        self.assertEqual(get_flow_var(self.step5, "memory", self.config), 32000)
        self.assertEqual(get_flow_var(self.step5, "queue", self.config), "pv_normal")

    def test_global_config(self):
        """测试全局级别配置"""
        # other_flow.step 没有自己的配置，也没有工具默认配置，应该使用 edp 的配置
        self.assertEqual(get_flow_var(self.step6, "cpu_num", self.config), 4)
        self.assertEqual(get_flow_var(self.step6, "memory", self.config), 8000)
        self.assertEqual(get_flow_var(self.step6, "queue", self.config), "normal")

        # 所有步骤都应该能获取到 edp.lsf 配置
        self.assertEqual(get_flow_var(self.step1, "lsf", self.config), 1)
        self.assertEqual(get_flow_var(self.step2, "lsf", self.config), 1)
        self.assertEqual(get_flow_var(self.step3, "lsf", self.config), 1)
        self.assertEqual(get_flow_var(self.step4, "lsf", self.config), 1)
        self.assertEqual(get_flow_var(self.step5, "lsf", self.config), 1)
        self.assertEqual(get_flow_var(self.step6, "lsf", self.config), 1)

    def test_default_value(self):
        """测试默认值"""
        # 不存在的变量应该返回默认值
        self.assertEqual(get_flow_var(self.step1, "non_existent", self.config, default="default_value"), "default_value")
        self.assertEqual(get_flow_var(self.step6, "non_existent", self.config, default=42), 42)

    # 注意：我们不再支持顶层变量，因此移除了向后兼容性测试

    def test_string_step_name(self):
        """测试使用字符串作为步骤名称"""
        # 使用字符串作为步骤名称
        self.assertEqual(get_flow_var("pnr_innovus.floorplan", "cpu_num", self.config), 16)
        self.assertEqual(get_flow_var("pnr_innovus.place", "queue", self.config), "pnr_high")
        self.assertEqual(get_flow_var("pv_calibre.drc", "memory", self.config), 32000)
        self.assertEqual(get_flow_var("other_flow.step", "cpu_num", self.config), 4)


if __name__ == '__main__':
    unittest.main()
