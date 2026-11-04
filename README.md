# 每日 MeoW 广播失败通知

每天北京时间 07:20 将 `content/daily_message.txt` 广播到指定 MeoW 频道。广播成功时不发送任何结果通知；只有广播请求失败、接口报告失败或缺少必要配置时，才向 `https://api.chuckfang.com/shangguan/` 发送失败通知。

失败通知包含频道名称、广播内容、失败原因和北京时间。通知使用该接口文档支持的 `application/x-www-form-urlencoded` POST，正文包括换行字段，避免把通知内容拼进 URL 路径。

## 配置

在 GitHub 仓库 **Settings → Secrets and variables → Actions** 添加 Repository secrets：

- `CHANNEL_ID`：正式频道 ID
- `UNION_ID`：频道创建者的 MeoW unionId

把 `content/channel_name.txt` 改成实际频道名称。编辑 `content/daily_message.txt` 设置日常文案；文案可用 `{date}` 插入北京时间日期。

不要将频道 ID 或 unionId 提交到仓库。广播 API 的文档端点使用 HTTP，并通过 URL 查询参数接收这两个值；GitHub Secrets 保护仓库配置，不会加密接口请求传输。

## 计划

GitHub Actions 使用 UTC cron `23:20`，对应北京时间每天 07:20。工作流也支持手动触发。广播接口文档标注每日最多 3 次、广播时间为 06:00–23:00、调用间隔至少 30 分钟。
