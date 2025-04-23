"""
测试 ICCommandExecutor 模块

此模块包含对 ICCommandExecutor 类的单元测试。
"""

import unittest
import sys
import os
import tempfile
import shutil
import logging
import subprocess
from unittest.mock import patch, MagicMock

# 添加父目录到 Python 路径，以便能够导入 flowkit 模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from flowkit.ICCommandExecutor import ICCommandExecutor
from flowkit.step import Step, StepStatus


class TestICCommandExecutor(unittest.TestCase):
    """测试 ICCommandExecutor 类"""

    def setUp(self):
        """每个测试前的设置"""
        # 创建临时目录作为基础目录
        self.base_dir = tempfile.mkdtemp()

        # 创建必要的子目录
        os.makedirs(os.path.join(self.base_dir, "cmds", "test_flow"), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "runs", "test_flow", "step1"), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "logs", "test_flow", "step1"), exist_ok=True)

        # 创建测试脚本
        self.script_path = os.path.join(self.base_dir, "cmds", "test_flow", "test_script.tcl")
        with open(self.script_path, "w") as f:
            f.write("echo 'Hello, World!'")
        os.chmod(self.script_path, 0o755)

        # 创建测试步骤
        self.step = Step("test_flow.step1", "test_script.tcl", [], ["output.txt"])

        # 创建配置
        self.config = {
            "tool_opt": "bash",
            "timeout": 10,
            "test_flow": {
                "step1": {
                    "timeout": 5
                }
            }
        }

        # 创建执行器
        self.executor = ICCommandExecutor(self.base_dir, self.config)

        # 禁用日志输出
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        """每个测试后的清理"""
        # 删除临时目录
        shutil.rmtree(self.base_dir)

        # 恢复日志输出
        logging.disable(logging.NOTSET)

    def test_init(self):
        """测试初始化"""
        # 验证基本属性
        self.assertEqual(self.executor.base_dir, self.base_dir)
        self.assertEqual(self.executor.config, self.config)
        self.assertFalse(self.executor.dry_run)

        # 测试演示模式
        dry_run_executor = ICCommandExecutor(self.base_dir, self.config, dry_run=True)
        self.assertTrue(dry_run_executor.dry_run)

    def test_parse_step_name(self):
        """测试解析步骤名称"""
        # 测试带点号的名称
        flow_name, sub_step_name = self.executor._parse_step_name("test_flow.step1")
        self.assertEqual(flow_name, "test_flow")
        self.assertEqual(sub_step_name, "step1")

        # 测试不带点号的名称
        flow_name, sub_step_name = self.executor._parse_step_name("test_flow")
        self.assertEqual(flow_name, "test_flow")
        self.assertEqual(sub_step_name, "")

    def test_get_step_directories(self):
        """测试获取步骤目录"""
        # 获取目录
        dirs = self.executor._get_step_directories(self.step)

        # 验证目录路径
        self.assertEqual(dirs["runs"], os.path.join(self.base_dir, "runs", "test_flow", "step1"))
        self.assertEqual(dirs["logs"], os.path.join(self.base_dir, "logs", "test_flow", "step1"))
        self.assertEqual(dirs["rpts"], os.path.join(self.base_dir, "rpts", "test_flow", "step1"))
        self.assertEqual(dirs["data"], os.path.join(self.base_dir, "data", "test_flow", "step1"))
        self.assertEqual(dirs["hooks"], os.path.join(self.base_dir, "hooks", "test_flow", "step1"))
        self.assertEqual(dirs["cmds"], os.path.join(self.base_dir, "cmds", "test_flow"))

        # 验证目录是否存在
        for dir_path in dirs.values():
            self.assertTrue(os.path.exists(dir_path))

    def test_replace_dir_variables(self):
        """测试替换目录变量"""
        # 获取目录
        dirs = self.executor._get_step_directories(self.step)

        # 测试替换
        cmd = "cat ${CMDS_DIR}/test_script.tcl > ${LOGS_DIR}/output.log"
        replaced_cmd = self.executor._replace_dir_variables(cmd, dirs)

        expected_cmd = f"cat {dirs['cmds']}/test_script.tcl > {dirs['logs']}/output.log"
        self.assertEqual(replaced_cmd, expected_cmd)

    @patch('subprocess.run')
    def test_run_local(self, mock_run):
        """测试本地执行"""
        # 模拟成功执行
        mock_run.return_value = MagicMock(returncode=0)

        # 执行命令
        result = self.executor._run_local(
            self.step,
            "echo 'test'",
            os.path.join(self.base_dir, "logs", "test_flow", "step1", "test.log"),
            os.path.join(self.base_dir, "runs", "test_flow", "step1"),
            timeout=5
        )

        # 验证结果
        self.assertTrue(result)
        mock_run.assert_called_once()

        # 模拟失败执行
        mock_run.reset_mock()
        mock_run.return_value = MagicMock(returncode=1)

        # 执行命令
        result = self.executor._run_local(
            self.step,
            "echo 'test' && exit 1",
            os.path.join(self.base_dir, "logs", "test_flow", "step1", "test.log"),
            os.path.join(self.base_dir, "runs", "test_flow", "step1"),
            timeout=5
        )

        # 验证结果
        self.assertFalse(result)
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_run_local_timeout(self, mock_run):
        """测试本地执行超时"""
        # 模拟超时
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 5)

        # 执行命令
        result = self.executor._run_local(
            self.step,
            "sleep 10",
            os.path.join(self.base_dir, "logs", "test_flow", "step1", "test.log"),
            os.path.join(self.base_dir, "runs", "test_flow", "step1"),
            timeout=5
        )

        # 验证结果
        self.assertFalse(result)
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_run_cmd_local(self, mock_run):
        """测试 run_cmd 方法（本地执行）"""
        # 模拟成功执行
        mock_run.return_value = MagicMock(returncode=0)

        # 执行命令
        result = self.executor.run_cmd(self.step, self.config)

        # 验证结果
        self.assertTrue(result)
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_run_cmd_dry_run(self, mock_run):
        """测试 run_cmd 方法（演示模式）"""
        # 创建演示模式执行器
        dry_run_executor = ICCommandExecutor(self.base_dir, self.config, dry_run=True)

        # 执行命令
        result = dry_run_executor.run_cmd(self.step, self.config)

        # 验证结果
        self.assertTrue(result)
        mock_run.assert_not_called()  # 演示模式不应该实际执行命令

    @patch('subprocess.run')
    def test_run_cmd_no_cmd_file(self, mock_run):
        """测试 run_cmd 方法（无命令文件）"""
        # 创建无命令文件的步骤
        step = Step("test_flow.step1", None, [], ["output.txt"])

        # 执行命令
        result = self.executor.run_cmd(step, self.config)

        # 验证结果
        self.assertTrue(result)
        mock_run.assert_not_called()  # 无命令文件不应该执行命令

    @patch('flowkit.ICCommandExecutor.ICCommandExecutor._run_local')
    def test_prepare_command_local(self, mock_run_local):
        """测试准备命令（本地执行）"""
        # 模拟成功执行
        mock_run_local.return_value = True

        # 获取目录
        dirs = self.executor._get_step_directories(self.step)

        # 准备命令
        cmd, use_lsf = self.executor._prepare_command(
            self.step,
            self.config,
            "test_script.tcl",
            os.path.join(dirs["logs"], "test.log"),
            dirs
        )

        # 验证结果
        self.assertFalse(use_lsf)
        self.assertIn("bash", cmd)
        self.assertIn("test_script.tcl", cmd)

    @patch('flowkit.ICCommandExecutor.ICCommandExecutor._run_lsf')
    def test_prepare_command_lsf(self, mock_run_lsf):
        """测试准备命令（LSF执行）"""
        # 模拟成功执行
        mock_run_lsf.return_value = True

        # 创建LSF配置
        lsf_config = {
            "lsf": 1,
            "queue": "normal",
            "cpu_num": 4,
            "memory": 8000,
            "span": 1,
            "tool_opt": "bash"
        }

        # 获取目录
        dirs = self.executor._get_step_directories(self.step)

        # 准备命令
        cmd, use_lsf = self.executor._prepare_command(
            self.step,
            lsf_config,
            "test_script.tcl",
            os.path.join(dirs["logs"], "test.log"),
            dirs
        )

        # 验证结果
        self.assertTrue(use_lsf)
        self.assertIn("bsub", cmd)
        self.assertIn("-q normal", cmd)
        self.assertIn("-n 4", cmd)
        self.assertIn("rusage[mem=8000]", cmd)
        self.assertIn("bash", cmd)
        self.assertIn("test_script.tcl", cmd)

    @patch('subprocess.run')
    def test_get_cmd_output(self, mock_run):
        """测试获取命令输出"""
        # 模拟成功执行
        mock_run.return_value = MagicMock(returncode=0, stdout="Command output")

        # 获取命令输出
        success, output = self.executor.get_cmd_output("echo 'test'")

        # 验证结果
        self.assertTrue(success)
        self.assertEqual(output, "Command output")
        mock_run.assert_called_once()

        # 模拟失败执行
        mock_run.reset_mock()
        mock_run.return_value = MagicMock(returncode=1, stdout="Error output")

        # 获取命令输出
        success, output = self.executor.get_cmd_output("echo 'test' && exit 1")

        # 验证结果
        self.assertFalse(success)
        self.assertEqual(output, "Error output")
        mock_run.assert_called_once()

    @patch('flowkit.ICCommandExecutor.ICCommandExecutor.run_cmd')
    def test_execute_with_retry(self, mock_run_cmd):
        """测试带重试的执行"""
        # 模拟第一次失败，第二次成功
        mock_run_cmd.side_effect = [False, True]

        # 执行命令
        result = self.executor.execute_with_retry(self.step, self.config, max_retries=2, retry_interval=0.1)

        # 验证结果
        self.assertTrue(result)
        self.assertEqual(mock_run_cmd.call_count, 2)

        # 模拟所有尝试都失败
        mock_run_cmd.reset_mock()
        mock_run_cmd.side_effect = [False, False, False]

        # 执行命令
        result = self.executor.execute_with_retry(self.step, self.config, max_retries=3, retry_interval=0.1)

        # 验证结果
        self.assertFalse(result)
        self.assertEqual(mock_run_cmd.call_count, 3)


if __name__ == '__main__':
    unittest.main()
