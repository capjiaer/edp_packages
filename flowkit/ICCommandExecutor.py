#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ICCommandExecutor模块 - IC设计命令执行器

此模块提供用于执行IC设计流程命令的执行器类，支持本地执行和LSF作业提交。
支持动态工作目录和日志目录管理，适用于多流程多步骤的IC设计环境。
"""

import os
import subprocess
import logging
import time
import re
from .run_graph import get_flow_var

# 配置日志记录器
logger = logging.getLogger(__name__)


class ICCommandExecutor:
    """
    IC设计命令执行器类

    用于执行IC设计流程中的各种命令，支持本地执行和LSF作业提交。
    可以作为execute_step和execute_all_steps函数的execute_func参数。
    支持动态工作目录和日志目录管理，适用于多流程多步骤的IC设计环境。

    属性:
        base_dir (str): 项目基础目录
        config (dict): 配置信息
        dry_run (bool): 是否为演示模式（不实际执行命令）
    """

    def __init__(self, base_dir, config=None, dry_run=False):
        """
        初始化IC命令执行器

        Args:
            base_dir (str): 项目基础目录，所有相对路径都基于此目录
            config (dict, optional): 配置信息
            dry_run (bool, optional): 是否为演示模式，默认为False
        """
        self.base_dir = os.path.abspath(base_dir)
        self.config = config or {}
        self.dry_run = dry_run

        logger.info(f"初始化IC命令执行器: 基础目录={self.base_dir}, 演示模式={dry_run}")

    def _parse_step_name(self, step_name):
        """
        解析步骤名称，提取流程名称和子步骤名称

        Args:
            step_name (str): 步骤名称，格式为 "flow_name.sub_step_name"

        Returns:
            tuple: (flow_name, sub_step_name)
        """
        if "." in step_name:
            flow_name, sub_step_name = step_name.split(".", 1)
            return flow_name, sub_step_name
        else:
            # 如果没有点号，则整个名称作为流程名，子步骤名为空
            return step_name, ""

    def _ensure_directory(self, dir_path):
        """
        确保目录存在，如果不存在则创建

        Args:
            dir_path (str): 目录路径

        Returns:
            str: 创建的目录路径
        """
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            logger.debug(f"创建目录: {dir_path}")
        return dir_path

    def _get_step_directories(self, step):
        """
        获取步骤的各种目录路径

        Args:
            step: 步骤对象

        Returns:
            dict: 包含各种目录路径的字典
        """
        step_name = step.name
        flow_name, sub_step_name = self._parse_step_name(step_name)

        # 如果子步骤名为空，使用流程名作为子目录
        sub_dir = sub_step_name if sub_step_name else flow_name

        # 构建各种目录路径
        dirs = {
            "runs": os.path.join(self.base_dir, "runs", flow_name, sub_dir),
            "logs": os.path.join(self.base_dir, "logs", flow_name, sub_dir),
            "rpts": os.path.join(self.base_dir, "rpts", flow_name, sub_dir),
            "data": os.path.join(self.base_dir, "data", flow_name, sub_dir),
            "hooks": os.path.join(self.base_dir, "hooks", flow_name, sub_dir),
            "cmds": os.path.join(self.base_dir, "cmds", flow_name)
        }

        # 确保所有目录都存在
        for dir_type, dir_path in dirs.items():
            self._ensure_directory(dir_path)

        return dirs

    def _replace_dir_variables(self, cmd, dirs):
        """
        替换命令中的目录变量

        Args:
            cmd (str): 原始命令
            dirs (dict): 目录字典

        Returns:
            str: 替换变量后的命令
        """
        # 定义变量映射
        var_map = {
            "${RUNS_DIR}": dirs["runs"],
            "${LOGS_DIR}": dirs["logs"],
            "${RPTS_DIR}": dirs["rpts"],
            "${DATA_DIR}": dirs["data"],
            "${HOOKS_DIR}": dirs["hooks"],
            "${CMDS_DIR}": dirs["cmds"],
            "${BASE_DIR}": self.base_dir
        }

        # 替换所有变量
        result = cmd
        for var, value in var_map.items():
            result = result.replace(var, value)

        return result

    def run_cmd(self, step, merged_var):
        """
        执行命令（用作execute_func）

        此方法符合flowkit.run_graph中execute_func的接口要求，
        可以直接用作execute_step和execute_all_steps函数的execute_func参数。

        Args:
            step: 步骤对象
            merged_var (dict): 合并后的配置字典

        Returns:
            bool: 执行是否成功
        """
        # 获取基本信息
        step_name = step.name
        cmd_file = step.cmd  # 命令文件名，如 "floorplan.tcl"

        if not cmd_file:
            logger.warning(f"步骤 {step_name} 没有指定命令文件，跳过执行")
            return True

        # 获取步骤的各种目录
        dirs = self._get_step_directories(step)
        work_dir = dirs["runs"]  # 工作目录设置为runs目录
        log_dir = dirs["logs"]
        cmd_path = os.path.join(dirs["cmds"], cmd_file)
        log_file = os.path.join(log_dir, f"{step_name.replace('.', '_')}.log")

        # 准备命令（决定使用本地还是LSF）
        cmd, use_lsf = self._prepare_command(step, merged_var, cmd_file, log_file, dirs)

        # 记录执行信息
        logger.info(f"执行步骤: {step_name}")
        logger.info(f"命令文件: {cmd_file}")
        logger.info(f"完整命令: {cmd}")
        logger.info(f"工作目录: {work_dir}")
        logger.info(f"日志文件: {log_file}")

        # 演示模式
        if self.dry_run:
            logger.info(f"[演示模式] 步骤 {step_name} 将在 {work_dir} 执行命令: {cmd}")
            return True

        try:
            if use_lsf:
                wait_lsf = get_flow_var(step, "wait_lsf", merged_var, default=True)
                return self._run_lsf(step, cmd, log_file, work_dir, merged_var, wait_lsf)
            else:
                timeout = get_flow_var(step, "timeout", merged_var, default=None)  # 默认为None，表示没有超时限制
                return self._run_local(step, cmd, log_file, work_dir, timeout)
        except Exception as e:
            logger.error(f"步骤 {step_name} 执行出错: {str(e)}")
            return False

    def _prepare_command(self, step, merged_var, cmd_file, log_file, dirs):
        """
        准备执行命令，决定使用本地执行还是LSF执行

        Args:
            step: 步骤对象
            merged_var (dict): 合并后的配置字典
            cmd_file (str): 命令文件名
            log_file (str): 日志文件路径
            dirs (dict): 目录字典

        Returns:
            tuple: (命令字符串, 是否使用LSF)
        """
        # 检查是否使用LSF
        use_lsf = get_flow_var(step, "lsf", merged_var, default=0)

        if use_lsf:
            # 构建LSF命令
            cmd = self._build_lsf_command(step, merged_var, cmd_file, log_file, dirs)
            if not cmd:  # 如果LSF命令构建失败，回退到本地执行
                logger.warning(f"步骤 {step.name} LSF配置无效，使用本地执行")
                use_lsf = False
                cmd = self._build_local_command(step, merged_var, cmd_file, dirs)
        else:
            # 构建本地命令
            cmd = self._build_local_command(step, merged_var, cmd_file, dirs)

        # 替换命令中的目录变量
        cmd = self._replace_dir_variables(cmd, dirs)

        return cmd, use_lsf

    def _build_local_command(self, step, merged_var, cmd_file, dirs):
        """
        构建本地执行的命令

        Args:
            step: 步骤对象
            merged_var (dict): 合并后的配置字典
            cmd_file (str): 命令文件名
            dirs (dict): 目录字典

        Returns:
            str: 构建的本地命令
        """
        # 获取工具选项
        tool_opt = get_flow_var(step, "tool_opt", merged_var, default="")

        # 构建命令路径
        cmd_path = os.path.join("${CMDS_DIR}", cmd_file)

        # 构建完整命令
        if tool_opt:
            cmd = f"{tool_opt} {cmd_path}"
        else:
            cmd = cmd_path

        return cmd

    def _build_lsf_command(self, step, merged_var, cmd_file, log_file, dirs):
        """
        构建LSF提交命令

        Args:
            step: 步骤对象
            merged_var (dict): 合并后的配置字典
            cmd_file (str): 命令文件名
            log_file (str): 日志文件路径
            dirs (dict): 目录字典

        Returns:
            str: 构建的LSF命令，如果配置无效则返回None
        """
        flow_name, sub_step_name = self._parse_step_name(step.name)

        # 基本LSF命令
        queue = get_flow_var(step, "queue", merged_var, default="normal")
        lsf_str = f"bsub -q {queue}"

        # 作业名
        job_str = f"-J {step.name}"

        # 资源字符串
        cpu_num = get_flow_var(step, "cpu_num", merged_var, default=1)
        memory = get_flow_var(step, "memory", merged_var, default=4000)
        span = get_flow_var(step, "span", merged_var, default=1)
        resource_str = f'-n {cpu_num} -R "rusage[mem={memory}] span[hosts={span}]"'

        # 日志重定向
        log_str = f"-o {log_file}"

        # 工具选项
        tool_opt = get_flow_var(step, "tool_opt", merged_var, default="")

        # 预处理命令
        pre_lsf = get_flow_var(step, "pre_lsf", merged_var, default="")

        # 构建本地命令（作为LSF的执行命令）
        local_cmd = self._build_local_command(step, merged_var, cmd_file, dirs)

        # 构建完整的LSF命令
        components = []
        if pre_lsf:
            components.append(pre_lsf)
        components.append(lsf_str)
        components.append(job_str)
        components.append(resource_str)
        components.append(log_str)

        # 组合LSF命令
        lsf_cmd = " ".join(components)

        # 获取工作目录
        work_dir = dirs["runs"]

        # 如果命令包含重定向或管道，需要用引号括起来
        if any(c in local_cmd for c in "|><&"):
            lsf_cmd += f" 'cd {work_dir} && {local_cmd}'"
        else:
            lsf_cmd += f" cd {work_dir} && {local_cmd}"

        return lsf_cmd

    def _run_local(self, step, cmd, log_file, work_dir, timeout=None):
        """
        在本地执行命令

        Args:
            step: 步骤对象
            cmd (str): 要执行的命令
            log_file (str): 日志文件路径
            work_dir (str): 工作目录
            timeout (int, optional): 超时时间（秒），如果为None则没有超时限制

        Returns:
            bool: 执行是否成功
        """
        logger.info(f"本地执行步骤 {step.name}, 工作目录: {work_dir}")
        if timeout:
            logger.info(f"设置超时: {timeout}秒")
        else:
            logger.info("没有设置超时限制")

        try:
            # 打开日志文件
            with open(log_file, 'w') as f:
                # 执行命令
                result = subprocess.run(
                    cmd,
                    shell=True,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    timeout=timeout,  # 如果为None，则没有超时限制
                    cwd=work_dir
                )

            # 检查命令是否成功执行
            if result.returncode == 0:
                logger.info(f"步骤 {step.name} 执行成功")
                return True
            else:
                logger.error(f"步骤 {step.name} 执行失败，返回码: {result.returncode}")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"步骤 {step.name} 执行超时 (>{timeout}秒)")
            return False

    def _run_lsf(self, step, cmd, log_file, work_dir, merged_var, wait_lsf=True):
        """
        通过LSF执行命令

        Args:
            step: 步骤对象
            cmd (str): 要执行的命令
            log_file (str): 日志文件路径
            work_dir (str): 工作目录
            merged_var (dict): 合并后的配置字典
            wait_lsf (bool): 是否等待LSF作业完成

        Returns:
            bool: 执行是否成功
        """
        logger.info(f"LSF提交步骤 {step.name}, 工作目录: {work_dir}")
        logger.info(f"LSF命令: {cmd}")

        try:
            # 提交LSF作业
            result = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=self.base_dir  # LSF提交命令在基础目录执行
            )

            # 检查作业是否成功提交
            if result.returncode != 0:
                logger.error(f"步骤 {step.name} 提交到LSF失败: {result.stdout}")
                return False

            # 提取作业ID
            output = result.stdout
            job_id = None
            for line in output.splitlines():
                if "Job <" in line and ">" in line:
                    job_id = line.split("<")[1].split(">")[0]
                    break

            if not job_id:
                logger.error(f"无法获取步骤 {step.name} 的LSF作业ID")
                return False

            logger.info(f"步骤 {step.name} 已成功提交到LSF，作业ID: {job_id}")

            # 如果不需要等待，直接返回成功
            if not wait_lsf:
                logger.info(f"不等待LSF作业 {job_id} 完成")
                return True

            # 等待作业完成
            return self._wait_lsf_job(step, job_id, merged_var)

        except Exception as e:
            logger.error(f"步骤 {step.name} 提交到LSF时出错: {str(e)}")
            return False

    def _wait_lsf_job(self, step, job_id, merged_var):
        """
        等待LSF作业完成

        Args:
            step: 步骤对象
            job_id (str): LSF作业ID
            merged_var (dict): 合并后的配置字典

        Returns:
            bool: 作业是否成功完成
        """
        # 获取轮询间隔和超时时间
        poll_interval = get_flow_var(step, "lsf_poll_interval", merged_var, default=30)
        max_wait_time = get_flow_var(step, "lsf_max_wait_time", merged_var, default=86400)  # 默认24小时

        logger.info(f"等待LSF作业 {job_id} 完成，轮询间隔: {poll_interval}秒，最大等待时间: {max_wait_time}秒")

        start_time = time.time()
        while True:
            # 检查是否超时
            elapsed_time = time.time() - start_time
            if elapsed_time > max_wait_time:
                logger.error(f"等待LSF作业 {job_id} 超时 (>{max_wait_time}秒)")
                return False

            # 检查作业状态
            try:
                result = subprocess.run(
                    f"bjobs -noheader {job_id}",
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                # 如果作业不存在，可能已经完成
                if "not found" in result.stderr:
                    # 检查作业历史
                    hist_result = subprocess.run(
                        f"bhist -n 1 -l {job_id}",
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )

                    # 检查作业是否成功完成
                    if "Done successfully" in hist_result.stdout:
                        logger.info(f"LSF作业 {job_id} 已成功完成")
                        return True
                    else:
                        logger.error(f"LSF作业 {job_id} 可能已失败: {hist_result.stdout}")
                        return False

                # 解析作业状态
                output = result.stdout.strip()
                if not output:
                    logger.warning(f"无法获取LSF作业 {job_id} 的状态，将继续等待")
                else:
                    fields = output.split()
                    if len(fields) >= 3:
                        status = fields[2]
                        if status == "DONE":
                            logger.info(f"LSF作业 {job_id} 已完成")
                            return True
                        elif status == "EXIT":
                            logger.error(f"LSF作业 {job_id} 异常退出")
                            return False
                        else:
                            logger.info(f"LSF作业 {job_id} 当前状态: {status}")

            except Exception as e:
                logger.warning(f"检查LSF作业 {job_id} 状态时出错: {str(e)}")

            # 等待一段时间后再次检查
            time.sleep(poll_interval)

    def execute_with_retry(self, step, merged_var, max_retries=3, retry_interval=60):
        """
        带重试机制的命令执行

        Args:
            step: 步骤对象
            merged_var (dict): 合并后的配置字典
            max_retries (int): 最大重试次数
            retry_interval (int): 重试间隔（秒）

        Returns:
            bool: 执行是否最终成功
        """
        for attempt in range(1, max_retries + 1):
            logger.info(f"执行步骤 {step.name} (尝试 {attempt}/{max_retries})")

            success = self.run_cmd(step, merged_var)
            if success:
                return True

            if attempt < max_retries:
                logger.warning(f"步骤 {step.name} 执行失败，将在 {retry_interval} 秒后重试")
                time.sleep(retry_interval)

        logger.error(f"步骤 {step.name} 在 {max_retries} 次尝试后仍然失败")
        return False

    def get_cmd_output(self, cmd, work_dir=None, timeout=60):
        """
        执行命令并获取输出

        Args:
            cmd (str): 要执行的命令
            work_dir (str, optional): 工作目录，默认为基础目录
            timeout (int): 超时时间（秒）

        Returns:
            tuple: (成功标志, 输出内容)
        """
        if work_dir is None:
            work_dir = self.base_dir

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout,
                cwd=work_dir
            )

            return result.returncode == 0, result.stdout
        except Exception as e:
            logger.error(f"执行命令 '{cmd}' 时出错: {str(e)}")
            return False, str(e)

    def check_tool_license(self, tool_name, timeout=60):
        """
        检查工具许可证是否可用

        Args:
            tool_name (str): 工具名称
            timeout (int): 超时时间（秒）

        Returns:
            bool: 许可证是否可用
        """
        # 不同工具的许可证检查命令
        license_check_cmds = {
            "innovus": "lmstat -a -c $CDS_LIC_FILE | grep -i innovus",
            "genus": "lmstat -a -c $CDS_LIC_FILE | grep -i genus",
            "calibre": "lmstat -a -c $MGLS_LICENSE_FILE | grep -i calibre",
            "primetime": "lmstat -a -c $SNPSLMD_LICENSE_FILE | grep -i primetime",
            "vcs": "lmstat -a -c $SNPSLMD_LICENSE_FILE | grep -i vcs"
        }

        if tool_name.lower() not in license_check_cmds:
            logger.warning(f"未知工具 '{tool_name}'，无法检查许可证")
            return True

        cmd = license_check_cmds[tool_name.lower()]
        logger.info(f"检查 {tool_name} 许可证")

        success, output = self.get_cmd_output(cmd, timeout=timeout)
        if not success:
            logger.error(f"检查 {tool_name} 许可证时出错")
            return False

        # 检查是否有可用的许可证
        if "lmstat" in output and "error" in output.lower():
            logger.error(f"{tool_name} 许可证服务器错误: {output}")
            return False

        if "Users of" in output:
            logger.info(f"{tool_name} 许可证可用")
            return True
        else:
            logger.warning(f"{tool_name} 许可证可能不可用: {output}")
            return False
