"""
RunGraph模块 - 工作流执行

此模块提供用于执行工作流图的功能，包括单步执行和并行执行。
基于重构后的 step.py、parser.py 和 graph.py 实现。
"""

import time
import logging
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from .step import StepStatus
from .graph import Graph

# 配置日志记录器
logger = logging.getLogger(__name__)


def execute_step(graph, step_name, execute_func=None, merged_var=None, force=False):
    """
    执行指定的步骤

    Args:
        graph (Graph): 工作流图对象
        step_name (str): 步骤名称
        execute_func (callable, optional): 执行函数，接受 step, merged_var 作为参数
        merged_var (dict, optional): 合并后的配置字典
        force (bool): 是否强制执行步骤，无视其前置步骤的状态。如果为True，则即使前置步骤未完成，也会执行步骤。

    Returns:
        bool: 执行是否成功
    """
    step = graph.get_specific_step(step_name)
    if not step:
        raise ValueError(f"步骤 {step_name} 不存在")

    # 如果不是强制执行，检查步骤是否可以运行
    if not force:
        # 获取前置步骤
        prev_steps = graph.get_prev_steps(step_name)

        # 检查前置步骤的状态
        if prev_steps and not all(prev.status in [StepStatus.FINISHED, StepStatus.SKIPPED] for prev in prev_steps):
            logger.warning(f"步骤 {step_name} 不能运行，因为它的前置步骤尚未完成或跳过")
            return False

    # 如果是强制执行，记录日志
    if force:
        logger.info(f"强制执行步骤 {step_name}，无视前置步骤状态")

    # 更新状态为运行中
    step.update_status(StepStatus.RUNNING)

    try:
        # 如果提供了执行函数，则调用它
        if execute_func:
            if merged_var is not None:
                success = execute_func(step, merged_var)
            else:
                success = execute_func(step, {})
        else:
            # 默认执行逻辑
            logger.info(f"执行步骤 {step.name}，命令: {step.cmd}")
            # 这里可以添加实际的执行逻辑，例如调用subprocess执行命令
            time.sleep(1)  # 模拟执行时间
            success = True  # 假设执行成功

        # 更新状态
        if success:
            step.update_status(StepStatus.FINISHED)
        else:
            step.update_status(StepStatus.FAILED)

        return success
    except Exception as e:
        logger.error(f"执行步骤 {step_name} 时出错: {e}")
        step.update_status(StepStatus.FAILED)
        return False


def _execute_step_task(step, execute_func, merged_var=None):
    """
    执行步骤任务（内部方法，用于并行执行）

    Args:
        step: 要执行的步骤
        execute_func (callable, optional): 执行函数，接受 step, merged_var 作为参数
        merged_var (dict, optional): 合并后的配置字典

    Returns:
        bool: 执行是否成功
    """
    try:
        # 如果提供了执行函数，则调用它
        if execute_func:
            if merged_var is not None:
                success = execute_func(step, merged_var)
            else:
                success = execute_func(step, {})
        else:
            # 默认执行逻辑
            logger.info(f"执行步骤 {step.name}，命令: {step.cmd}")
            # 这里可以添加实际的执行逻辑，例如调用subprocess执行命令
            time.sleep(1)  # 模拟执行时间
            success = True  # 假设执行成功

        # 更新状态
        if success:
            step.update_status(StepStatus.FINISHED)
        else:
            step.update_status(StepStatus.FAILED)

        return success
    except Exception as e:
        logger.error(f"执行步骤 {step.name} 时出错: {e}")
        step.update_status(StepStatus.FAILED)
        raise  # 重新抛出异常，以便在上层捕获


def execute_steps_parallel(graph, step_names, execute_func=None, merged_var=None, max_workers=None, force=False):
    """
    并行执行多个步骤

    Args:
        graph (Graph): 工作流图对象
        step_names (list): 要执行的步骤名称列表
        execute_func (callable, optional): 执行函数，接受 step, merged_var 作为参数
        merged_var (dict, optional): 合并后的配置字典
        max_workers (int, optional): 最大并行数，默认为系统的CPU数量
        force (bool): 是否强制执行步骤，无视其前置步骤的状态。如果为True，则即使前置步骤未完成，也会执行步骤。

    Returns:
        dict: 步骤名称到执行结果的映射
    """
    results = {}
    runnable_steps = []

    # 检查哪些步骤可以运行
    for step_name in step_names:
        step = graph.get_specific_step(step_name)
        if not step:
            logger.warning(f"步骤 {step_name} 不存在")
            results[step_name] = False
            continue

        # 如果不是强制执行，检查步骤是否可以运行
        if not force:
            # 获取前置步骤
            prev_steps = graph.get_prev_steps(step_name)

            # 检查前置步骤的状态
            if prev_steps and not all(prev.status in [StepStatus.FINISHED, StepStatus.SKIPPED] for prev in prev_steps):
                logger.warning(f"步骤 {step_name} 不能运行，因为它的前置步骤尚未完成或跳过")
                results[step_name] = False
                continue

        # 如果是强制执行，记录日志
        if force:
            logger.info(f"强制执行步骤 {step_name}，无视前置步骤状态")

        runnable_steps.append(step)

    if not runnable_steps:
        return results

    # 并行执行可运行的步骤
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 创建任务
        future_to_step = {}
        for step in runnable_steps:
            # 更新状态为运行中
            step.update_status(StepStatus.RUNNING)

            # 提交任务
            future = executor.submit(_execute_step_task, step, execute_func, merged_var)
            future_to_step[future] = step

        # 处理结果
        for future in as_completed(future_to_step):
            step = future_to_step[future]
            try:
                success = future.result()
                results[step.name] = success
            except Exception as e:
                logger.error(f"执行步骤 {step.name} 时出错: {e}")
                step.update_status(StepStatus.FAILED)
                results[step.name] = False

    return results


