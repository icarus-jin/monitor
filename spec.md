## 设计风格
style_demo.png是首页的数据展示参考，目前集成什么插件，还未知
整体界面的ui背景设计要参考style_demo.png

## 代码要求
需要考虑系统的一些安全性，比如系统访问前必须登录，然后使用seesion等

## 通用 utils 规范
通用工具统一放在后端 `utils` 目录（`backend/utils/`），包括：
- **token**：Token 存储与验证
- **log**：日志记录
- **message**：统一 API 响应格式（success/error）
- **json_utils**：请求体解析（parse_body/get_param），支持 JSON 与 form-urlencoded

详见 `架构说明.md`。

## 测试要求
测试需要包含后端api的测试和前端页面的测试，需要保证质量

## 使用说明
系统设计方面，你可以自行决策，但是针对使用电脑和登录等方面决策可以咨询我
自动完善对应的说明文档，方便项目的信息查阅和文档整理



