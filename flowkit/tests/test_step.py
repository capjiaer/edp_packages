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
        self.assertEqual(self.step1.prev_steps, [])
        self.assertEqual(self.step1.next_steps, [])

        # 测试默认值
        step = Step("test")
        self.assertEqual(step.cmd, None)
        self.assertEqual(step.inputs, [])
        self.assertEqual(step.outputs, [])

    def test_add_next_step(self):
        """测试添加后续步骤"""
        # 添加后续步骤
        self.step1.add_next_step(self.step2)

        # 验证关系是双向的
        self.assertIn(self.step2, self.step1.next_steps)
        self.assertIn(self.step1, self.step2.prev_steps)

        # 测试重复添加
        self.step1.add_next_step(self.step2)
        self.assertEqual(len(self.step1.next_steps), 1)
        self.assertEqual(len(self.step2.prev_steps), 1)

        # 测试链式关系
        self.step2.add_next_step(self.step3)
        self.assertIn(self.step3, self.step2.next_steps)
        self.assertIn(self.step2, self.step3.prev_steps)

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

    def test_can_run_no_deps(self):
        """测试无依赖时的可运行状态"""
        # 没有前置步骤时应该可以运行
        self.assertTrue(self.step1.can_run())
        self.assertTrue(self.step1.can_run(ignore_failed_deps=True))

    def test_can_run_with_deps(self):
        """测试有依赖时的可运行状态"""
        # 设置依赖关系
        self.step1.add_next_step(self.step2)
        self.step2.add_next_step(self.step3)

        # 当前置步骤未完成时，不应该可以运行
        self.assertFalse(self.step2.can_run())
        self.assertFalse(self.step3.can_run())

        # 当前置步骤完成时，应该可以运行
        self.step1.update_status(StepStatus.FINISHED)
        self.assertTrue(self.step2.can_run())
        self.assertFalse(self.step3.can_run())

        # 当前置步骤跳过时，也应该可以运行
        self.step1.update_status(StepStatus.SKIPPED)
        self.assertTrue(self.step2.can_run())

    def test_can_run_with_failed_deps(self):
        """测试前置步骤失败时的可运行状态"""
        # 设置依赖关系
        self.step1.add_next_step(self.step2)

        # 当前置步骤失败时
        self.step1.update_status(StepStatus.FAILED)

        # 默认情况下，不应该可以运行
        self.assertFalse(self.step2.can_run())

        # 当忽略失败的前置步骤时，应该可以运行
        self.assertTrue(self.step2.can_run(ignore_failed_deps=True))

    def test_get_all_prerequisites(self):
        """测试获取所有前置步骤"""
        # 创建更复杂的依赖关系
        step4 = Step("step4")
        step5 = Step("step5")

        # step1 -> step2 -> step3
        #      \-> step4 -> step5 -> step3
        self.step1.add_next_step(self.step2)
        self.step1.add_next_step(step4)
        self.step2.add_next_step(self.step3)
        step4.add_next_step(step5)
        step5.add_next_step(self.step3)

        # 测试 step3 的所有前置步骤
        prerequisites = self.step3.get_all_prerequisites()
        self.assertEqual(len(prerequisites), 4)
        self.assertIn(self.step1, prerequisites)
        self.assertIn(self.step2, prerequisites)
        self.assertIn(step4, prerequisites)
        self.assertIn(step5, prerequisites)

        # 测试 step5 的所有前置步骤
        prerequisites = step5.get_all_prerequisites()
        self.assertEqual(len(prerequisites), 2)
        self.assertIn(self.step1, prerequisites)
        self.assertIn(step4, prerequisites)

    def test_repr(self):
        """测试字符串表示"""
        self.assertEqual(repr(self.step1), "Step(step1, status=init)")
        self.step1.update_status(StepStatus.RUNNING)
        self.assertEqual(repr(self.step1), "Step(step1, status=running)")


if __name__ == '__main__':
    unittest.main()
