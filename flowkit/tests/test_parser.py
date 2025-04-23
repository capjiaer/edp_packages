"""
测试 Parser 模块

此模块包含对 Parser 模块中各函数的单元测试。
"""

import unittest
import sys
import os
import tempfile
import yaml

# 添加父目录到 Python 路径，以便能够导入 flowkit 模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from flowkit.parser import deep_merge, yaml2dict, dict2stepsdict, parse_yaml
from flowkit.step import Step


class TestParser(unittest.TestCase):
    """测试 Parser 模块"""

    def setUp(self):
        """每个测试前的设置"""
        # 创建临时 YAML 文件
        self.temp_files = []
        
        # 创建第一个 YAML 文件
        self.yaml_content1 = {
            'flow1': {
                'dependency': {
                    'mode1': [
                        {'step1': {'cmd': 'echo step1', 'in': 'input1.txt', 'out': 'output1.txt'}},
                        {'step2': {'cmd': 'echo step2', 'in': 'output1.txt', 'out': 'output2.txt'}}
                    ]
                }
            }
        }
        self.temp_file1 = self._create_temp_yaml(self.yaml_content1)
        self.temp_files.append(self.temp_file1)
        
        # 创建第二个 YAML 文件
        self.yaml_content2 = {
            'flow2': {
                'dependency': {
                    'mode1': [
                        {'step3': {'cmd': 'echo step3', 'in': 'output2.txt', 'out': 'output3.txt'}}
                    ]
                }
            }
        }
        self.temp_file2 = self._create_temp_yaml(self.yaml_content2)
        self.temp_files.append(self.temp_file2)

    def tearDown(self):
        """每个测试后的清理"""
        # 删除临时文件
        for temp_file in self.temp_files:
            os.unlink(temp_file)

    def _create_temp_yaml(self, content):
        """创建临时 YAML 文件"""
        fd, path = tempfile.mkstemp(suffix='.yaml')
        with os.fdopen(fd, 'w') as f:
            yaml.dump(content, f)
        return path

    def test_deep_merge_dicts(self):
        """测试字典的深度合并"""
        dict1 = {'a': 1, 'b': {'c': 2, 'd': 3}}
        dict2 = {'b': {'e': 4}, 'f': 5}
        
        result = deep_merge(dict1, dict2)
        
        self.assertEqual(result['a'], 1)
        self.assertEqual(result['b']['c'], 2)
        self.assertEqual(result['b']['d'], 3)
        self.assertEqual(result['b']['e'], 4)
        self.assertEqual(result['f'], 5)

    def test_deep_merge_lists(self):
        """测试列表的合并"""
        dict1 = {'a': [1, 2]}
        dict2 = {'a': [3, 4]}
        
        result = deep_merge(dict1, dict2)
        
        self.assertEqual(result['a'], [1, 2, 3, 4])

    def test_deep_merge_overwrite(self):
        """测试非字典和非列表值的覆盖"""
        dict1 = {'a': 1, 'b': 'old'}
        dict2 = {'b': 'new', 'c': True}
        
        result = deep_merge(dict1, dict2)
        
        self.assertEqual(result['a'], 1)
        self.assertEqual(result['b'], 'new')
        self.assertEqual(result['c'], True)

    def test_yaml2dict_single_file(self):
        """测试单个 YAML 文件的解析"""
        result = yaml2dict(self.temp_file1)
        
        self.assertEqual(result, self.yaml_content1)

    def test_yaml2dict_multiple_files(self):
        """测试多个 YAML 文件的解析和合并"""
        result = yaml2dict([self.temp_file1, self.temp_file2])
        
        # 验证结果包含两个文件的内容
        self.assertIn('flow1', result)
        self.assertIn('flow2', result)
        self.assertEqual(result['flow1'], self.yaml_content1['flow1'])
        self.assertEqual(result['flow2'], self.yaml_content2['flow2'])

    def test_yaml2dict_empty_file(self):
        """测试空 YAML 文件的解析"""
        # 创建空 YAML 文件
        empty_file = self._create_temp_yaml({})
        self.temp_files.append(empty_file)
        
        result = yaml2dict(empty_file)
        
        self.assertEqual(result, {})

    def test_dict2stepsdict(self):
        """测试从字典创建步骤字典"""
        # 合并两个 YAML 内容
        data = deep_merge(self.yaml_content1, self.yaml_content2)
        
        steps = dict2stepsdict(data)
        
        # 验证步骤数量
        self.assertEqual(len(steps), 3)
        
        # 验证步骤属性
        self.assertIn('step1', steps)
        self.assertIn('step2', steps)
        self.assertIn('step3', steps)
        
        step1 = steps['step1']
        self.assertEqual(step1.id, 'step1')
        self.assertEqual(step1.cmd, 'echo step1')
        self.assertEqual(step1.inputs, ['input1.txt'])
        self.assertEqual(step1.outputs, ['output1.txt'])
        
        step2 = steps['step2']
        self.assertEqual(step2.id, 'step2')
        self.assertEqual(step2.cmd, 'echo step2')
        self.assertEqual(step2.inputs, ['output1.txt'])
        self.assertEqual(step2.outputs, ['output2.txt'])
        
        step3 = steps['step3']
        self.assertEqual(step3.id, 'step3')
        self.assertEqual(step3.cmd, 'echo step3')
        self.assertEqual(step3.inputs, ['output2.txt'])
        self.assertEqual(step3.outputs, ['output3.txt'])

    def test_dict2stepsdict_with_string_io(self):
        """测试字符串形式的输入输出"""
        data = {
            'flow': {
                'dependency': {
                    'mode': [
                        {'step': {'cmd': 'echo step', 'in': 'input.txt', 'out': 'output.txt'}}
                    ]
                }
            }
        }
        
        steps = dict2stepsdict(data)
        
        self.assertIn('step', steps)
        step = steps['step']
        self.assertEqual(step.inputs, ['input.txt'])
        self.assertEqual(step.outputs, ['output.txt'])

    def test_dict2stepsdict_with_list_io(self):
        """测试列表形式的输入输出"""
        data = {
            'flow': {
                'dependency': {
                    'mode': [
                        {'step': {'cmd': 'echo step', 'in': ['input1.txt', 'input2.txt'], 'out': ['output1.txt', 'output2.txt']}}
                    ]
                }
            }
        }
        
        steps = dict2stepsdict(data)
        
        self.assertIn('step', steps)
        step = steps['step']
        self.assertEqual(step.inputs, ['input1.txt', 'input2.txt'])
        self.assertEqual(step.outputs, ['output1.txt', 'output2.txt'])

    def test_dict2stepsdict_with_empty_io(self):
        """测试空输入输出"""
        data = {
            'flow': {
                'dependency': {
                    'mode': [
                        {'step': {'cmd': 'echo step'}}
                    ]
                }
            }
        }
        
        steps = dict2stepsdict(data)
        
        self.assertIn('step', steps)
        step = steps['step']
        self.assertEqual(step.inputs, [])
        self.assertEqual(step.outputs, [])

    def test_parse_yaml(self):
        """测试完整的解析流程"""
        steps = parse_yaml([self.temp_file1, self.temp_file2])
        
        # 验证步骤数量
        self.assertEqual(len(steps), 3)
        
        # 验证步骤属性
        self.assertIn('step1', steps)
        self.assertIn('step2', steps)
        self.assertIn('step3', steps)


if __name__ == '__main__':
    unittest.main()
