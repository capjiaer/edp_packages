"""
测试 Step 类和 Graph 类的重构
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flowkit.step import Step, StepStatus
from flowkit.graph import Graph

def test_step_creation():
    """测试 Step 类的创建"""
    print("测试 Step 类的创建...")
    
    # 创建步骤
    s1 = Step("S1", cmd="command1", inputs=["input1.txt"], outputs=["output1.txt"])
    s2 = Step("S2", cmd="command2", inputs=["output1.txt"], outputs=["output2.txt"])
    s3 = Step("S3", cmd="command3", inputs=["output2.txt"], outputs=["output3.txt"])
    
    # 检查步骤属性
    assert s1.name == "S1"
    assert s1.cmd == "command1"
    assert s1.inputs == ["input1.txt"]
    assert s1.outputs == ["output1.txt"]
    assert s1.status == StepStatus.INIT
    
    print("Step 类创建测试通过！")
    return s1, s2, s3

def test_graph_creation(s1, s2, s3):
    """测试 Graph 类的创建"""
    print("\n测试 Graph 类的创建...")
    
    # 创建图
    steps_dict = {
        "S1": s1,
        "S2": s2,
        "S3": s3
    }
    graph = Graph(steps_dict=steps_dict)
    
    # 检查图属性
    assert len(graph.steps) == 3
    assert "S1" in graph.steps
    assert "S2" in graph.steps
    assert "S3" in graph.steps
    
    # 检查依赖关系是否已初始化
    assert "S1" in graph.dependencies
    assert "S2" in graph.dependencies
    assert "S3" in graph.dependencies
    
    print("Graph 类创建测试通过！")
    return graph

def test_dependency_building(graph):
    """测试依赖关系的构建"""
    print("\n测试依赖关系的构建...")
    
    # 构建依赖关系
    graph._build_dependency_graph()
    
    # 检查依赖关系
    assert "S2" in graph.dependencies["S1"]["next"]
    assert "S1" in graph.dependencies["S2"]["prev"]
    assert "S3" in graph.dependencies["S2"]["next"]
    assert "S2" in graph.dependencies["S3"]["prev"]
    
    print("依赖关系构建测试通过！")

def test_get_prev_next_steps(graph):
    """测试获取前置和后续步骤"""
    print("\n测试获取前置和后续步骤...")
    
    # 获取前置步骤
    s1_prev = graph.get_prev_steps("S1")
    s2_prev = graph.get_prev_steps("S2")
    s3_prev = graph.get_prev_steps("S3")
    
    # 获取后续步骤
    s1_next = graph.get_next_steps("S1")
    s2_next = graph.get_next_steps("S2")
    s3_next = graph.get_next_steps("S3")
    
    # 检查前置步骤
    assert len(s1_prev) == 0
    assert len(s2_prev) == 1 and s2_prev[0].name == "S1"
    assert len(s3_prev) == 1 and s3_prev[0].name == "S2"
    
    # 检查后续步骤
    assert len(s1_next) == 1 and s1_next[0].name == "S2"
    assert len(s2_next) == 1 and s2_next[0].name == "S3"
    assert len(s3_next) == 0
    
    print("获取前置和后续步骤测试通过！")

def test_root_leaf_steps(graph):
    """测试获取根步骤和叶步骤"""
    print("\n测试获取根步骤和叶步骤...")
    
    # 获取根步骤和叶步骤
    root_steps = graph.get_root_steps()
    leaf_steps = graph.get_leaf_steps()
    
    # 检查根步骤和叶步骤
    assert len(root_steps) == 1 and root_steps[0].name == "S1"
    assert len(leaf_steps) == 1 and leaf_steps[0].name == "S3"
    
    print("获取根步骤和叶步骤测试通过！")

def test_ready_steps(graph):
    """测试获取可运行的步骤"""
    print("\n测试获取可运行的步骤...")
    
    # 获取可运行的步骤
    ready_steps = graph.get_ready_steps()
    
    # 检查可运行的步骤
    assert len(ready_steps) == 1 and ready_steps[0].name == "S1"
    
    # 将 S1 标记为已完成
    graph.steps["S1"].status = StepStatus.FINISHED
    
    # 再次获取可运行的步骤
    ready_steps = graph.get_ready_steps()
    
    # 检查可运行的步骤
    assert len(ready_steps) == 1 and ready_steps[0].name == "S2"
    
    print("获取可运行的步骤测试通过！")

def test_topological_sort(graph):
    """测试拓扑排序"""
    print("\n测试拓扑排序...")
    
    # 重置所有步骤状态
    graph.reset_all_steps()
    
    # 拓扑排序
    sorted_steps = graph.topological_sort()
    
    # 检查排序结果
    assert len(sorted_steps) == 3
    assert sorted_steps[0].name == "S1"
    assert sorted_steps[1].name == "S2"
    assert sorted_steps[2].name == "S3"
    
    print("拓扑排序测试通过！")

def test_subgraph(graph):
    """测试子图"""
    print("\n测试子图...")
    
    # 获取 S2 之后的子图
    subgraph_after = graph.get_subgraph_after("S2")
    
    # 检查子图
    assert len(subgraph_after.steps) == 2
    assert "S2" in subgraph_after.steps
    assert "S3" in subgraph_after.steps
    
    # 获取 S2 之前的子图
    subgraph_before = graph.get_subgraph_before("S2")
    
    # 检查子图
    assert len(subgraph_before.steps) == 2
    assert "S1" in subgraph_before.steps
    assert "S2" in subgraph_before.steps
    
    print("子图测试通过！")

def test_add_dependency(graph):
    """测试添加依赖关系"""
    print("\n测试添加依赖关系...")
    
    # 创建新步骤
    s4 = Step("S4", cmd="command4", inputs=["output3.txt"], outputs=["output4.txt"])
    graph.steps["S4"] = s4
    graph._init_dependencies()  # 初始化依赖关系
    
    # 添加依赖关系
    graph.add_dependency("S3", "S4")
    
    # 检查依赖关系
    assert "S4" in graph.dependencies["S3"]["next"]
    assert "S3" in graph.dependencies["S4"]["prev"]
    
    # 获取前置和后续步骤
    s3_next = graph.get_next_steps("S3")
    s4_prev = graph.get_prev_steps("S4")
    
    # 检查前置和后续步骤
    assert len(s3_next) == 1 and s3_next[0].name == "S4"
    assert len(s4_prev) == 1 and s4_prev[0].name == "S3"
    
    print("添加依赖关系测试通过！")

def test_complex_graph():
    """测试复杂图"""
    print("\n测试复杂图...")
    
    # 创建步骤
    s1 = Step("S1", cmd="command1")
    s2 = Step("S2", cmd="command2")
    s3 = Step("S3", cmd="command3")
    s4 = Step("S4", cmd="command4")
    s5 = Step("S5", cmd="command5")
    
    # 创建图
    steps_dict = {
        "S1": s1,
        "S2": s2,
        "S3": s3,
        "S4": s4,
        "S5": s5
    }
    graph = Graph(steps_dict=steps_dict)
    
    # 添加依赖关系
    graph.add_dependency("S1", "S2")
    graph.add_dependency("S1", "S3")
    graph.add_dependency("S2", "S4")
    graph.add_dependency("S3", "S4")
    graph.add_dependency("S4", "S5")
    
    # 检查依赖关系
    assert set(graph.dependencies["S1"]["next"]) == {"S2", "S3"}
    assert set(graph.dependencies["S2"]["prev"]) == {"S1"}
    assert set(graph.dependencies["S3"]["prev"]) == {"S1"}
    assert set(graph.dependencies["S4"]["prev"]) == {"S2", "S3"}
    assert set(graph.dependencies["S5"]["prev"]) == {"S4"}
    
    # 拓扑排序
    sorted_steps = graph.topological_sort()
    
    # 检查排序结果
    assert len(sorted_steps) == 5
    assert sorted_steps[0].name == "S1"
    assert sorted_steps[1].name in ["S2", "S3"]
    assert sorted_steps[2].name in ["S2", "S3"]
    assert sorted_steps[3].name == "S4"
    assert sorted_steps[4].name == "S5"
    
    print("复杂图测试通过！")

def run_all_tests():
    """运行所有测试"""
    s1, s2, s3 = test_step_creation()
    graph = test_graph_creation(s1, s2, s3)
    test_dependency_building(graph)
    test_get_prev_next_steps(graph)
    test_root_leaf_steps(graph)
    test_ready_steps(graph)
    test_topological_sort(graph)
    test_subgraph(graph)
    test_add_dependency(graph)
    test_complex_graph()
    
    print("\n所有测试通过！")

if __name__ == "__main__":
    run_all_tests()
