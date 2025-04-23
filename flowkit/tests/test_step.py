"""
测试 Step 模块

此模块包含对 Step 类和 StepStatus 类的单元测试。
"""

import unittest
import sys
import os

# 添加父目录到 Python 路径，以便能够导入 flowkit 模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from flowkit.step import Step, StepStatus


class TestStep(unittest.TestCase):
    """测试 Step 类"""

    def setUp(self):
        """每个测试前的设置"""
        # 创建一些测试步骤
        self.step1 = Step("step1", "echo step1", ["input1.txt"], ["output1.txt"])
        self.step2 = Step("step2", "echo step2", ["output1.txt"], ["output2.txt"])
        self.step3 = Step("step3", "echo step3", ["output2.txt"], ["output3.txt"])

    def test_init(self):
        """测试步骤初始化"""
        # 测试基本属性
        self.assertEqual(self.step1.id, "step1")
        self.assertEqual(self.step1.name, "step1")
        self.assertEqual(self.step1.cmd, "echo step1")
        self.assertEqual(self.step1.inputs, ["input1.txt"])
        self.assertEqual(self.step1.outputs, ["output1.txt"])
        self.assertEqual(self.step1.status, StepStatus.INIT)

        # 测试默认值
        step = Step("test")
        self.assertEqual(step.cmd, None)
        self.assertEqual(step.inputs, [])
        self.assertEqual(step.outputs, [])

    def test_update_status(self):
        """测试更新状态"""
        # 测试有效状态更新
        self.step1.update_status(StepStatus.RUNNING)
        self.assertEqual(self.step1.status, StepStatus.RUNNING)

        self.step1.update_status(StepStatus.FINISHED)
        self.assertEqual(self.step1.status, StepStatus.FINISHED)

        # 测试无效状态
        with self.assertRaises(ValueError):
            self.step1.update_status("invalid_status")

    def test_set_status(self):
        """测试设置状态（兼容性方法）"""
        self.step1.set_status(StepStatus.SKIPPED)
        self.assertEqual(self.step1.status, StepStatus.SKIPPED)

    def test_get_status(self):
        """测试获取状态"""
        self.assertEqual(self.step1.get_status(), StepStatus.INIT)
        self.step1.update_status(StepStatus.RUNNING)
        self.assertEqual(self.step1.get_status(), StepStatus.RUNNING)

    def test_reset(self):
        """测试重置状态"""
        # 从非 INIT 状态重置
        self.step1.update_status(StepStatus.FINISHED)
        self.step1.reset()
        self.assertEqual(self.step1.status, StepStatus.INIT)

        # 从 INIT 状态重置（不应该有变化）
        self.step1.reset()
        self.assertEqual(self.step1.status, StepStatus.INIT)

    def test_repr(self):
        """测试字符串表示"""
        self.assertEqual(repr(self.step1), f"Step({self.step1.id}, status={self.step1.status})")
        self.step1.update_status(StepStatus.RUNNING)
        self.assertEqual(repr(self.step1), f"Step({self.step1.id}, status={StepStatus.RUNNING})")


class TestStepStatus(unittest.TestCase):
    """测试 StepStatus 类"""

    def test_status_constants(self):
        """测试状态常量"""
        self.assertEqual(StepStatus.INIT, "init")
        self.assertEqual(StepStatus.RUNNING, "running")
        self.assertEqual(StepStatus.FINISHED, "finished")
        self.assertEqual(StepStatus.SKIPPED, "skipped")
        self.assertEqual(StepStatus.FAILED, "failed")


if __name__ == '__main__':
    unittest.main()
