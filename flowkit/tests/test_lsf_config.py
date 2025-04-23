#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试多级LSF配置

此脚本用于测试ICCommandExecutor类是否能够正确地使用多级LSF配置。
"""

import os
import logging
from flowkit.step import Step
from flowkit.ICCommandExecutor import ICCommandExecutor

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建基础目录
base_dir = os.path.join(os.getcwd(), "test_project")
os.makedirs(base_dir, exist_ok=True)

def test_multilevel_lsf_config():
    """测试多级LSF配置"""
    print("\n=== 测试多级LSF配置 ===")
    
    # 创建命令目录
    cmds_dir = os.path.join(base_dir, "cmds", "pnr_innovus")
    os.makedirs(cmds_dir, exist_ok=True)
    
    # 创建测试命令文件
    script_path = os.path.join(cmds_dir, "test_script.tcl")
    with open(script_path, "w") as f:
        f.write("@echo off\necho 测试脚本\nexit /b 0")
    os.chmod(script_path, 0o755)  # 设置可执行权限
    
    # 创建测试步骤
    step1 = Step("pnr_innovus.floorplan", "test_script.tcl")
    step2 = Step("pnr_innovus.place", "test_script.tcl")
    step3 = Step("pnr_innovus.route", "test_script.tcl")
    step4 = Step("pv_calibre.drc", "test_script.tcl")
    
    # 创建多级配置
    config = {
        "edp": {
            "lsf": 1,
            "cpu_num": 4,
            "memory": 8000,
            "queue": "normal"
        },
        "pnr_innovus": {
            "default": {
                "cpu_num": 8,
                "memory": 16000,
                "queue": "pnr_normal"
            },
            "floorplan": {
                "cpu_num": 16,
                "memory": 32000
            },
            "place": {
                "cpu_num": 32,
                "memory": 64000,
                "queue": "pnr_high"
            }
        },
        "pv_calibre": {
            "default": {
                "cpu_num": 16,
                "memory": 32000,
                "queue": "pv_normal"
            },
            "drc": {
                "cpu_num": 32
            }
        }
    }
    
    # 创建执行器（演示模式）
    executor = ICCommandExecutor(base_dir, config, dry_run=True)
    
    # 测试步骤级别配置
    print("\n步骤级别配置:")
    cmd1, use_lsf1 = executor._prepare_command(
        step1,
        config,
        "test_script.tcl",
        os.path.join(base_dir, "logs", "pnr_innovus", "floorplan", "test.log"),
        executor._get_step_directories(step1)
    )
    print(f"pnr_innovus.floorplan 命令: {cmd1}")
    print(f"使用LSF: {use_lsf1}")
    
    # 测试工具默认级别配置
    print("\n工具默认级别配置:")
    cmd2, use_lsf2 = executor._prepare_command(
        step3,
        config,
        "test_script.tcl",
        os.path.join(base_dir, "logs", "pnr_innovus", "route", "test.log"),
        executor._get_step_directories(step3)
    )
    print(f"pnr_innovus.route 命令: {cmd2}")
    print(f"使用LSF: {use_lsf2}")
    
    # 测试全局级别配置
    print("\n全局级别配置:")
    cmd3, use_lsf3 = executor._prepare_command(
        step4,
        config,
        "test_script.tcl",
        os.path.join(base_dir, "logs", "pv_calibre", "drc", "test.log"),
        executor._get_step_directories(step4)
    )
    print(f"pv_calibre.drc 命令: {cmd3}")
    print(f"使用LSF: {use_lsf3}")
    
    # 验证配置是否正确应用
    print("\n验证配置:")
    
    # 验证步骤级别配置
    assert "rusage[mem=32000]" in cmd1, "步骤级别内存配置未正确应用"
    assert "-n 16" in cmd1, "步骤级别CPU配置未正确应用"
    assert "-q pnr_normal" in cmd1, "工具默认级别队列配置未正确应用"
    
    # 验证工具默认级别配置
    assert "rusage[mem=16000]" in cmd2, "工具默认级别内存配置未正确应用"
    assert "-n 8" in cmd2, "工具默认级别CPU配置未正确应用"
    assert "-q pnr_normal" in cmd2, "工具默认级别队列配置未正确应用"
    
    # 验证全局级别配置与工具默认级别配置
    assert "rusage[mem=32000]" in cmd3, "工具默认级别内存配置未正确应用"
    assert "-n 32" in cmd3, "步骤级别CPU配置未正确应用"
    assert "-q pv_normal" in cmd3, "工具默认级别队列配置未正确应用"
    
    print("\n所有测试通过!")
    return True

if __name__ == "__main__":
    test_multilevel_lsf_config()
