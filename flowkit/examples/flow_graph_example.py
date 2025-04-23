"""
FlowGraph使用示例

此脚本展示了如何使用FlowGraph类加载YAML配置文件，
构建依赖图，并执行图中的步骤。
"""

import os
import sys
import time
from pathlib import Path

# 添加父目录到路径，以便导入flowkit
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from flowkit.flow_graph import FlowGraph
from flowkit.step import StepStatus


def custom_execute_func(step):
    """
    自定义步骤执行函数
    
    Args:
        step: 要执行的步骤
        
    Returns:
        bool: 执行是否成功
    """
    print(f"正在执行步骤: {step.name}")
    print(f"  命令: {step.cmd}")
    print(f"  输入: {step.inputs}")
    print(f"  输出: {step.outputs}")
    
    # 模拟执行过程
    time.sleep(1)
    
    # 返回执行结果（这里总是成功）
    return True


def main():
    """主函数"""
    # 获取示例YAML文件的路径
    example_yaml = os.path.join('flowkit', 'tests', 'examples', 'example.yaml')
    
    # 创建FlowGraph对象并加载YAML文件
    flow_graph = FlowGraph(yaml_file=example_yaml)
    print(f"加载了 {len(flow_graph.steps)} 个步骤")
    
    # 打印拓扑排序
    topo_order = flow_graph.get_topological_order()
    print("\n步骤执行顺序:")
    for i, step in enumerate(topo_order):
        deps = [dep.name for dep in step.dependencies]
        print(f"{i+1}. {step.name} (依赖: {deps})")
    
    # 获取根步骤（没有依赖的步骤）
    root_steps = flow_graph.get_root_steps()
    print("\n根步骤:")
    for step in root_steps:
        print(f"- {step.name}")
    
    # 获取叶步骤（没有被依赖的步骤）
    leaf_steps = flow_graph.get_leaf_steps()
    print("\n叶步骤:")
    for step in leaf_steps:
        print(f"- {step.name}")
    
    # 执行根步骤
    print("\n开始执行根步骤:")
    for step in root_steps:
        flow_graph.execute_step(step.name, custom_execute_func)
    
    # 获取可运行的步骤
    runnable_steps = flow_graph.get_runnable_steps()
    print("\n现在可以运行的步骤:")
    for step in runnable_steps:
        print(f"- {step.name}")
    
    # 执行所有步骤
    print("\n按拓扑顺序执行所有步骤:")
    for step in topo_order:
        if step.status != StepStatus.FINISHED:
            flow_graph.execute_step(step.name, custom_execute_func)
    
    # 打印状态摘要
    status_summary = flow_graph.get_status_summary()
    print("\n步骤状态摘要:")
    for status, count in status_summary.items():
        print(f"- {status}: {count}")


if __name__ == "__main__":
    main()
