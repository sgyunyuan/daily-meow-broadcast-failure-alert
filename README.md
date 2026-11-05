# 每日 MeoW 广播机器人

每天北京时间 07:08 将 `content/daily_message.txt` 广播到指定 MeoW 频道。支持推送结果上报模式控制，默认仅广播失败时发送通知。

## 功能

- 📢 每日定时广播到 MeoW 频道
- 📝 广播文案支持 `{date}` 占位符（自动替换为北京时间日期）
- 🔔 推送结果上报模式控制（全部 / 仅成功 / 仅失败 / 关闭）
- ❌ 广播失败时自动发送失败通知（含频道名称、广播内容、失败原因、失败时间）
- 🔒 敏感配置通过 GitHub Secrets 管理，不提交到仓库
- 🔄 自动保活提交，防止 60 天无 commit 导致定时任务被禁用
- 🛡️ 失败原因细化：配置缺失 / 网络异常 / HTTP 错误 / API 业务错误
- ✅ 支持公开/私有仓库（通过 PAT 认证）

## 上报模式

通过 `REPORT_MODE` secret 控制（可选，默认 `fail`）：

| REPORT_MODE | 成功时上报 | 失败时上报 | 说明 |
|-------------|-----------|-----------|------|
| `all` | ✅ | ✅ | 全部上报 |
| `success` | ✅ | ❌ | 仅上报成功 |
| `fail` | ❌ | ✅ | 仅上报失败（默认） |
| `none` | ❌ | ❌ | 完全不上报 |

失败通知发送到 `https://api.chuckfang.com/昵称/`，使用 `application/x-www-form-urlencoded` POST，正文包含频道名称、广播内容、失败原因和北京时间。

## 配置

在 GitHub 仓库 **Settings → Secrets and variables → Actions** 添加 Repository secrets：

| Secret | 必填 | 说明 |
|--------|------|------|
| `CHANNEL_ID` | ✅ | 正式频道 ID |
| `UNION_ID` | ✅ | 频道创建者的 MeoW unionId |
| `GH_TOKEN` | ✅ | Personal Access Token（repo 权限，用于 checkout + 保活 push） |
| `REPORT_MODE` | ❌ | 上报模式，见上方说明（默认 `fail`） |

把 `content/channel_name.txt` 改成实际频道名称。编辑 `content/daily_message.txt` 设置日常文案；文案可用 `{date}` 插入北京时间日期。

不要将频道 ID 或 unionId 提交到仓库。广播 API 通过 URL 查询参数接收这两个值；GitHub Secrets 保护仓库配置，不会加密接口请求传输。

## 计划

GitHub Actions 使用 UTC cron `23:58`，对应北京时间每天 07:58。工作流也支持手动触发。

广播接口调用间隔至少 30 分钟，每日最多 3 次，广播时间为 06:00–23:00。

## 错误提示

| 场景 | 提示内容 |
|------|---------|
| 缺少 Secrets | `缺少必需的 GitHub Actions Secrets：CHANNEL_ID 或 UNION_ID` |
| HTTP 403 | `广播接口返回 HTTP 403（权限被拒绝）：请检查 CHANNEL_ID/UNION_ID 是否正确、是否已过期` |
| HTTP 429 | `广播接口返回 HTTP 429（请求过于频繁）：请降低调用频率后重试` |
| 连接超时 | `网络请求失败：连接超时(30s)，API 响应缓慢或不可达` |
| 无法连接 | `网络请求失败：无法连接到服务器` |
| API 业务错误 | `广播接口报告失败：{detail}` |

所有失败通知中的敏感值（CHANNEL_ID、UNION_ID）会自动脱敏为 `[已隐藏]`。

## 文件结构
├── broadcast.py              # 主程序

├── daily-meow-broadcast.yml  # GitHub Actions 工作流

├── content/

│   ├── channel_name.txt      # 频道名称

│   └── daily_message.txt     # 广播文案（支持 {date} 占位符）

└── README.md
├── broadcast.py              # 主程序

├── daily-meow-broadcast.yml  # GitHub Actions 工作流

├── content/

│   ├── channel_name.txt      # 频道名称

│   └── daily_message.txt     # 广播文案（支持 {date} 占位符）

└── README.md
## 保活机制

- 每次 workflow 运行后自动更新 `.keepalive-meow` 文件并 push
- 即使广播失败也照常保活（`if: always()`）
- 保活 push 失败不影响 workflow 主流程（`continue-on-error: true`）
- 防止 GitHub 在仓库 60 天无 commit 时自动禁用定时任务

## 手动测试

仓库页面 → **Actions → Daily MeoW Broadcast → Run workflow** → 点击运行按钮。

查看日志中 `[DEBUG]` 行确认配置读取状态：
