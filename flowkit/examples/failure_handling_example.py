"""
失败处理示例

此脚本展示了如何处理步骤执行失败的情况。
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
    自定义步骤执行函数，某些步骤会故意失败
    
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
    
    # 让特定步骤失败
    if step.name == "dummy":
        print(f"  步骤 {step.name} 执行失败！")
        return False
    
    # 其他步骤成功
    return True


def main():
    """主函数"""
    # 获取示例YAML文件的路径
    example_yaml = os.path.join('flowkit', 'tests', 'examples', 'example.yaml')
    
    # 创建FlowGraph对象并加载YAML文件
    flow_graph = FlowGraph(yaml_file=example_yaml)
    print(f"加载了 {len(flow_graph.steps)} 个步骤")
    
    # 打印依赖关系
    print("\n步骤依赖关系:")
    for step_name, step in flow_graph.steps.items():
        deps = [dep.name for dep in step.dependencies]
        print(f"- {step_name} 依赖于: {deps}")
    
    # 场景1：默认行为 - 不忽略失败的依赖步骤
    print("\n\n场景1：默认行为 - 不忽略失败的依赖步骤")
    flow_graph.reset_all_steps()
    
    # 执行根步骤
    print("\n执行根步骤:")
    root_steps = flow_graph.get_root_steps()
    for step in root_steps:
        success = flow_graph.execute_step(step.name, custom_execute_func)
        print(f"- {step.name}: {'成功' if success else '失败'}")
    
    # 尝试执行下一级步骤
    print("\n尝试执行下一级步骤:")
    next_steps = []
    for step in root_steps:
        for dep_step in step.dependents:
            if dep_step not in next_steps:
                next_steps.append(dep_step)
    
    for step in next_steps:
        success = flow_graph.execute_step(step.name, custom_execute_func)
        print(f"- {step.name}: {'成功' if success else '失败'}")
    
    # 打印状态摘要
    status_summary = flow_graph.get_status_summary()
    print("\n步骤状态摘要:")
    for status, count in status_summary.items():
        print(f"- {status}: {count}")
    
    # 场景2：忽略失败的依赖步骤
    print("\n\n场景2：忽略失败的依赖步骤")
    flow_graph.reset_all_steps()
    
    # 执行根步骤
    print("\n执行根步骤:")
    for step in root_steps:
        success = flow_graph.execute_step(step.name, custom_execute_func)
        print(f"- {step.name}: {'成功' if success else '失败'}")
    
    # 尝试执行下一级步骤，忽略失败的依赖
    print("\n尝试执行下一级步骤（忽略失败的依赖）:")
    for step in next_steps:
        success = flow_graph.execute_step(step.name, custom_execute_func, ignore_failed_deps=True)
        print(f"- {step.name}: {'成功' if success else '失败'}")
    
    # 打印状态摘要
    status_summary = flow_graph.get_status_summary()
    print("\n步骤状态摘要:")
    for status, count in status_summary.items():
        print(f"- {status}: {count}")
    
    # 场景3：使用 execute_all_steps_parallel 并继续执行，即使有步骤失败
    print("\n\n场景3：使用 execute_all_steps_parallel 并继续执行，即使有步骤失败")
    flow_graph.reset_all_steps()
    
    # 执行所有步骤，忽略失败的依赖并继续执行
    print("\n执行所有步骤:")
    results = flow_graph.execute_all_steps_parallel(
        custom_execute_func, 
        ignore_failed_deps=True,
        continue_on_failure=True
    )
    
    # 打印执行结果
    print("\n执行结果:")
    for step_name, success in results.items():
        print(f"- {step_name}: {'成功' if success else '失败'}")
    
    # 打印状态摘要
    status_summary = flow_graph.get_status_summary()
    print("\n步骤状态摘要:")
    for status, count in status_summary.items():
        print(f"- {status}: {count}")


if __name__ == "__main__":
    main()
