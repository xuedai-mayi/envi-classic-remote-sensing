# Contributing

欢迎修复兼容性问题、增加通用实验预设或改进证据校验。

## 开发检查

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\setup.ps1 -Dev
.\.venv\Scripts\python.exe -m pytest
powershell.exe -ExecutionPolicy Bypass -File .\scripts\check_release.ps1
```

真实 ENVI 冒烟测试是可选项，只能在拥有合法 ENVI Classic 5.6 安装的 Windows 机器上执行：

```powershell
.\.venv\Scripts\python.exe .\tests\smoke_envi_classic.py <实验工作区>
```

## 提交规则

- 不提交老师数据、指导书、模板、benchmark、学生报告、个人信息或实验截图。
- 新的实验预设只描述通用步骤，不写入本机绝对路径和特定学生答案。
- GUI 配方必须先 `dry_run`，并限制在 MCP 启动的 ENVI 进程窗口内。
- 新增工具需提供 Pydantic 输入/输出模型、明确错误信息、工具注解和测试。
- 不用生成图片冒充真实 ENVI 证据，也不降低冻结后的证据门禁。
