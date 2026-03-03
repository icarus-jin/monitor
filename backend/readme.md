# 气象监测系统 - 后端

基于 Django 的后端 API 服务，负责用户认证、用户管理、设备信息查询与设备数据查询。

## 环境要求

- Python 3.9+
- MySQL 5.7+
- Django 3.2

## 快速开始

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 配置数据库

编辑 `api_server/settings.py` 中的 `DATABASES` 配置（含业务库与原始库连接）。

3. 执行迁移

```bash
python manage.py migrate
```

4. 初始化用户模拟数据

```bash
python manage.py init_users
```

5. 启动服务（端口需与前端代理一致）

```bash
python manage.py runserver 5000
```

## API 概览

### 用户管理

| 接口 | 方法 | 说明 |
|------|------|------|
| `/user/login/` | POST | 登录 |
| `/user/user_list/` | GET | 用户列表（分页、搜索） |
| `/user/register/` | POST | 新增用户 |
| `/user/register/` | PUT | 编辑用户 |
| `/user/register/` | DELETE | 删除用户（软删除） |
| `/user/batch_delete/` | POST | 批量删除用户 |
| `/user/reset_password/` | PUT/GET | 重置密码 |

### 设备与数据查询

| 接口 | 方法 | 说明 |
|------|------|------|
| `/device/list/` | GET | 设备列表（分页、筛选） |
| `/device/simple_list/` | GET | 设备简要列表 |
| `/device/data/latest/` | GET | 设备最新数据 |
| `/device/data/trend/` | GET | 设备趋势数据 |
| `/device/track/` | GET | 设备轨迹 |
| `/device/overview/` | GET | 总览统计 |
| `/device/map/tile/` | GET | 地图瓦片代理 |

> 当前阶段设备信息与业务数据均从原始库只读查询，不支持新增/编辑/删除写入。

## 默认账号

- 超级管理员：`admin / admin123`
- 客户账号：`zhangsan / 123456`、`lisi / 123456`、`wangwu / 123456`、`zhaoliu / 123456`

## 通用工具模块（`backend/utils`）

- `token.py`：Token 生成、存储与校验
- `log.py`：日志记录
- `message.py`：统一响应封装（`success/error`）
- `json_utils.py`：请求体解析与参数提取（兼容 JSON / form-urlencoded）
