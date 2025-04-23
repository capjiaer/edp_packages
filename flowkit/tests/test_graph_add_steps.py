"""
测试 Graph 类的 add_step 和 add_steps 方法
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flowkit.step import Step
from flowkit.graph import Graph

def test_add_step():
    """测试 add_step 方法"""
    print("测试 add_step 方法...")
    
    # 创建图
    graph = Graph()
    
    # 创建步骤
    s1 = Step("S1", cmd="command1")
    
    # 添加步骤
    graph.add_step(s1)
    
    # 检查步骤是否已添加
    assert "S1" in graph.steps
    assert graph.steps["S1"] == s1
    
    # 检查依赖关系是否已初始化
    assert "S1" in graph.dependencies
    assert graph.dependencies["S1"]["prev"] == []
    assert graph.dependencies["S1"]["next"] == []
    
    print("add_step 方法测试通过！")
    return graph

def test_add_steps():
    """测试 add_steps 方法"""
    print("\n测试 add_steps 方法...")
    
    # 创建图
    graph = Graph()
    
    # 创建步骤
    s1 = Step("S1", cmd="command1")
    s2 = Step("S2", cmd="command2")
    s3 = Step("S3", cmd="command3")
    
    # 添加步骤
    graph.add_steps([s1, s2, s3])
    
    # 检查步骤是否已添加
    assert "S1" in graph.steps
    assert "S2" in graph.steps
    assert "S3" in graph.steps
    
    # 检查依赖关系是否已初始化
    assert "S1" in graph.dependencies
    assert "S2" in graph.dependencies
    assert "S3" in graph.dependencies
    
    print("add_steps 方法测试通过！")
    return graph

def test_add_dependency():
    """测试添加依赖关系"""
    print("\n测试添加依赖关系...")
    
    # 创建图
    graph = Graph()
    
    # 创建步骤
    s1 = Step("S1", cmd="command1")
    s2 = Step("S2", cmd="command2")
    
    # 添加步骤
    graph.add_steps([s1, s2])
    
    # 添加依赖关系
    graph.add_dependency("S1", "S2")
    
    # 检查依赖关系
    assert "S2" in graph.dependencies["S1"]["next"]
    assert "S1" in graph.dependencies["S2"]["prev"]
    
    # 获取前置和后续步骤
    s1_next = graph.get_next_steps("S1")
    s2_prev = graph.get_prev_steps("S2")
    
    # 检查前置和后续步骤
    assert len(s1_next) == 1 and s1_next[0].name == "S2"
    assert len(s2_prev) == 1 and s2_prev[0].name == "S1"
    
    print("添加依赖关系测试通过！")

def test_chain_calls():
    """测试链式调用"""
    print("\n测试链式调用...")
    
    # 创建图
    graph = Graph()
    
    # 创建步骤
    s1 = Step("S1", cmd="command1")
    s2 = Step("S2", cmd="command2")
    s3 = Step("S3", cmd="command3")
    
    # 链式调用
    graph.add_step(s1).add_step(s2).add_step(s3).add_dependency("S1", "S2").add_dependency("S2", "S3")
    
    # 检查步骤是否已添加
    assert "S1" in graph.steps
    assert "S2" in graph.steps
    assert "S3" in graph.steps
    
    # 检查依赖关系
    assert "S2" in graph.dependencies["S1"]["next"]
    assert "S1" in graph.dependencies["S2"]["prev"]
    assert "S3" in graph.dependencies["S2"]["next"]
    assert "S2" in graph.dependencies["S3"]["prev"]
    
    print("链式调用测试通过！")

def run_all_tests():
    """运行所有测试"""
    test_add_step()
    test_add_steps()
    test_add_dependency()
    test_chain_calls()
    
    print("\n所有测试通过！")

if __name__ == "__main__":
    run_all_tests()
