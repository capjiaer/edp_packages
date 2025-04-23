#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FlowKit 命令行接口

此模块提供命令行接口，用于执行工作流。
"""

import os
import sys
import argparse
import logging
from .parser import yaml2dict
from .graph import Graph
from .run_graph import execute_all_steps, execute_step, setup_logging
from .ICCommandExecutor import ICCommandExecutor


def main():
    """命令行入口点"""
    parser = argparse.ArgumentParser(description='FlowKit - IC设计工作流管理工具')
    subparsers = parser.add_subparsers(dest='command', help='命令')

    # 运行命令
    run_parser = subparsers.add_parser('run', help='执行工作流')
    run_parser.add_argument('--dependency', '-d', required=True, help='依赖文件路径')
    run_parser.add_argument('--config', '-c', required=True, help='配置文件路径')
    run_parser.add_argument('--project-dir', '-p', default=os.getcwd(), help='项目目录路径')
    run_parser.add_argument('--step', '-s', help='要执行的特定步骤，如果不指定则执行整个工作流')
    run_parser.add_argument('--force', '-f', action='store_true', help='强制执行步骤，忽略依赖关系')
    run_parser.add_argument('--continue-on-failure', '-k', action='store_true', help='当步骤失败时继续执行')
    run_parser.add_argument('--dry-run', '-n', action='store_true', help='演示模式，不实际执行命令')
    run_parser.add_argument('--verbose', '-v', action='store_true', help='显示详细日志')

    # 解析参数
    args = parser.parse_args()

    # 如果没有指定命令，显示帮助信息
    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 设置日志级别
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(level=log_level)

    # 执行命令
    if args.command == 'run':
        run_workflow(args)


def run_workflow(args):
    """执行工作流"""
    # 解析依赖文件
    dependency_file = os.path.abspath(args.dependency)
    if not os.path.exists(dependency_file):
        print(f"错误: 依赖文件 {dependency_file} 不存在")
        sys.exit(1)

    # 解析配置文件
    config_file = os.path.abspath(args.config)
    if not os.path.exists(config_file):
        print(f"错误: 配置文件 {config_file} 不存在")
        sys.exit(1)

    # 获取项目目录
    project_dir = os.path.abspath(args.project_dir)
    if not os.path.exists(project_dir):
        print(f"错误: 项目目录 {project_dir} 不存在")
        sys.exit(1)

    try:
        # 解析配置
        config = yaml2dict(config_file)

        # 创建图
        graph = Graph(yaml_files=dependency_file)

        # 创建执行器
        executor = ICCommandExecutor(project_dir, config, dry_run=args.dry_run)

        # 执行工作流
        if args.step:
            # 执行特定步骤
            print(f"执行步骤: {args.step}")
            success = execute_step(graph, args.step, execute_func=executor.run_cmd, merged_var=config, force=args.force)
            if success:
                print(f"步骤 {args.step} 执行成功")
            else:
                print(f"步骤 {args.step} 执行失败")
                sys.exit(1)
        else:
            # 执行整个工作流
            print("执行整个工作流")
            results = execute_all_steps(
                graph,
                execute_func=executor.run_cmd,
                merged_var=config,
                continue_on_failure=args.continue_on_failure
            )

            # 打印结果
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            print(f"执行完成: {success_count}/{total_count} 个步骤成功")

            # 如果有步骤失败，返回非零退出码
            if success_count < total_count:
                failed_steps = [step for step, success in results.items() if not success]
                print(f"失败的步骤: {', '.join(failed_steps)}")
                sys.exit(1)

    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
