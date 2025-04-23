"""
并行执行示例

此脚本展示了如何使用FlowGraph类并行执行步骤。
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
    
    # 模拟执行过程，根据步骤名称设置不同的执行时间
    sleep_time = 1
    if step.name == "ipmerge":
        sleep_time = 2
    elif step.name == "dummy":
        sleep_time = 1
    else:
        sleep_time = 3
    
    print(f"  执行时间: {sleep_time}秒")
    time.sleep(sleep_time)
    
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
    
    # 并行执行根步骤
    print("\n并行执行根步骤:")
    root_step_names = [step.name for step in root_steps]
    results = flow_graph.execute_steps_parallel(root_step_names, custom_execute_func)
    
    # 打印执行结果
    print("\n根步骤执行结果:")
    for step_name, success in results.items():
        print(f"- {step_name}: {'成功' if success else '失败'}")
    
    # 获取可运行的步骤
    runnable_steps = flow_graph.get_runnable_steps()
    print("\n现在可以运行的步骤:")
    for step in runnable_steps:
        print(f"- {step.name}")
    
    # 并行执行可运行的步骤
    print("\n并行执行可运行的步骤:")
    results = flow_graph.execute_runnable_steps_parallel(custom_execute_func)
    
    # 打印执行结果
    print("\n可运行步骤执行结果:")
    for step_name, success in results.items():
        print(f"- {step_name}: {'成功' if success else '失败'}")
    
    # 重置所有步骤状态
    flow_graph.reset_all_steps()
    
    # 按拓扑顺序并行执行所有步骤
    print("\n按拓扑顺序并行执行所有步骤:")
    start_time = time.time()
    results = flow_graph.execute_all_steps_parallel(custom_execute_func)
    end_time = time.time()
    
    # 打印执行结果
    print("\n所有步骤执行结果:")
    for step_name, success in results.items():
        print(f"- {step_name}: {'成功' if success else '失败'}")
    
    # 打印总执行时间
    print(f"\n总执行时间: {end_time - start_time:.2f}秒")
    
    # 打印状态摘要
    status_summary = flow_graph.get_status_summary()
    print("\n步骤状态摘要:")
    for status, count in status_summary.items():
        print(f"- {status}: {count}")


if __name__ == "__main__":
    main()
