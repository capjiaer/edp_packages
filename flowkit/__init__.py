"""
FlowKit - 控制流系统包

用于解析YAML配置文件，构建步骤依赖关系图，并管理步骤状态。
"""

__version__ = '0.1.0'

from .step import Step, StepStatus
from .graph import Graph
from .run_graph import (
    execute_step,
    execute_steps_parallel,
    execute_runnable_steps,
    execute_all_steps,
    get_status_summary,
    get_flow_var,
    setup_logging
)
