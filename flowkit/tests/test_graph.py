"""
测试 Graph 模块

此模块包含对 Graph 类的单元测试。
"""

import unittest
import sys
import os
import tempfile
import yaml

# 添加父目录到 Python 路径，以便能够导入 flowkit 模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from flowkit.graph import Graph
from flowkit.step import Step, StepStatus


class TestGraph(unittest.TestCase):
    """测试 Graph 类"""

    def setUp(self):
        """每个测试前的设置"""
        # 创建一些测试步骤
        self.step1 = Step("step1", "echo step1", ["input1.txt"], ["output1.txt"])
        self.step2 = Step("step2", "echo step2", ["output1.txt"], ["output2.txt"])
        self.step3 = Step("step3", "echo step3", ["output2.txt"], ["output3.txt"])
        self.step4 = Step("step4", "echo step4", ["output1.txt"], ["output4.txt"])
        self.step5 = Step("step5", "echo step5", ["output4.txt", "output2.txt"], ["output5.txt"])
        
        # 手动设置依赖关系
        self.step1.add_next_step(self.step2)  # step1 -> step2
        self.step1.add_next_step(self.step4)  # step1 -> step4
        self.step2.add_next_step(self.step3)  # step2 -> step3
        self.step2.add_next_step(self.step5)  # step2 -> step5
        self.step4.add_next_step(self.step5)  # step4 -> step5
        
        # 创建步骤字典
        self.steps_dict = {
            "step1": self.step1,
            "step2": self.step2,
            "step3": self.step3,
            "step4": self.step4,
            "step5": self.step5
        }
        
        # 创建临时 YAML 文件
        self.temp_files = []
        
        # 创建 YAML 文件内容
        self.yaml_content = {
            'flow': {
                'dependency': {
                    'mode': [
                        {'step1': {'cmd': 'echo step1', 'in': 'input1.txt', 'out': 'output1.txt'}},
                        {'step2': {'cmd': 'echo step2', 'in': 'output1.txt', 'out': 'output2.txt'}},
                        {'step3': {'cmd': 'echo step3', 'in': 'output2.txt', 'out': 'output3.txt'}},
                        {'step4': {'cmd': 'echo step4', 'in': 'output1.txt', 'out': 'output4.txt'}},
                        {'step5': {'cmd': 'echo step5', 'in': ['output4.txt', 'output2.txt'], 'out': 'output5.txt'}}
                    ]
                }
            }
        }
        
        # 创建 YAML 文件
        self.yaml_file = self._create_temp_yaml(self.yaml_content)
        self.temp_files.append(self.yaml_file)

    def tearDown(self):
        """每个测试后的清理"""
        # 删除临时文件
        for temp_file in self.temp_files:
            os.unlink(temp_file)

    def _create_temp_yaml(self, content):
        """创建临时 YAML 文件"""
        fd, path = tempfile.mkstemp(suffix='.yaml')
        with os.fdopen(fd, 'w') as f:
            yaml.dump(content, f)
        return path

    def test_init_with_steps_dict(self):
        """测试使用步骤字典初始化图"""
        graph = Graph(steps_dict=self.steps_dict)
        
        # 验证步骤数量
        self.assertEqual(len(graph.steps), 5)
        
        # 验证步骤对象
        self.assertIn("step1", graph.steps)
        self.assertIn("step2", graph.steps)
        self.assertIn("step3", graph.steps)
        self.assertIn("step4", graph.steps)
        self.assertIn("step5", graph.steps)
        
        # 验证依赖关系
        self.assertIn(self.step2, self.step1.next_steps)
        self.assertIn(self.step4, self.step1.next_steps)
        self.assertIn(self.step3, self.step2.next_steps)
        self.assertIn(self.step5, self.step2.next_steps)
        self.assertIn(self.step5, self.step4.next_steps)
        
        self.assertIn(self.step1, self.step2.prev_steps)
        self.assertIn(self.step1, self.step4.prev_steps)
        self.assertIn(self.step2, self.step3.prev_steps)
        self.assertIn(self.step2, self.step5.prev_steps)
        self.assertIn(self.step4, self.step5.prev_steps)

    def test_init_with_yaml_file(self):
        """测试使用 YAML 文件初始化图"""
        graph = Graph(yaml_files=self.yaml_file)
        
        # 验证步骤数量
        self.assertEqual(len(graph.steps), 5)
        
        # 验证步骤对象
        self.assertIn("step1", graph.steps)
        self.assertIn("step2", graph.steps)
        self.assertIn("step3", graph.steps)
        self.assertIn("step4", graph.steps)
        self.assertIn("step5", graph.steps)
        
        # 验证依赖关系
        step1 = graph.steps["step1"]
        step2 = graph.steps["step2"]
        step3 = graph.steps["step3"]
        step4 = graph.steps["step4"]
        step5 = graph.steps["step5"]
        
        self.assertIn(step2, step1.next_steps)
        self.assertIn(step4, step1.next_steps)
        self.assertIn(step3, step2.next_steps)
        self.assertIn(step5, step2.next_steps)
        self.assertIn(step5, step4.next_steps)
        
        self.assertIn(step1, step2.prev_steps)
        self.assertIn(step1, step4.prev_steps)
        self.assertIn(step2, step3.prev_steps)
        self.assertIn(step2, step5.prev_steps)
        self.assertIn(step4, step5.prev_steps)

    def test_build_graph_from_yaml(self):
        """测试从 YAML 文件构建图"""
        graph = Graph()
        graph.build_graph_from_yaml(self.yaml_file)
        
        # 验证步骤数量
        self.assertEqual(len(graph.steps), 5)
        
        # 验证步骤对象
        self.assertIn("step1", graph.steps)
        self.assertIn("step2", graph.steps)
        self.assertIn("step3", graph.steps)
        self.assertIn("step4", graph.steps)
        self.assertIn("step5", graph.steps)

    def test_load_from_yaml(self):
        """测试兼容性方法 load_from_yaml"""
        graph = Graph()
        graph.load_from_yaml(self.yaml_file)
        
        # 验证步骤数量
        self.assertEqual(len(graph.steps), 5)
        
        # 验证步骤对象
        self.assertIn("step1", graph.steps)
        self.assertIn("step2", graph.steps)
        self.assertIn("step3", graph.steps)
        self.assertIn("step4", graph.steps)
        self.assertIn("step5", graph.steps)

    def test_get_root_steps(self):
        """测试获取根步骤"""
        graph = Graph(steps_dict=self.steps_dict)
        root_steps = graph.get_root_steps()
        
        # 只有 step1 是根步骤
        self.assertEqual(len(root_steps), 1)
        self.assertEqual(root_steps[0].id, "step1")

    def test_get_leaf_steps(self):
        """测试获取叶步骤"""
        graph = Graph(steps_dict=self.steps_dict)
        leaf_steps = graph.get_leaf_steps()
        
        # step3 和 step5 是叶步骤
        self.assertEqual(len(leaf_steps), 2)
        leaf_ids = [step.id for step in leaf_steps]
        self.assertIn("step3", leaf_ids)
        self.assertIn("step5", leaf_ids)

    def test_get_ready_steps(self):
        """测试获取可执行步骤"""
        graph = Graph(steps_dict=self.steps_dict)
        ready_steps = graph.get_ready_steps()
        
        # 只有 step1 是可执行步骤
        self.assertEqual(len(ready_steps), 1)
        self.assertEqual(ready_steps[0], "step1")
        
        # 将 step1 标记为已完成
        self.step1.update_status(StepStatus.FINISHED)
        ready_steps = graph.get_ready_steps()
        
        # 现在 step2 和 step4 是可执行步骤
        self.assertEqual(len(ready_steps), 2)
        self.assertIn("step2", ready_steps)
        self.assertIn("step4", ready_steps)
        
        # 将 step2 标记为已跳过
        self.step2.update_status(StepStatus.SKIPPED)
        ready_steps = graph.get_ready_steps()
        
        # 现在 step3 和 step4 是可执行步骤
        self.assertEqual(len(ready_steps), 2)
        self.assertIn("step3", ready_steps)
        self.assertIn("step4", ready_steps)

    def test_topological_sort(self):
        """测试拓扑排序"""
        graph = Graph(steps_dict=self.steps_dict)
        sorted_steps = graph.topological_sort()
        
        # 验证排序结果
        self.assertEqual(len(sorted_steps), 5)
        
        # 验证顺序约束
        # step1 必须在 step2 和 step4 之前
        # step2 必须在 step3 和 step5 之前
        # step4 必须在 step5 之前
        step1_idx = sorted_steps.index(self.step1)
        step2_idx = sorted_steps.index(self.step2)
        step3_idx = sorted_steps.index(self.step3)
        step4_idx = sorted_steps.index(self.step4)
        step5_idx = sorted_steps.index(self.step5)
        
        self.assertLess(step1_idx, step2_idx)
        self.assertLess(step1_idx, step4_idx)
        self.assertLess(step2_idx, step3_idx)
        self.assertLess(step2_idx, step5_idx)
        self.assertLess(step4_idx, step5_idx)

    def test_topological_sort_with_cycle(self):
        """测试带有循环依赖的拓扑排序"""
        # 创建循环依赖
        self.step3.add_next_step(self.step1)  # 添加 step3 -> step1，形成循环
        
        graph = Graph(steps_dict=self.steps_dict)
        
        # 拓扑排序应该抛出异常
        with self.assertRaises(ValueError):
            graph.topological_sort()

    def test_get_specific_step(self):
        """测试获取特定步骤"""
        graph = Graph(steps_dict=self.steps_dict)
        
        # 获取存在的步骤
        step = graph.get_specific_step("step1")
        self.assertEqual(step, self.step1)
        
        # 获取不存在的步骤
        step = graph.get_specific_step("non_existent")
        self.assertIsNone(step)

    def test_getitem(self):
        """测试 __getitem__ 方法"""
        graph = Graph(steps_dict=self.steps_dict)
        
        # 使用 [] 操作符获取步骤
        self.assertEqual(graph["step1"], self.step1)
        self.assertEqual(graph["step2"], self.step2)
        
        # 获取不存在的步骤
        self.assertIsNone(graph["non_existent"])

    def test_contains(self):
        """测试 __contains__ 方法"""
        graph = Graph(steps_dict=self.steps_dict)
        
        # 使用 in 操作符检查步骤是否存在
        self.assertTrue("step1" in graph)
        self.assertTrue("step2" in graph)
        self.assertFalse("non_existent" in graph)

    def test_len(self):
        """测试 __len__ 方法"""
        graph = Graph(steps_dict=self.steps_dict)
        
        # 使用 len() 获取步骤数量
        self.assertEqual(len(graph), 5)

    def test_iter(self):
        """测试 __iter__ 方法"""
        graph = Graph(steps_dict=self.steps_dict)
        
        # 使用 for 循环迭代步骤名称
        step_names = list(graph)
        self.assertEqual(len(step_names), 5)
        self.assertIn("step1", step_names)
        self.assertIn("step2", step_names)
        self.assertIn("step3", step_names)
        self.assertIn("step4", step_names)
        self.assertIn("step5", step_names)

    def test_get_all_stepsdict(self):
        """测试获取所有步骤字典"""
        graph = Graph(steps_dict=self.steps_dict)
        
        # 获取步骤字典
        steps_dict = dict(graph.get_all_stepsdict())
        self.assertEqual(len(steps_dict), 5)
        self.assertEqual(steps_dict["step1"], self.step1)
        self.assertEqual(steps_dict["step2"], self.step2)
        self.assertEqual(steps_dict["step3"], self.step3)
        self.assertEqual(steps_dict["step4"], self.step4)
        self.assertEqual(steps_dict["step5"], self.step5)

    def test_get_all_stepsinfo(self):
        """测试获取所有步骤信息"""
        graph = Graph(steps_dict=self.steps_dict)
        
        # 获取步骤信息
        steps_info = list(graph.get_all_stepsinfo())
        self.assertEqual(len(steps_info), 5)
        self.assertIn(self.step1, steps_info)
        self.assertIn(self.step2, steps_info)
        self.assertIn(self.step3, steps_info)
        self.assertIn(self.step4, steps_info)
        self.assertIn(self.step5, steps_info)

    def test_get_all_stepsname(self):
        """测试获取所有步骤名称"""
        graph = Graph(steps_dict=self.steps_dict)
        
        # 获取步骤名称
        steps_name = list(graph.get_all_stepsname())
        self.assertEqual(len(steps_name), 5)
        self.assertIn("step1", steps_name)
        self.assertIn("step2", steps_name)
        self.assertIn("step3", steps_name)
        self.assertIn("step4", steps_name)
        self.assertIn("step5", steps_name)

    def test_get_intersection_graph(self):
        """测试获取图的交集"""
        # 创建第一个图
        graph1 = Graph(steps_dict={
            "step1": self.step1,
            "step2": self.step2,
            "step3": self.step3
        })
        
        # 创建第二个图
        graph2 = Graph(steps_dict={
            "step2": self.step2,
            "step3": self.step3,
            "step4": self.step4
        })
        
        # 获取交集
        intersection = graph1.get_intersection_graph(graph2)
        
        # 验证交集
        self.assertEqual(len(intersection.steps), 2)
        self.assertIn("step2", intersection.steps)
        self.assertIn("step3", intersection.steps)
        self.assertNotIn("step1", intersection.steps)
        self.assertNotIn("step4", intersection.steps)

    def test_get_union_graph(self):
        """测试获取图的并集"""
        # 创建第一个图
        graph1 = Graph(steps_dict={
            "step1": self.step1,
            "step2": self.step2
        })
        
        # 创建第二个图
        graph2 = Graph(steps_dict={
            "step3": self.step3,
            "step4": self.step4
        })
        
        # 获取并集
        union = graph1.get_union_graph(graph2)
        
        # 验证并集
        self.assertEqual(len(union.steps), 4)
        self.assertIn("step1", union.steps)
        self.assertIn("step2", union.steps)
        self.assertIn("step3", union.steps)
        self.assertIn("step4", union.steps)

    def test_get_subgraph_after(self):
        """测试获取节点之后的子图"""
        graph = Graph(steps_dict=self.steps_dict)
        
        # 获取 step2 之后的子图
        subgraph = graph.get_subgraph_after("step2")
        
        # 验证子图
        self.assertEqual(len(subgraph.steps), 3)
        self.assertIn("step2", subgraph.steps)
        self.assertIn("step3", subgraph.steps)
        self.assertIn("step5", subgraph.steps)
        self.assertNotIn("step1", subgraph.steps)
        self.assertNotIn("step4", subgraph.steps)
        
        # 测试不存在的步骤
        with self.assertRaises(ValueError):
            graph.get_subgraph_after("non_existent")

    def test_get_subgraph_before(self):
        """测试获取节点之前的子图"""
        graph = Graph(steps_dict=self.steps_dict)
        
        # 获取 step5 之前的子图
        subgraph = graph.get_subgraph_before("step5")
        
        # 验证子图
        self.assertEqual(len(subgraph.steps), 4)
        self.assertIn("step1", subgraph.steps)
        self.assertIn("step2", subgraph.steps)
        self.assertIn("step4", subgraph.steps)
        self.assertIn("step5", subgraph.steps)
        self.assertNotIn("step3", subgraph.steps)
        
        # 测试不存在的步骤
        with self.assertRaises(ValueError):
            graph.get_subgraph_before("non_existent")

    def test_get_subgraph_between(self):
        """测试获取两个节点之间的子图"""
        graph = Graph(steps_dict=self.steps_dict)
        
        # 获取 step1 和 step3 之间的子图
        subgraph = graph.get_subgraph_between("step1", "step3")
        
        # 验证子图
        self.assertEqual(len(subgraph.steps), 3)
        self.assertIn("step1", subgraph.steps)
        self.assertIn("step2", subgraph.steps)
        self.assertIn("step3", subgraph.steps)
        self.assertNotIn("step4", subgraph.steps)
        self.assertNotIn("step5", subgraph.steps)
        
        # 测试不存在的路径
        with self.assertRaises(ValueError):
            graph.get_subgraph_between("step4", "step3")
        
        # 测试不存在的步骤
        with self.assertRaises(ValueError):
            graph.get_subgraph_between("step1", "non_existent")

    def test_get_subgraph_after_greedy(self):
        """测试贪婪模式获取节点之后的子图"""
        # 创建一个更复杂的图
        step6 = Step("step6", "echo step6", ["output3.txt"], ["output6.txt"])
        step7 = Step("step7", "echo step7", ["output5.txt", "output6.txt"], ["output7.txt"])
        
        # 设置依赖关系
        self.step3.add_next_step(step6)  # step3 -> step6
        self.step5.add_next_step(step7)  # step5 -> step7
        step6.add_next_step(step7)       # step6 -> step7
        
        steps_dict = {
            "step1": self.step1,
            "step2": self.step2,
            "step3": self.step3,
            "step4": self.step4,
            "step5": self.step5,
            "step6": step6,
            "step7": step7
        }
        
        graph = Graph(steps_dict=steps_dict)
        
        # 获取 step2 之后的子图（贪婪模式）
        subgraph = graph.get_subgraph_after_greedy("step2")
        
        # 验证子图
        self.assertEqual(len(subgraph.steps), 5)
        self.assertIn("step2", subgraph.steps)
        self.assertIn("step3", subgraph.steps)
        self.assertIn("step5", subgraph.steps)
        self.assertIn("step6", subgraph.steps)
        self.assertIn("step7", subgraph.steps)
        self.assertNotIn("step1", subgraph.steps)
        self.assertNotIn("step4", subgraph.steps)
        
        # 测试不存在的步骤
        with self.assertRaises(ValueError):
            graph.get_subgraph_after_greedy("non_existent")

    def test_get_subgraph_between_greedy(self):
        """测试贪婪模式获取两个节点之间的子图"""
        # 创建一个更复杂的图
        step6 = Step("step6", "echo step6", ["output3.txt"], ["output6.txt"])
        step7 = Step("step7", "echo step7", ["output5.txt", "output6.txt"], ["output7.txt"])
        
        # 设置依赖关系
        self.step3.add_next_step(step6)  # step3 -> step6
        self.step5.add_next_step(step7)  # step5 -> step7
        step6.add_next_step(step7)       # step6 -> step7
        
        steps_dict = {
            "step1": self.step1,
            "step2": self.step2,
            "step3": self.step3,
            "step4": self.step4,
            "step5": self.step5,
            "step6": step6,
            "step7": step7
        }
        
        graph = Graph(steps_dict=steps_dict)
        
        # 获取 step2 和 step7 之间的子图（贪婪模式）
        subgraph = graph.get_subgraph_between_greedy("step2", "step7")
        
        # 验证子图
        self.assertEqual(len(subgraph.steps), 5)
        self.assertIn("step2", subgraph.steps)
        self.assertIn("step3", subgraph.steps)
        self.assertIn("step5", subgraph.steps)
        self.assertIn("step6", subgraph.steps)
        self.assertIn("step7", subgraph.steps)
        self.assertNotIn("step1", subgraph.steps)
        self.assertNotIn("step4", subgraph.steps)
        
        # 测试不存在的路径
        with self.assertRaises(ValueError):
            graph.get_subgraph_between_greedy("step4", "step6")
        
        # 测试不存在的步骤
        with self.assertRaises(ValueError):
            graph.get_subgraph_between_greedy("step1", "non_existent")


if __name__ == '__main__':
    unittest.main()
