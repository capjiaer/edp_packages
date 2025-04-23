# FlowKit

FlowKit 是一个用于管理 IC 设计工作流的 Python 库。它提供了一套工具，用于解析 YAML 配置文件，构建步骤依赖关系图，并管理步骤状态。

## 特性

- **步骤管理**：定义和管理工作流步骤，包括命令、输入、输出和状态
- **依赖关系**：自动处理步骤之间的依赖关系
- **图操作**：支持图的交集、并集、子图提取等操作
- **执行控制**：支持单步执行、并行执行和全流程执行
- **LSF 支持**：内置 LSF 作业提交和监控功能
- **多级配置**：支持全局级别、工具默认级别和步骤级别的配置

## 安装

```bash
pip install flowkit
```

## 快速入门

### 创建和执行工作流

```python
from flowkit import Step, Graph, execute_all_steps, ICCommandExecutor

# 创建步骤
step1 = Step("flow.step1", "step1.tcl", [], ["output1.txt"])
step2 = Step("flow.step2", "step2.tcl", ["output1.txt"], ["output2.txt"])

# 创建图
graph = Graph(steps_dict={"flow.step1": step1, "flow.step2": step2})

# 创建配置
config = {
    "edp": {
        "lsf": 0,
        "tool_opt": "bash"
    }
}

# 创建执行器
executor = ICCommandExecutor("/path/to/project", config)

# 执行工作流
results = execute_all_steps(graph, execute_func=executor.run_cmd, merged_var=config)
```

### 从 YAML 文件创建工作流

```python
from flowkit import Graph, execute_all_steps, ICCommandExecutor

# 从 YAML 文件创建图
graph = Graph(yaml_files=["dependency.yaml"])

# 解析配置
config = {
    "edp": {
        "lsf": 0,
        "tool_opt": "bash"
    }
}

# 创建执行器
executor = ICCommandExecutor("/path/to/project", config)

# 执行工作流
results = execute_all_steps(graph, execute_func=executor.run_cmd, merged_var=config)
```

## 多级配置

FlowKit 支持多级配置，按照以下顺序查找配置项：

1. 步骤级别：`flow_name.step_name.var_name`
2. 工具默认级别：`flow_name.default.var_name`
3. 全局级别：`edp.var_name`

示例配置：

```yaml
# 全局配置
edp:
  lsf: 1
  cpu_num: 4
  memory: 8000
  queue: "normal"

# 工具默认配置
pnr_innovus:
  default:
    cpu_num: 8
    memory: 16000
    queue: "pnr_normal"
  
  # 步骤配置
  floorplan:
    cpu_num: 16
    memory: 32000
```

## 文档

更详细的文档请参考 [API 文档](docs/api.md)。

## 贡献

欢迎贡献代码、报告问题或提出改进建议。请参考 [贡献指南](CONTRIBUTING.md)。

## 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。
