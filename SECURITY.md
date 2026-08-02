# Security Policy

## Supported version

仅维护最新发布版本。

## Reporting

请通过 GitHub Security Advisory 私密报告安全问题，不要在公开 issue 中附带数据、截图、凭据或本机路径。

## Scope

重点关注：

- 窗口焦点逃逸，导致操作落到非 ENVI 应用；
- 工作区路径校验绕过或覆盖用户文件；
- 任意命令、脚本或代码执行；
- 强制关闭非 MCP 启动进程；
- 证据哈希、冻结计划或完整性状态被绕过。
