"""
Step模块 - 定义工作流步骤和状态管理

此模块提供Step类，用于表示工作流中的单个步骤，
以及StepStatus类，用于定义步骤的可能状态。
"""


class StepStatus:
    """步骤状态常量"""
    INIT = "init"           # 初始状态
    RUNNING = "running"     # 运行中
    FINISHED = "finished"   # 已完成
    SKIPPED = "skipped"     # 已跳过
    FAILED = "failed"       # 失败


class Step:
    """
    表示工作流中的一个步骤

    属性:
        id (str): 步骤ID
        name (str): 步骤名称，与ID相同
        cmd (str): 执行命令
        inputs (list): 输入文件列表
        outputs (list): 输出文件列表
        status (str): 当前状态，使用StepStatus中的常量
    """

    def __init__(self, id, cmd=None, inputs=None, outputs=None):
        """
        初始化步骤

        Args:
            id (str): 步骤ID
            cmd (str, optional): 执行命令
            inputs (list, optional): 输入文件列表
            outputs (list, optional): 输出文件列表
        """
        self.id = id
        self.name = id  # 为了兼容性，添加name属性
        self.cmd = cmd
        self.inputs = inputs or []
        self.outputs = outputs or []
        self.status = StepStatus.INIT


    def update_status(self, status):
        """
        更新步骤状态

        Args:
            status (str): 新状态，使用StepStatus中的常量
        """
        valid_statuses = [StepStatus.INIT, StepStatus.RUNNING,
                         StepStatus.FINISHED, StepStatus.FAILED,
                         StepStatus.SKIPPED]
        if status not in valid_statuses:
            raise ValueError("Status must be a valid StepStatus value")
        self.status = status

    def get_status(self):
        """获取当前状态"""
        return self.status

    def set_status(self, status):
        """
        设置步骤状态（与update_status相同，为了兼容性）

        Args:
            status (str): 新状态，使用StepStatus中的常量
        """
        self.update_status(status)

    def reset(self):
        """重置步骤状态为INIT"""
        if self.status != StepStatus.INIT:
            self.status = StepStatus.INIT

    def __repr__(self):
        """返回步骤的字符串表示"""
        return f"Step({self.id}, status={self.status})"
