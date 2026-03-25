# Linux 部署文档（Git 部署，deploy 用户）

适用项目：`monitor`（Django + Vue2 + MySQL + Nginx）  
建议系统：`Ubuntu 22.04 LTS`

> 说明：本文按 `deploy` 用户 + `git` 拉取代码方式编写。

---

## 0. 资源需求（建议）

- 最低：2 vCPU / 4 GB RAM / 40 GB SSD
- 推荐：4 vCPU / 8 GB RAM / 80 GB SSD
- 数据量大（长期存储/高并发）：8 vCPU / 16 GB RAM / 200 GB SSD

其他：
- 带宽建议 ≥ 5 Mbps
- 需要放行端口：`80`（HTTP）、`443`（HTTPS 可选）、`5000`（后端内网）、`8088`（TCP 接收服务，默认）、MySQL 端口（按实际配置，如 `3306`/`33060`）

---

## 1. 服务器初始化（无预装环境）

```bash
# 可选：切换 APT 为国内镜像（以清华源为例，Ubuntu 22.04）
cp /etc/apt/sources.list /etc/apt/sources.list.bak
cat > /etc/apt/sources.list << 'EOF'
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-updates main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-backports main restricted universe multiverse
deb http://security.ubuntu.com/ubuntu/ jammy-security main restricted universe multiverse
EOF

apt update && apt upgrade -y
timedatectl set-timezone Asia/Shanghai
apt install -y curl wget vim unzip build-essential ca-certificates git

# 创建部署用户（已存在可跳过）
id deploy || useradd -m -s /bin/bash deploy
usermod -aG sudo deploy
```

---

## 2. 安装运行环境

### 2.1 Python 与系统依赖

> `mysqlclient` 依赖系统库，必须先装。

```bash
apt install -y python3 python3-pip python3-venv
apt install -y default-libmysqlclient-dev pkg-config
```

### 2.2 Node.js（前端打包）

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# npm 使用国内源（淘宝镜像）
npm config set registry https://registry.npmmirror.com
node -v
npm -v
npm config get registry
```

### 2.3 Nginx

```bash
apt install -y nginx
systemctl enable nginx
systemctl start nginx
```

### 2.4 项目依赖说明（与代码同步）

- 后端依赖以 `backend/requirements.txt` 为准，部署统一执行：
  - `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`
- 前端依赖以 `frontend/web/package.json` 为准，部署统一执行：
  - `npm ci --registry=https://registry.npmmirror.com`

当前后端关键依赖（节选）：
- `Django==3.2.25`
- `mysqlclient==2.2.7`
- `PyMySQL==1.0.2`
- `requests==2.32.5`
- `openpyxl==3.1.5`

当前前端关键依赖（节选）：
- `vue@2.6.14`
- `vue-router@3.5.1`
- `axios@1.13.2`
- `element-ui@2.4.5`
- `cesium@1.138.0`
- `mars3d@3.11.0`
- `echarts@6.0.0`

---

## 3. 获取代码（Git）

### 3.1 首次部署

```bash
su - deploy
cd /home/deploy
git clone <你的仓库地址> qixiangjiance
cd /home/deploy/qixiangjiance
```

### 3.2 后续更新

```bash
cd /home/deploy/qixiangjiance
git pull
```

---

## 4. 后端部署（Django）

```bash
cd /home/deploy/qixiangjiance/backend
python3 -m venv .venv
source .venv/bin/activate

# pip 使用清华源
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install gunicorn -i https://pypi.tuna.tsinghua.edu.cn/simple
```

> 说明：`gunicorn` 不在当前 `requirements.txt` 中，需单独安装（如上）。

### 4.1 配置数据库（必须）

编辑：`/home/deploy/qixiangjiance/backend/api_server/settings.py`

确认以下参数为你的生产环境配置：
- `DATABASES.default.NAME`
- `DATABASES.default.USER`
- `DATABASES.default.PASSWORD`
- `DATABASES.default.HOST`
- `DATABASES.default.PORT`

### 4.2 邮件模块配置

编辑：`/home/deploy/qixiangjiance/backend/api_server/settings.py`

默认配置：
- `EMAIL_IMAP_HOST = 'imap.163.com'`
- `EMAIL_IMAP_PORT = 993`
- `EMAIL_ATTACHMENT_DIR = 'downloads'`
- `EMAIL_MAX_WORKERS = 16`
- `EMAIL_MAX_QUERY_DAYS = 730`
- `EMAIL_DOWNLOAD_RETRY_TIMES = 3`
- `EMAIL_IMAP_TIMEOUT = 30`