def execute_runnable_steps(graph, execute_func=None, merged_var=None, max_workers=None):
    """
    执行所有当前可运行的步骤

    Args:
        graph (Graph): 工作流图对象
        execute_func (callable, optional): 执行函数，接受 step, merged_var 作为参数
        merged_var (dict, optional): 合并后的配置字典
        max_workers (int, optional): 最大并行数，默认为系统的CPU数量

    Returns:
        dict: 步骤名称到执行结果的映射
    """
    # 获取所有当前可运行的步骤
    runnable_steps = graph.get_ready_steps()
    step_names = [step.name for step in runnable_steps]

    # 并行执行这些步骤
    return execute_steps_parallel(graph, step_names, execute_func, merged_var, max_workers)


def execute_all_steps(graph, execute_func=None, merged_var=None, max_workers=None, continue_on_failure=False):
    """
    按拓扑顺序执行所有步骤

    此方法会按照前置后续关系执行所有步骤，先执行没有前置步骤的步骤，
    然后执行前置步骤已满足的步骤，直到所有步骤都执行完成。

    Args:
        graph (Graph): 工作流图对象
        execute_func (callable, optional): 执行函数，接受 step, merged_var 作为参数
        merged_var (dict, optional): 合并后的配置字典
        max_workers (int, optional): 最大并行数，默认为系统的CPU数量
        continue_on_failure (bool): 当步骤失败时是否继续执行。如果为True，则即使有步骤失败，也会继续执行其他可运行的步骤。

    Returns:
        dict: 步骤名称到执行结果的映射
    """
    all_results = {}

    # 重置所有步骤状态
    graph.reset_all_steps()

    # 循环执行，直到没有可运行的步骤
    while True:
        # 获取当前可运行的步骤
        runnable_steps = graph.get_ready_steps()
        if not runnable_steps:
            break

        # 并行执行这些步骤
        step_names = [step.name for step in runnable_steps]
        results = execute_steps_parallel(graph, step_names, execute_func, merged_var, max_workers)

        # 合并结果
        all_results.update(results)

        # 检查是否有步骤失败
        if not continue_on_failure and any(not success for success in results.values()):
            logger.warning("检测到步骤失败，停止执行")
            break

    # 检查是否有未执行的步骤
    unexecuted_steps = [step.name for step in graph.get_all_stepsinfo()
                       if step.status == StepStatus.INIT]
    if unexecuted_steps:
        logger.warning(f"以下步骤未执行: {', '.join(unexecuted_steps)}")
        logger.warning("可能存在循环前置后续关系或前置步骤失败")

    return all_results


def get_flow_var(step, var_name, merged_var, default=None):
    """
    按优先级在嵌套字典中查找变量值：
    1. 特定步骤的变量: merged_var[flow_name][step_name][var_name]
    2. 流程级变量: merged_var[flow_name][var_name]
    3. 全局变量: merged_var[var_name]
    4. 默认值

    Args:
        step: 步骤对象
        var_name: 变量名称
        merged_var: 合并后的配置字典
        default: 默认值

    Returns:
        找到的变量值或默认值
    """
    # 解析流程名称和步骤名称
    if "." in step.name:
        flow_name, step_name = step.name.split(".", 1)
    else:
        flow_name = ""
        step_name = step.name

    # 尝试获取特定步骤的变量
    try:
        if flow_name and flow_name in merged_var and isinstance(merged_var[flow_name], dict):
            if step_name and step_name in merged_var[flow_name] and isinstance(merged_var[flow_name][step_name], dict):
                if var_name in merged_var[flow_name][step_name]:
                    return merged_var[flow_name][step_name][var_name]
    except (KeyError, TypeError):
        pass

    # 尝试获取流程级变量
    try:
        if flow_name and flow_name in merged_var and isinstance(merged_var[flow_name], dict):
            if var_name in merged_var[flow_name]:
                return merged_var[flow_name][var_name]
    except (KeyError, TypeError):
        pass

    # 尝试获取全局变量
    try:
        if var_name in merged_var:
            return merged_var[var_name]
    except (KeyError, TypeError):
        pass

    # 返回默认值
    return default


def setup_logging(level=logging.INFO, log_file=None, log_format=None):
    """
    设置日志记录器

    Args:
        level: 日志级别，默认为 INFO
        log_file: 日志文件路径，如果为 None，则只输出到控制台
        log_format: 日志格式，如果为 None，则使用默认格式
    """
    # 设置日志级别
    logger.setLevel(level)

    # 如果没有处理器，添加一个控制台处理器
    if not logger.handlers:
        # 设置日志格式
        if log_format is None:
            log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(log_format)

        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # 如果指定了日志文件，添加文件处理器
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def get_status_summary(graph):
    """
    获取步骤状态摘要

    Args:
        graph (Graph): 工作流图对象

    Returns:
        dict: 各状态的步骤数量
    """
    summary = {
        StepStatus.INIT: 0,
        StepStatus.RUNNING: 0,
        StepStatus.FINISHED: 0,
        StepStatus.SKIPPED: 0,
        StepStatus.FAILED: 0
    }

    for step in graph.get_all_stepsinfo():
        summary[step.status] += 1

    return summary
