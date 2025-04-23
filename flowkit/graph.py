"""
Graph模块 - 依赖图构建

此模块提供用于构建步骤依赖关系图的功能。
"""

import copy
from .parser import yaml2dict, dict2stepsdict
from .step import StepStatus


class Graph:
    """
    表示步骤依赖关系图的类

    属性:
        steps (dict): 步骤名称到Step对象的映射
    """

    def __init__(self, steps_dict=None, yaml_files=None):
        """
        初始化Graph对象

        Args:
            steps_dict (dict, optional): 步骤名称到Step对象的映射
            yaml_files (str or list, optional): 单个YAML文件路径或YAML文件路径列表

        Note:
            如果同时提供steps_dict和yaml_files，则优先使用steps_dict。
        """
        self.steps = {}
        self.dependencies = {}  # 存储步骤之间的依赖关系

        if steps_dict:
            self.steps = steps_dict
            self._init_dependencies()
            self._build_dependency_graph()
        elif yaml_files:
            self.build_graph_from_yaml(yaml_files)

    def _init_dependencies(self):
        """初始化依赖关系字典"""
        self.dependencies = {}
        for name in self.steps:
            self.dependencies[name] = {"prev": [], "next": []}

    def build_graph_from_dict(self, data):
        """
        从字典加载步骤并构建依赖图

        Args:
            data (dict): 包含步骤信息的字典，可以是从多个YAML文件合并而来

        Returns:
            Graph: 当前 Graph 对象（支持链式调用）
        """
        # 创建步骤对象
        steps_dict = dict2stepsdict(data)

        # 合并步骤
        for name, step in steps_dict.items():
            if name not in self.steps:
                self.steps[name] = step
            else:
                # 如果步骤已存在，合并输入和输出
                existing_step = self.steps[name]
                for input_file in step.inputs:
                    if input_file not in existing_step.inputs:
                        existing_step.inputs.append(input_file)
                for output_file in step.outputs:
                    if output_file not in existing_step.outputs:
                        existing_step.outputs.append(output_file)

        # 初始化依赖关系
        self._init_dependencies()

        # 构建依赖图
        self._build_dependency_graph()

        return self

    def build_graph_from_yaml(self, yaml_files):
        """
        从 YAML 文件加载步骤并构建依赖图

        Args:
            yaml_files (str or list): 单个YAML文件路径或YAML文件路径列表

        Returns:
            Graph: 当前 Graph 对象（支持链式调用）
        """
        # 解析YAML文件
        data = yaml2dict(yaml_files)

        # 使用字典构建图
        return self.build_graph_from_dict(data)

    # 为了兼容性保留的方法
    def load_from_yaml(self, yaml_files):
        """为兼容性保留的方法，请使用 build_graph_from_yaml"""
        return self.build_graph_from_yaml(yaml_files)

    def _build_dependency_graph(self):
        """
        根据输入输出关系构建依赖图

        Returns:
            Graph: 当前 Graph 对象（支持链式调用）
        """
        # 创建文件到步骤的映射
        file_to_step = {}
        for step_name, step in self.steps.items():
            for output in step.outputs:
                file_to_step[output] = step_name

        # 建立依赖关系
        for step_name, step in self.steps.items():
            for input_file in step.inputs:
                if input_file in file_to_step:
                    producer_step_name = file_to_step[input_file]
                    if producer_step_name != step_name:  # 避免自己依赖自己
                        self.add_dependency(producer_step_name, step_name)

        return self

    def add_dependency(self, from_step_name, to_step_name):
        """
        添加依赖关系：from_step -> to_step

        Args:
            from_step_name (str): 前置步骤名称
            to_step_name (str): 后续步骤名称

        Returns:
            Graph: 当前 Graph 对象（支持链式调用）
        """
        if from_step_name not in self.steps:
            raise ValueError(f"步骤 {from_step_name} 不存在")
        if to_step_name not in self.steps:
            raise ValueError(f"步骤 {to_step_name} 不存在")

        # 更新依赖关系字典
        if from_step_name not in self.dependencies:
            self.dependencies[from_step_name] = {"prev": [], "next": []}
        if to_step_name not in self.dependencies:
            self.dependencies[to_step_name] = {"prev": [], "next": []}

        if to_step_name not in self.dependencies[from_step_name]["next"]:
            self.dependencies[from_step_name]["next"].append(to_step_name)
        if from_step_name not in self.dependencies[to_step_name]["prev"]:
            self.dependencies[to_step_name]["prev"].append(from_step_name)

        return self

    def get_prev_steps(self, step_name):
        """
        获取步骤的前置步骤

        Args:
            step_name (str): 步骤名称

        Returns:
            list: 前置步骤对象列表
        """
        if step_name not in self.dependencies:
            return []
        return [self.steps[name] for name in self.dependencies[step_name]["prev"] if name in self.steps]

    def get_next_steps(self, step_name):
        """
        获取步骤的后续步骤

        Args:
            step_name (str): 步骤名称

        Returns:
            list: 后续步骤对象列表
        """
        if step_name not in self.dependencies:
            return []
        return [self.steps[name] for name in self.dependencies[step_name]["next"] if name in self.steps]

    def get_root_steps(self):
        """
        获取没有前置步骤的根步骤

        Returns:
            list: 没有前置步骤的步骤列表
        """
        return [self.steps[name] for name, deps in self.dependencies.items() if not deps["prev"] and name in self.steps]

    def get_leaf_steps(self):
        """
        获取没有后续步骤的叶步骤

        Returns:
            list: 没有后续步骤的步骤列表
        """
        return [self.steps[name] for name, deps in self.dependencies.items() if not deps["next"] and name in self.steps]

    def get_ready_steps(self):
        """
        获取所有可以立即执行的步骤

        可以立即执行的步骤需要满足两个条件：
        1. 步骤当前状态为INIT，也就是没有执行过
        2. 没有前置步骤，或者所有前置步骤都是FINISHED或SKIPPED状态

        Returns:
            list: 可以立即执行的步骤对象列表
        """
        ready_steps = []

        for step_name, step in self.steps.items():
            # 检查步骤当前状态是否为INIT
            if step.status != StepStatus.INIT:
                continue

            # 获取前置步骤
            prev_steps = self.get_prev_steps(step_name)

            # 检查前置步骤的状态
            if not prev_steps or all(prev.status in [StepStatus.FINISHED, StepStatus.SKIPPED] for prev in prev_steps):
                ready_steps.append(step)

        return ready_steps

    def topological_sort(self):
        """
        对步骤进行拓扑排序

        Returns:
            list: 拓扑排序后的步骤列表
        """
        # 创建依赖关系的副本，以便我们可以修改它们
        dependencies_copy = {}
        for name, deps in self.dependencies.items():
            dependencies_copy[name] = {
                "prev": deps["prev"].copy(),
                "next": deps["next"].copy()
            }

        sorted_steps = []

        # 找到所有没有前置步骤的步骤
        no_deps = [self.steps[name] for name, deps in dependencies_copy.items() if not deps["prev"] and name in self.steps]

        while no_deps:
            # 取出一个没有前置步骤的步骤
            current = no_deps.pop(0)
            sorted_steps.append(current)

            # 对于所有当前步骤的后续步骤
            next_steps_names = dependencies_copy[current.name]["next"].copy()
            for next_name in next_steps_names:
                # 移除前置后续关系
                dependencies_copy[next_name]["prev"].remove(current.name)
                dependencies_copy[current.name]["next"].remove(next_name)

                # 如果该步骤没有其他前置步骤，则添加到无前置步骤列表
                if not dependencies_copy[next_name]["prev"] and next_name in self.steps:
                    no_deps.append(self.steps[next_name])

        # 检查是否有循环依赖
        has_remaining_deps = any(deps["prev"] for deps in dependencies_copy.values())
        if has_remaining_deps:
            raise ValueError("检测到循环前置后续关系")

        return sorted_steps

    def get_specific_step(self, step_name):
        """
        获取指定名称的步骤

        Args:
            step_name (str): 步骤名称

        Returns:
            Step: 步骤对象，如果不存在则返回None
        """
        return self.steps.get(step_name)

    def __getitem__(self, step_name):
        """支持使用 graph[step_name] 访问步骤"""
        return self.get_specific_step(step_name)

    def __contains__(self, step_name):
        """支持使用 step_name in graph 检查步骤是否存在"""
        return step_name in self.steps

    def __len__(self):
        """返回步骤数量"""
        return len(self.steps)

    def __iter__(self):
        """迭代所有步骤名称"""
        return iter(self.steps)

    def get_all_stepsdict(self):
        """返回步骤名称和步骤对象的键值对"""
        return self.steps.items()

    def get_all_stepsinfo(self):
        """返回所有步骤对象"""
        return self.steps.values()

    def get_all_stepsname(self):
        """返回所有步骤名称"""
        return self.steps.keys()

    def get_intersection_graph(self, other_graph):
        """
        获取与另一个图的交集

        Args:
            other_graph (Graph): 另一个图对象

        Returns:
            Graph: 包含两个图中都存在的步骤的新图对象

        Note:
            对于两个图中都存在的步骤，第二个图的步骤状态会覆盖第一个图
        """
        # 找出两个图中都存在的步骤
        common_step_names = set(self.steps.keys()) & set(other_graph.steps.keys())

        # 创建交集图的步骤字典
        import copy
        intersection_steps = {}
        for step_name in common_step_names:
            # 使用当前图中的步骤的深拷贝
            intersection_steps[step_name] = copy.deepcopy(self.steps[step_name])
            # 使用第二个图中步骤的状态覆盖
            intersection_steps[step_name].status = other_graph.steps[step_name].status

        # 创建新的图对象
        return Graph(steps_dict=intersection_steps)

    def create_union_graph(self, other_graph):
        """
        创建一个新的图，包含当前图和另一个图的所有步骤
        当两个图中有同名步骤时，第二个图的步骤状态会覆盖第一个图

        Args:
            other_graph (Graph): 另一个图对象

        Returns:
            Graph: 包含两个图中所有步骤的新图对象
        """
        # 创建当前图的步骤字典的副本
        import copy
        union_steps = copy.deepcopy(self.steps)

        # 添加或覆盖来自第二个图的步骤
        for step_name, step in other_graph.steps.items():
            if step_name in union_steps:
                # 如果步骤已存在，更新其状态
                union_steps[step_name].status = step.status
            else:
                # 如果步骤不存在，添加它
                union_steps[step_name] = step

        # 创建新的图对象
        return Graph(steps_dict=union_steps)

    def get_union_graph(self, other_graph):
        """
        获取与另一个图的并集，第二个图的步骤状态覆盖第一个图

        注意：此方法已弃用，请使用 create_union_graph 方法

        Args:
            other_graph (Graph): 另一个图对象

        Returns:
            Graph: 包含两个图中所有步骤的新图对象
        """
        import warnings
        warnings.warn(
            "get_union_graph is deprecated, use create_union_graph instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.create_union_graph(other_graph)

    def get_subgraph_after(self, step_name):
        """
        获取某个节点之后的子图（包含此节点）

        Args:
            step_name (str): 步骤名称

        Returns:
            Graph: 包含指定节点及其所有后续节点的新图对象

        Raises:
            ValueError: 如果步骤不存在
        """
        if step_name not in self.steps:
            raise ValueError(f"步骤 {step_name} 不存在")

        # 创建子图的步骤字典
        subgraph_steps = {step_name: self.steps[step_name]}

        # 递归收集所有后续节点
        def collect_successors(current_name):
            next_steps = self.get_next_steps(current_name)
            for next_step in next_steps:
                if next_step.name not in subgraph_steps:
                    subgraph_steps[next_step.name] = next_step
                    collect_successors(next_step.name)

        collect_successors(step_name)

        # 创建新的图对象
        return Graph(steps_dict=subgraph_steps)

    def get_subgraph_before(self, step_name):
        """
        获取某个节点之前的子图（包含此节点）

        Args:
            step_name (str): 步骤名称

        Returns:
            Graph: 包含指定节点及其所有前置节点的新图对象

        Raises:
            ValueError: 如果步骤不存在
        """
        if step_name not in self.steps:
            raise ValueError(f"步骤 {step_name} 不存在")

        # 创建子图的步骤字典
        subgraph_steps = {step_name: self.steps[step_name]}

        # 递归收集所有前置节点
        def collect_predecessors(current_name):
            prev_steps = self.get_prev_steps(current_name)
            for prev_step in prev_steps:
                if prev_step.name not in subgraph_steps:
                    subgraph_steps[prev_step.name] = prev_step
                    collect_predecessors(prev_step.name)

        collect_predecessors(step_name)

        # 创建新的图对象
        return Graph(steps_dict=subgraph_steps)

    def get_subgraph_between(self, start_step_name, end_step_name):
        """
        获取两个节点之间的子图

        Args:
            start_step_name (str): 起始步骤名称
            end_step_name (str): 终止步骤名称

        Returns:
            Graph: 包含从起始节点到终止节点之间的所有节点的新图对象

        Raises:
            ValueError: 如果步骤不存在或者不存在从起始节点到终止节点的路径
        """
        if start_step_name not in self.steps:
            raise ValueError(f"起始步骤 {start_step_name} 不存在")
        if end_step_name not in self.steps:
            raise ValueError(f"终止步骤 {end_step_name} 不存在")

        # 获取终止节点及其所有前置节点
        before_end = self.get_subgraph_before(end_step_name)

        # 获取起始节点及其所有后续节点
        after_start = self.get_subgraph_after(start_step_name)

        # 取交集得到两节点之间的子图
        between_graph = before_end.get_intersection_graph(after_start)

        # 检查是否存在从起始节点到终止节点的路径
        if start_step_name not in between_graph.steps or end_step_name not in between_graph.steps:
            raise ValueError(f"不存在从 {start_step_name} 到 {end_step_name} 的路径")

        return between_graph

    def get_subgraph_after_greedy(self, step_name):
        """
        获取某个节点之后的子图（贪婪模式），包含此节点及其所有后续节点，
        以及那些依赖于后续节点的其他节点及其前置步骤

        与 get_subgraph_after 不同，此方法会收集所有在拓扑排序中位于指定节点之后的节点，
        包括那些不直接依赖于该节点但依赖于该节点之后节点的其他节点，以及这些节点的前置步骤。

        例如，对于图 S1->S2->S3, S2.1->S3，调用 get_subgraph_after_greedy("S2")
        会返回包含 S2, S3, S2.1 的子图。

        Args:
            step_name (str): 步骤名称

        Returns:
            Graph: 包含指定节点及其所有后续节点的新图对象，以及那些依赖于后续节点的其他节点及其前置步骤

        Raises:
            ValueError: 如果步骤不存在
        """
        if step_name not in self.steps:
            raise ValueError(f"步骤 {step_name} 不存在")

        # 首先获取直接后续节点的子图
        direct_subgraph = self.get_subgraph_after(step_name)

        # 创建结果子图的步骤字典
        result_steps = {name: step for name, step in direct_subgraph.steps.items()}

        # 获取所有叶节点（没有后续步骤的节点）
        leaf_steps = direct_subgraph.get_leaf_steps()
        leaf_step_names = [step.name for step in leaf_steps]

        # 对于每个叶节点，找出依赖它的所有节点
        for leaf_name in leaf_step_names:
            # 找出所有以这个叶节点为输入的节点
            for other_name, other_step in self.steps.items():
                # 如果节点已经在结果中，跳过
                if other_name in result_steps:
                    continue

                # 检查这个节点是否依赖于叶节点或其他已包含的节点
                depends_on_included = False
                prev_steps = self.get_prev_steps(other_name)
                for prev_step in prev_steps:
                    if prev_step.name in result_steps:
                        depends_on_included = True
                        break

                # 如果依赖于已包含的节点，将其添加到结果中
                if depends_on_included:
                    result_steps[other_name] = other_step

                    # 递归收集这个节点的所有前置节点
                    def collect_predecessors(current_name):
                        prev_steps = self.get_prev_steps(current_name)
                        for prev_step in prev_steps:
                            if prev_step.name not in result_steps and prev_step.name != step_name:
                                result_steps[prev_step.name] = prev_step
                                collect_predecessors(prev_step.name)

                    collect_predecessors(other_name)

        # 创建新的图对象
        return Graph(steps_dict=result_steps)

    def get_subgraph_between_greedy(self, start_step_name, end_step_name):
        """
        获取两个节点之间的子图（贪婪模式）

        与 get_subgraph_between 不同，此方法使用 get_subgraph_after_greedy 获取起始节点之后的子图，
        可以捕获到更多的相关节点，包括那些不直接依赖于起始节点但依赖于起始节点后续节点的其他节点。

        例如，对于图：
        A -> B -> C -> D
             |         ^
             v         |
             E ------> F

        调用 get_subgraph_between_greedy("B", "D") 会返回包含 B, C, D, E, F 的子图。

        Args:
            start_step_name (str): 起始步骤名称
            end_step_name (str): 终止步骤名称

        Returns:
            Graph: 包含从起始节点到终止节点之间的所有节点的新图对象，以及那些依赖于这些节点的其他节点

        Raises:
            ValueError: 如果步骤不存在或者不存在从起始节点到终止节点的路径
        """
        if start_step_name not in self.steps:
            raise ValueError(f"起始步骤 {start_step_name} 不存在")
        if end_step_name not in self.steps:
            raise ValueError(f"终止步骤 {end_step_name} 不存在")

        # 获取终止节点及其所有前置节点
        before_end = self.get_subgraph_before(end_step_name)

        # 使用贪婪模式获取起始节点及其所有相关后续节点
        after_start_greedy = self.get_subgraph_after_greedy(start_step_name)

        # 取交集得到两节点之间的子图
        between_graph = before_end.get_intersection_graph(after_start_greedy)

        # 检查是否存在从起始节点到终止节点的路径
        if start_step_name not in between_graph.steps or end_step_name not in between_graph.steps:
            raise ValueError(f"不存在从 {start_step_name} 到 {end_step_name} 的路径")

        return between_graph

    def reset_all_steps(self):
        """
        重置所有步骤的状态为INIT

        Returns:
            Graph: 当前 Graph 对象（支持链式调用）
        """
        for step in self.steps.values():
            step.set_status(StepStatus.INIT)
        return self

    def add_step(self, step):
        """
        添加单个步骤到图中

        Args:
            step (Step): 要添加的步骤对象

        Returns:
            Graph: 当前 Graph 对象（支持链式调用）
        """
        self.steps[step.name] = step

        # 初始化依赖关系
        if step.name not in self.dependencies:
            self.dependencies[step.name] = {"prev": [], "next": []}

        return self

    def add_steps(self, steps):
        """
        添加多个步骤到图中

        Args:
            steps (list): 要添加的步骤对象列表

        Returns:
            Graph: 当前 Graph 对象（支持链式调用）
        """
        for step in steps:
            self.add_step(step)

        return self

    def merge_graph(self, other_graph):
        """
        合并另一个图的步骤和依赖关系

        Args:
            other_graph (Graph): 要合并的图对象

        Returns:
            Graph: 当前 Graph 对象（支持链式调用）
        """
        # 合并步骤
        for name, step in other_graph.steps.items():
            if name not in self.steps:
                self.steps[name] = step
            else:
                # 如果步骤已存在，合并输入和输出
                existing_step = self.steps[name]
                for input_file in step.inputs:
                    if input_file not in existing_step.inputs:
                        existing_step.inputs.append(input_file)
                for output_file in step.outputs:
                    if output_file not in existing_step.outputs:
                        existing_step.outputs.append(output_file)

        # 合并依赖关系
        for name, deps in other_graph.dependencies.items():
            if name not in self.dependencies:
                self.dependencies[name] = {"prev": [], "next": []}

            # 合并前置步骤
            for prev_name in deps["prev"]:
                if prev_name in self.steps and prev_name not in self.dependencies[name]["prev"]:
                    self.dependencies[name]["prev"].append(prev_name)

            # 合并后续步骤
            for next_name in deps["next"]:
                if next_name in self.steps and next_name not in self.dependencies[name]["next"]:
                    self.dependencies[name]["next"].append(next_name)

        # 重新构建依赖关系
        self._build_dependency_graph()

        return self
