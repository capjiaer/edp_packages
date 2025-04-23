#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试IC命令执行器
"""

import os
import logging
from flowkit.parser import yaml2dict
from flowkit.graph import Graph
from flowkit.step import Step, StepStatus
from flowkit.run_graph import execute_step, execute_all_steps, get_status_summary, setup_logging
from flowkit.ICCommandExecutor import ICCommandExecutor

# 设置日志
setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建基础目录
base_dir = os.path.join(os.getcwd(), "test_project")
os.makedirs(base_dir, exist_ok=True)

def test_simple_commands():
    """测试简单命令执行"""
    print("\n=== 测试简单命令执行 ===")

    # 创建步骤
    step1 = Step("test_flow.echo_test", "echo 'Hello, IC Design!' > ${RUNS_DIR}/output.txt", [], ["output.txt"])
    step2 = Step("test_flow.ls_test", "ls -la ${RUNS_DIR} > ${RPTS_DIR}/ls_output.txt", ["output.txt"], ["ls_output.txt"])

    # 创建图
    steps_dict = {
        "test_flow.echo_test": step1,
        "test_flow.ls_test": step2
    }
    graph = Graph(steps_dict=steps_dict)

    # 创建执行器
    config = {
        "timeout": 30,
        "test_flow": {
            "echo_test": {
                "timeout": 10
            }
        }
    }
    executor = ICCommandExecutor(base_dir, config)

    # 执行所有步骤
    print("执行所有步骤...")
    results = execute_all_steps(graph, execute_func=executor.run_cmd, merged_var=config)

    # 打印结果
    print("执行结果:", results)
    print("最终状态:", get_status_summary(graph))

    return results

def test_lsf_simulation():
    """测试LSF模拟（演示模式）"""
    print("\n=== 测试LSF模拟（演示模式）===")

    # 创建步骤
    step1 = Step("pnr_innovus.synthesis", "genus -f ${CMDS_DIR}/syn.tcl", [], ["syn.v"])
    step2 = Step("pnr_innovus.place_route", "innovus -f ${CMDS_DIR}/pr.tcl", ["syn.v"], ["layout.def"])

    # 创建图
    steps_dict = {
        "pnr_innovus.synthesis": step1,
        "pnr_innovus.place_route": step2
    }
    graph = Graph(steps_dict=steps_dict)

    # 创建配置
    config = {
        "use_lsf": True,
        "lsf_queue": "normal",
        "lsf_memory": "8G",
        "lsf_cores": 4,
        "pnr_innovus": {
            "synthesis": {
                "lsf_memory": "16G"
            }
        }
    }

    # 创建执行器（演示模式）
    executor = ICCommandExecutor(base_dir, config, dry_run=True)

    # 执行所有步骤
    print("执行所有步骤（演示模式）...")
    results = execute_all_steps(graph, execute_func=executor.run_cmd, merged_var=config)

    # 打印结果
    print("执行结果:", results)
    print("最终状态:", get_status_summary(graph))

    return results

def test_retry_mechanism():
    """测试重试机制"""
    print("\n=== 测试重试机制 ===")

    # 创建一个会失败的步骤
    fail_step = Step("test_flow.fail_test", "exit 1", [], [])

    # 创建图
    graph = Graph(steps_dict={"test_flow.fail_test": fail_step})

    # 创建执行器
    executor = ICCommandExecutor(base_dir)

    # 使用重试机制执行步骤
    print("执行步骤（带重试）...")
    success = executor.execute_with_retry(fail_step, {}, max_retries=2, retry_interval=1)

    # 打印结果
    print("执行结果:", success)
    print("步骤状态:", fail_step.status)

    return success

def main():
    """主函数"""
    print("开始测试IC命令执行器...")

    test_simple_commands()
    test_lsf_simulation()
    test_retry_mechanism()

    print("\n所有测试完成!")

if __name__ == "__main__":
    main()
