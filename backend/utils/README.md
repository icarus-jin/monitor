# 通用工具模块

通用工具统一放在本目录，供各 app 复用。

## 模块说明

| 模块 | 说明 |
|------|------|
| token | Token 存储与验证 |
| log | 日志记录 |
| message | 统一 API 响应格式（success/error） |
| json_utils | JSON 及请求体解析 |

## 使用示例

```python
from utils import token_store, success, error, parse_body, get_param, logger

# 响应
return success(data={'list': []})
return error('参数错误', code=400)

# 请求解析
body = parse_body(request)
name = get_param(body, 'name')

# 日志
logger.info('用户登录: %s', username)
```
