# 气象监测系统 - 后端

基于 Django 的后端 API 服务。

## 环境要求

- Python 3.9+
- MySQL 5.7+
- Django 3.2

## 快速开始

1. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

2. 配置数据库：编辑 `api_server/settings.py` 中的 `DATABASES` 配置

3. 执行迁移
   ```bash
   python manage.py migrate
   ```

4. 初始化用户模拟数据
   ```bash
   python manage.py init_users
   ```

5. 启动服务（需在 5000 端口，与前端 proxy 一致）
   ```bash
   python manage.py runserver 5000
   ```

## 用户管理 API

| 接口 | 方法 | 说明 |
|------|------|------|
| /user/login/ | POST | 登录 |
| /user/user_list/ | GET | 用户列表（分页、搜索） |
| /user/register/ | POST | 新增用户 |
| /user/register/ | PUT | 编辑用户 |
| /user/register/ | DELETE | 删除用户 |
| /user/batch_delete/ | POST | 批量删除用户 |
| /user/reset_password/ | PUT | 重置密码 |

## 默认账号

- 超级管理员：admin / admin123
- 客户账号：zhangsan / 123456、lisi / 123456、wangwu / 123456、zhaoliu / 123456
