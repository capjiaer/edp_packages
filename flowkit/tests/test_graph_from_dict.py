"""
测试 Graph 类的 build_graph_from_dict 方法
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flowkit.step import Step
from flowkit.graph import Graph
from flowkit.parser import yaml2dict

def test_build_graph_from_dict():
    """测试从字典构建图"""
    print("测试从字典构建图...")
    
    # 创建一个字典，模拟从 YAML 文件解析得到的数据
    data = {
        "flow1": {
            "dependency": {
                "mode1": [
                    {
                        "S1": {
                            "cmd": "command1",
                            "in": "input1.txt",
                            "out": "output1.txt"
                        }
                    },
                    {
                        "S2": {
                            "cmd": "command2",
                            "in": "output1.txt",
                            "out": "output2.txt"
                        }
                    }
                ]
            }
        }
    }
    
    # 创建图
    graph = Graph()
    graph.build_graph_from_dict(data)
    
    # 检查步骤是否已添加
    assert "S1" in graph.steps
    assert "S2" in graph.steps
    
    # 检查依赖关系
    assert "S2" in graph.dependencies["S1"]["next"]
    assert "S1" in graph.dependencies["S2"]["prev"]
    
    print("从字典构建图测试通过！")
    return graph

def test_merge_multiple_dicts():
    """测试合并多个字典构建图"""
    print("\n测试合并多个字典构建图...")
    
    # 创建第一个字典
    data1 = {
        "flow1": {
            "dependency": {
                "mode1": [
                    {
                        "S1": {
                            "cmd": "command1",
                            "in": "input1.txt",
                            "out": "output1.txt"
                        }
                    }
                ]
            }
        }
    }
    
    # 创建第二个字典
    data2 = {
        "flow1": {
            "dependency": {
                "mode1": [
                    {
                        "S2": {
                            "cmd": "command2",
                            "in": "output1.txt",
                            "out": "output2.txt"
                        }
                    }
                ]
            }
        }
    }
    
    # 创建第三个字典
    data3 = {
        "flow2": {
            "dependency": {
                "mode1": [
                    {
                        "S3": {
                            "cmd": "command3",
                            "in": "output2.txt",
                            "out": "output3.txt"
                        }
                    }
                ]
            }
        }
    }
    
    # 创建图
    graph = Graph()
    
    # 依次添加字典
    graph.build_graph_from_dict(data1)
    graph.build_graph_from_dict(data2)
    graph.build_graph_from_dict(data3)
    
    # 检查步骤是否已添加
    assert "S1" in graph.steps
    assert "S2" in graph.steps
    assert "S3" in graph.steps
    
    # 检查依赖关系
    assert "S2" in graph.dependencies["S1"]["next"]
    assert "S1" in graph.dependencies["S2"]["prev"]
    assert "S3" in graph.dependencies["S2"]["next"]
    assert "S2" in graph.dependencies["S3"]["prev"]
    
    print("合并多个字典构建图测试通过！")
    return graph

def test_build_graph_from_yaml():
    """测试从 YAML 文件构建图"""
    print("\n测试从 YAML 文件构建图...")
    
    # 创建临时 YAML 文件
    with open("test_flow1.yaml", "w") as f:
        f.write("""
flow1:
  dependency:
    mode1:
      - S1:
          cmd: command1
          in: input1.txt
          out: output1.txt
      - S2:
          cmd: command2
          in: output1.txt
          out: output2.txt
        """)
    
    with open("test_flow2.yaml", "w") as f:
        f.write("""
flow2:
  dependency:
    mode1:
      - S3:
          cmd: command3
          in: output2.txt
          out: output3.txt
        """)
    
    # 创建图
    graph = Graph()
    graph.build_graph_from_yaml(["test_flow1.yaml", "test_flow2.yaml"])
    
    # 检查步骤是否已添加
    assert "S1" in graph.steps
    assert "S2" in graph.steps
    assert "S3" in graph.steps
    
    # 检查依赖关系
    assert "S2" in graph.dependencies["S1"]["next"]
    assert "S1" in graph.dependencies["S2"]["prev"]
    assert "S3" in graph.dependencies["S2"]["next"]
    assert "S2" in graph.dependencies["S3"]["prev"]
    
    # 清理临时文件
    os.remove("test_flow1.yaml")
    os.remove("test_flow2.yaml")
    
    print("从 YAML 文件构建图测试通过！")
    return graph

def test_yaml2dict_and_build_graph():
    """测试使用 yaml2dict 和 build_graph_from_dict 构建图"""
    print("\n测试使用 yaml2dict 和 build_graph_from_dict 构建图...")
    
    # 创建临时 YAML 文件
    with open("test_flow1.yaml", "w") as f:
        f.write("""
flow1:
  dependency:
    mode1:
      - S1:
          cmd: command1
          in: input1.txt
          out: output1.txt
      - S2:
          cmd: command2
          in: output1.txt
          out: output2.txt
        """)
    
    with open("test_flow2.yaml", "w") as f:
        f.write("""
flow2:
  dependency:
    mode1:
      - S3:
          cmd: command3
          in: output2.txt
          out: output3.txt
        """)
    
    # 使用 yaml2dict 解析 YAML 文件
    data = yaml2dict(["test_flow1.yaml", "test_flow2.yaml"])
    
    # 创建图
    graph = Graph()
    graph.build_graph_from_dict(data)
    
    # 检查步骤是否已添加
    assert "S1" in graph.steps
    assert "S2" in graph.steps
    assert "S3" in graph.steps
    
    # 检查依赖关系
    assert "S2" in graph.dependencies["S1"]["next"]
    assert "S1" in graph.dependencies["S2"]["prev"]
    assert "S3" in graph.dependencies["S2"]["next"]
    assert "S2" in graph.dependencies["S3"]["prev"]
    
    # 清理临时文件
    os.remove("test_flow1.yaml")
    os.remove("test_flow2.yaml")
    
    print("使用 yaml2dict 和 build_graph_from_dict 构建图测试通过！")
    return graph

def run_all_tests():
    """运行所有测试"""
    test_build_graph_from_dict()
    test_merge_multiple_dicts()
    test_build_graph_from_yaml()
    test_yaml2dict_and_build_graph()
    
    print("\n所有测试通过！")

if __name__ == "__main__":
    run_all_tests()
