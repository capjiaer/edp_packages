"""
Parser模块 - YAML配置文件解析

此模块提供用于解析YAML配置文件和创建Step对象的基本功能。
"""

import yaml
import copy
from .step import Step


def deep_merge(dict1, dict2):
    """
    将两个字典深度合并

    Args:
        dict1 (dict): 第一个字典
        dict2 (dict): 第二个字典

    Returns:
        dict: 合并后的字典
    """
    result = copy.deepcopy(dict1)
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        elif key in result and isinstance(result[key], list) and isinstance(value, list):
            result[key] = result[key] + value
        else:
            result[key] = copy.deepcopy(value)
    return result


def yaml2dict(yaml_files):
    """
    将一个或多个YAML文件解析为Python字典

    Args:
        yaml_files (str or list): 单个YAML文件路径或YAML文件路径列表

    Returns:
        dict: 解析并合并后的Python字典
    """
    # 如果输入是单个文件路径，转换为列表
    if isinstance(yaml_files, str):
        yaml_files = [yaml_files]

    # 初始化空字典
    result = {}

    # 依次解析并合并每个YAML文件
    for yaml_file in yaml_files:
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
            if data:
                result = deep_merge(result, data)

    return result


def dict2stepsdict(data):
    """
    从解析后的字典创建步骤字典

    Args:
        data (dict): 解析后的Python字典

    Returns:
        dict: 步骤名称到Step对象的映射
    """
    steps = {}

    # 创建所有步骤
    for flow_name, flow_data in data.items():
        if 'dependency' in flow_data:
            for mode, mode_steps in flow_data['dependency'].items():
                for step_item in mode_steps:
                    if isinstance(step_item, dict):
                        for step_name, step_data in step_item.items():
                            if isinstance(step_data, dict):
                                # 提取输入和输出文件
                                inputs = []
                                if 'in' in step_data and step_data['in']:
                                    inputs = [step_data['in']] if isinstance(step_data['in'], str) else step_data['in']

                                outputs = []
                                if 'out' in step_data and step_data['out']:
                                    outputs = [step_data['out']] if isinstance(step_data['out'], str) else step_data['out']

                                cmd = step_data.get('cmd')

                                # 创建步骤
                                step = Step(step_name, cmd, inputs, outputs)
                                steps[step_name] = step

    return steps


def parse_yaml(yaml_files):
    """
    解析一个或多个YAML文件并返回步骤字典（保留此函数以兼容现有代码）

    Args:
        yaml_files (str or list): 单个YAML文件路径或YAML文件路径列表

    Returns:
        dict: 步骤名称到Step对象的映射
    """
    data = yaml2dict(yaml_files)
    steps = dict2stepsdict(data)

    # 注意：依赖关系的建立已移至graph.py中处理

    return steps
