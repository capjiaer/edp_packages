#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FlowKit 安装脚本
"""

from setuptools import setup, find_packages

# 直接指定版本号，避免读取文件
version = '0.1.0'

# 直接提供描述，避免读取文件
long_description = """
# FlowKit

FlowKit 是一个用于管理 IC 设计工作流的 Python 库。它提供了一套工具，用于解析 YAML 配置文件，构建步骤依赖关系图，并管理步骤状态。

## 特性

- **步骤管理**：定义和管理工作流步骤，包括命令、输入、输出和状态
- **依赖关系**：自动处理步骤之间的依赖关系
- **图操作**：支持图的交集、并集、子图提取等操作
- **执行控制**：支持单步执行、并行执行和全流程执行
- **LSF 支持**：内置 LSF 作业提交和监控功能
- **多级配置**：支持全局级别、工具默认级别和步骤级别的配置
"""

setup(
    name='flowkit',
    version=version,
    description='IC设计工作流管理工具',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Anping Chen',
    author_email='capjiaer@163.com',
    url='https://github.com/capjiaer/edp_packages',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    python_requires='>=3.6',
    install_requires=[
        'pyyaml>=5.1',
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.10',
            'flake8>=3.8',
        ],
    },
    entry_points={
        'console_scripts': [
            'flowkit=flowkit.cli:main',
        ],
    },
)
