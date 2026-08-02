# ENVI Classic GUI 配方

## 设计原则

- 菜单必须使用完整名称路径调用，不用鼠标坐标。
- IDL 自绘对话框只能在该 ENVI 会话拥有的窗口内按比例定位。
- `x_ratio`、`y_ratio` 范围为 0 到 1，分别相对于目标窗口左上角和宽高。
- 每次点击前用 `wait_window` 确认标题；步骤间只使用必要的短等待。
- 新配方先 `dry_run=true` 检查字段，再用一小段动作实跑和截图确认。
- 不把密码、账号或其他敏感文本放入 `type_text`。

## 动作类型

```json
[
  {
    "type": "invoke_menu",
    "menu_path": ["Filter", "Convolutions and Morphology"]
  },
  {
    "type": "wait_window",
    "window_title_contains": "Convolutions and Morphology Tool",
    "timeout_seconds": 20
  },
  {
    "type": "capture",
    "stage_id": "03-open-convolution-tool",
    "caption": "打开卷积与形态学工具",
    "window_title_contains": "Convolutions and Morphology Tool",
    "parameters": {}
  }
]
```

受支持动作：

- `invoke_menu`：调用原生菜单叶节点；
- `wait_window`：等待 ENVI 窗口出现；
- `click`、`double_click`：窗口内比例坐标；
- `type_text`：向当前聚焦控件输入 Unicode 文本；
- `key`：如 `CTRL+A`、`TAB`、`ENTER`、`ESC`；
- `sleep`：0–30 秒短等待；
- `capture`：保存证据截图并写清单。

## 校准对话框

1. 只打开目标工具，不继续操作。
2. 捕获工具窗口并查看原始分辨率。
3. 以控件中心像素计算比例：

```text
x_ratio = (控件中心 x - 窗口 left) / 窗口 width
y_ratio = (控件中心 y - 窗口 top) / 窗口 height
```

4. 单独执行一次点击或键盘动作。
5. 立即截图确认状态变化。
6. 把成功动作加入正式配方，并记录 ENVI 版本、Windows 缩放比例和目标窗口标题。

坐标校准只对相同 ENVI 版本、对话框和布局复用。标题或窗口尺寸变化时重新校准。

## 常见安全失败

- 目标窗口不存在：动作失败，不点击其他窗口。
- 比例越界：输入校验直接拒绝。
- 菜单名称不精确：动作失败，重新列出菜单。
- ENVI 已退出：会话拒绝继续操作。
- 需要强制关闭：必须显式 `force=true`，且只影响本 MCP 启动的进程。
