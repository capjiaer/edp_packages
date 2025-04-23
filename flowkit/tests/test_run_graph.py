"""
测试 run_graph 模块

此模块包含对 run_graph 模块中各函数的单元测试。
"""

import unittest
import sys
import os
import logging

# 添加父目录到 Python 路径，以便能够导入 flowkit 模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from flowkit.run_graph import execute_step, execute_all_steps, execute_steps_parallel, get_flow_var, get_status_summary
from flowkit.graph import Graph
from flowkit.step import Step, StepStatus


class TestRunGraph(unittest.TestCase):
    """测试 run_graph 模块"""

    def setUp(self):
        """每个测试前的设置"""
        # 创建一些测试步骤
        self.step1 = Step("step1", "echo step1", ["input1.txt"], ["output1.txt"])
        self.step2 = Step("step2", "echo step2", ["output1.txt"], ["output2.txt"])
        self.step3 = Step("step3", "echo step3", ["output2.txt"], ["output3.txt"])
        self.step4 = Step("step4", "echo step4", ["output1.txt"], ["output4.txt"])
        self.step5 = Step("step5", "echo step5", ["output4.txt", "output2.txt"], ["output5.txt"])

        # 创建步骤字典
        self.steps_dict = {
            "step1": self.step1,
            "step2": self.step2,
            "step3": self.step3,
            "step4": self.step4,
            "step5": self.step5
        }

        # 创建图
        self.graph = Graph(steps_dict=self.steps_dict)

        # 创建配置字典
        self.config = {
            "global_var": "global_value",
            "flow1": {
                "flow_var": "flow_value",
                "step1": {
                    "step_var": "step_value"
                }
            }
        }

        # 记录执行的步骤
        self.executed_steps = []

        # 禁用日志输出
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        """每个测试后的清理"""
        # 重置所有步骤状态
        for step in self.steps_dict.values():
            step.reset()

        # 清空执行记录
        self.executed_steps = []

        # 恢复日志输出
        logging.disable(logging.NOTSET)

    def mock_execute_func(self, step, merged_var):
        """模拟执行函数"""
        self.executed_steps.append(step.name)
        return True

    def mock_execute_func_with_failure(self, step, merged_var):
        """模拟执行函数（带失败）"""
        self.executed_steps.append(step.name)
        return step.name != "step2"  # step2 执行失败

    def test_execute_step(self):
        """测试执行单个步骤"""
        # 执行 step1
        result = execute_step(self.graph, "step1", execute_func=self.mock_execute_func, merged_var=self.config)

        # 验证结果
        self.assertTrue(result)
        self.assertEqual(self.executed_steps, ["step1"])
        self.assertEqual(self.step1.status, StepStatus.FINISHED)

    def test_execute_step_with_deps(self):
        """测试执行有依赖的步骤"""
        # 尝试执行 step2（依赖 step1）
        result = execute_step(self.graph, "step2", execute_func=self.mock_execute_func, merged_var=self.config)

        # 验证结果（应该失败，因为 step1 未完成）
        self.assertFalse(result)
        self.assertEqual(self.executed_steps, [])
        self.assertEqual(self.step2.status, StepStatus.INIT)

        # 将 step1 标记为已完成
        self.step1.update_status(StepStatus.FINISHED)

        # 再次尝试执行 step2
        result = execute_step(self.graph, "step2", execute_func=self.mock_execute_func, merged_var=self.config)

        # 验证结果（应该成功）
        self.assertTrue(result)
        self.assertEqual(self.executed_steps, ["step2"])
        self.assertEqual(self.step2.status, StepStatus.FINISHED)

    def test_execute_step_force(self):
        """测试强制执行步骤"""
        # 强制执行 step2（忽略依赖）
        result = execute_step(self.graph, "step2", execute_func=self.mock_execute_func, merged_var=self.config, force=True)

        # 验证结果
        self.assertTrue(result)
        self.assertEqual(self.executed_steps, ["step2"])
        self.assertEqual(self.step2.status, StepStatus.FINISHED)

    def test_execute_step_nonexistent(self):
        """测试执行不存在的步骤"""
        # 尝试执行不存在的步骤
        with self.assertRaises(ValueError):
            execute_step(self.graph, "non_existent", execute_func=self.mock_execute_func, merged_var=self.config)

    def test_execute_all_steps(self):
        """测试执行所有步骤"""
        # 执行所有步骤
        results = execute_all_steps(self.graph, execute_func=self.mock_execute_func, merged_var=self.config)

        # 验证结果
        self.assertEqual(len(results), 5)
        self.assertTrue(all(results.values()))

        # 验证执行顺序（应该遵循依赖关系）
        self.assertEqual(self.executed_steps[0], "step1")
        self.assertIn("step2", self.executed_steps[1:3])
        self.assertIn("step4", self.executed_steps[1:3])
        self.assertIn("step3", self.executed_steps[3:5])
        self.assertIn("step5", self.executed_steps[3:5])

        # 验证所有步骤状态
        for step in self.steps_dict.values():
            self.assertEqual(step.status, StepStatus.FINISHED)

    def test_execute_all_steps_with_failure(self):
        """测试执行所有步骤（带失败）"""
        # 执行所有步骤，但 step2 会失败
        results = execute_all_steps(self.graph, execute_func=self.mock_execute_func_with_failure, merged_var=self.config)

        # 验证结果
        # 注意：根据当前实现，execute_all_steps 可能会返回3个结果（step1, step2, step4）
        # 因为 step4 只依赖 step1，而 step1 成功了
        self.assertIn("step1", results)
        self.assertIn("step2", results)
        self.assertTrue(results["step1"])
        self.assertFalse(results["step2"])

        # 验证执行顺序（前两个步骤应该是 step1 和 step2）
        self.assertEqual(self.executed_steps[0], "step1")
        self.assertEqual(self.executed_steps[1], "step2")

        # 验证步骤状态
        self.assertEqual(self.step1.status, StepStatus.FINISHED)
        self.assertEqual(self.step2.status, StepStatus.FAILED)
        self.assertEqual(self.step3.status, StepStatus.INIT)  # step3 依赖 step2，所以不会执行

    def test_execute_all_steps_continue_on_failure(self):
        """测试执行所有步骤（失败时继续）"""
        # 执行所有步骤，但 step2 会失败，设置失败时继续
        results = execute_all_steps(
            self.graph,
            execute_func=self.mock_execute_func_with_failure,
            merged_var=self.config,
            continue_on_failure=True
        )

        # 验证结果
        # 注意：根据当前实现，execute_all_steps 可能会返回3个结果
        # 因为 step5 可能需要 step2 和 step4 都完成才能执行
        self.assertIn("step1", results)
        self.assertIn("step2", results)
        self.assertIn("step4", results)  # step4 只依赖 step1，所以应该执行
        self.assertTrue(results["step1"])
        self.assertFalse(results["step2"])
        self.assertTrue(results["step4"])

        # 验证步骤状态
        self.assertEqual(self.step1.status, StepStatus.FINISHED)
        self.assertEqual(self.step2.status, StepStatus.FAILED)
        self.assertEqual(self.step3.status, StepStatus.INIT)  # step3 依赖 step2，所以不会执行
        self.assertEqual(self.step4.status, StepStatus.FINISHED)  # step4 只依赖 step1，所以会执行

    def test_execute_steps_parallel(self):
        """测试并行执行步骤"""
        # 将 step1 标记为已完成
        self.step1.update_status(StepStatus.FINISHED)

        # 并行执行 step2 和 step4
        results = execute_steps_parallel(
            self.graph,
            ["step2", "step4"],
            execute_func=self.mock_execute_func,
            merged_var=self.config
        )

        # 验证结果
        self.assertEqual(len(results), 2)
        self.assertTrue(results["step2"])
        self.assertTrue(results["step4"])

        # 验证步骤状态
        self.assertEqual(self.step2.status, StepStatus.FINISHED)
        self.assertEqual(self.step4.status, StepStatus.FINISHED)

    def test_get_flow_var(self):
        """测试获取配置变量"""
        # 创建带有流程名的步骤
        flow_step = Step("flow1.step1", "echo flow_step")

        # 测试步骤级变量
        value = get_flow_var(flow_step, "step_var", self.config)
        self.assertEqual(value, "step_value")

        # 测试流程级变量
        value = get_flow_var(flow_step, "flow_var", self.config)
        self.assertEqual(value, "flow_value")

        # 测试全局变量
        value = get_flow_var(flow_step, "global_var", self.config)
        self.assertEqual(value, "global_value")

        # 测试不存在的变量
        value = get_flow_var(flow_step, "non_existent", self.config, default="default")
        self.assertEqual(value, "default")

    def test_get_status_summary(self):
        """测试获取状态摘要"""
        # 初始状态
        summary = get_status_summary(self.graph)
        self.assertEqual(summary[StepStatus.INIT], 5)
        self.assertEqual(summary[StepStatus.RUNNING], 0)
        self.assertEqual(summary[StepStatus.FINISHED], 0)
        self.assertEqual(summary[StepStatus.SKIPPED], 0)
        self.assertEqual(summary[StepStatus.FAILED], 0)

        # 更新一些步骤状态
        self.step1.update_status(StepStatus.FINISHED)
        self.step2.update_status(StepStatus.RUNNING)
        self.step3.update_status(StepStatus.FAILED)
        self.step4.update_status(StepStatus.SKIPPED)

        # 再次获取状态摘要
        summary = get_status_summary(self.graph)
        self.assertEqual(summary[StepStatus.INIT], 1)
        self.assertEqual(summary[StepStatus.RUNNING], 1)
        self.assertEqual(summary[StepStatus.FINISHED], 1)
        self.assertEqual(summary[StepStatus.SKIPPED], 1)
        self.assertEqual(summary[StepStatus.FAILED], 1)


if __name__ == '__main__':
    unittest.main()