建议：
- `EMAIL_ATTACHMENT_DIR` 建议改绝对路径（如 `/data/email_downloads`），并确保磁盘空间充足。
- 放行出站 993 端口（IMAP）。

### 4.3 数据库迁移与初始化（必须）

```bash
cd /home/deploy/qixiangjiance/backend
source .venv/bin/activate
python manage.py makemigrations
python manage.py migrate
python manage.py check
```

> 若历史库中缺少邮箱表，可单独执行：

```bash
python manage.py makemigrations email
python manage.py migrate email
```

### 4.4 启动后端（后台运行）

```bash
cd /home/deploy/qixiangjiance/backend
source .venv/bin/activate
nohup gunicorn api_server.wsgi:application -b 127.0.0.1:5000 -w 4 --timeout 120 > /home/deploy/qixiangjiance/backend/logs/gunicorn.out 2>&1 &
```

查看进程：

```bash
ps -ef | grep gunicorn
```

---

## 5. 前端部署（Vue，后台运行）

```bash
cd /home/deploy/qixiangjiance/frontend/web
npm ci --registry=https://registry.npmmirror.com

# 方式一（推荐生产）：构建后交给 Nginx 托管（天然后台）
npm run build

# 方式二（仅临时验证）：前端开发服务后台运行
nohup npm run serve -- --host 0.0.0.0 --port 8080 > /home/deploy/qixiangjiance/frontend/web/serve.out 2>&1 &
```

构建产物：
- `/home/deploy/qixiangjiance/frontend/web/dist`

---

## 6. Nginx 配置（前后端同域）

新建配置：

```bash
vim /etc/nginx/sites-available/qixiangjiance.conf
```

写入：

```nginx
server {
    listen 80;
    server_name _;

    client_max_body_size 50m;

    root /home/deploy/qixiangjiance/frontend/web/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 30s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

启用：

```bash
ln -s /etc/nginx/sites-available/qixiangjiance.conf /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

---

## 7. systemd 托管后端（推荐）

创建服务：

```bash
vim /etc/systemd/system/qixiangjiance-backend.service
```

内容：

```ini
[Unit]
Description=Qixiangjiance Django Backend
After=network.target

[Service]
User=deploy
Group=deploy
WorkingDirectory=/home/deploy/qixiangjiance/backend
Environment="PATH=/home/deploy/qixiangjiance/backend/.venv/bin"
ExecStart=/home/deploy/qixiangjiance/backend/.venv/bin/gunicorn api_server.wsgi:application -b 127.0.0.1:5000 -w 4 --timeout 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

生效并启动：

```bash
systemctl daemon-reload
systemctl enable qixiangjiance-backend
systemctl start qixiangjiance-backend
systemctl status qixiangjiance-backend
```

日志：

```bash
journalctl -u qixiangjiance-backend -f
```

> 如需启用 TCP 接收服务，还需单独托管 `apps.collect_data.run_collect_data`（默认监听 `0.0.0.0:8088`）。

TCP 接收服务（临时后台运行）示例：

```bash
cd /home/deploy/qixiangjiance/backend
source .venv/bin/activate
nohup python -m apps.collect_data.run_collect_data > /home/deploy/qixiangjiance/backend/logs/collector.out 2>&1 &
```

---

## 8. Git 更新发布流程（推荐）

```bash
# 1) 拉代码
cd /home/deploy/qixiangjiance
git pull

# 2) 后端更新
cd /home/deploy/qixiangjiance/backend
source .venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install gunicorn -i https://pypi.tuna.tsinghua.edu.cn/simple
python manage.py migrate
systemctl restart qixiangjiance-backend

# 3) 前端更新
cd /home/deploy/qixiangjiance/frontend/web
npm ci --registry=https://registry.npmmirror.com
npm run build
systemctl reload nginx
```

---

## 9. 生产环境检查清单

1. `DEBUG=False`
2. `ALLOWED_HOSTS` 仅保留真实域名/IP
3. 数据库不要使用 root，改最小权限账号
4. 开启 HTTPS（Certbot）
5. 密钥/数据库密码改环境变量
6. 配置数据库备份与日志轮转

---

## 10. 常见故障排查

### 10.1 页面可开但接口 502
- `systemctl status qixiangjiance-backend`
- `journalctl -u qixiangjiance-backend -f`
- 检查 Nginx `proxy_pass` 是否 `127.0.0.1:5000`

### 10.2 导出/趋势请求超时
- 提高 gunicorn `--timeout`
- 提高 Nginx `proxy_read_timeout`
- 检查 `(devid,time)` 索引是否已生效

### 10.3 静态资源 404
- 检查 Nginx `root` 是否为 `frontend/web/dist`
- 重新执行 `npm run build`
- `systemctl reload nginx`
