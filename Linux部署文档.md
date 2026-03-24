# Linux 部署文档（新服务器）

适用项目：`monitor`（Django + Vue2 + MySQL + Nginx）  
建议系统：`Ubuntu 22.04 LTS`

---

## 0. 资源需求（建议）

- 最低：2 vCPU / 4 GB RAM / 40 GB SSD
- 推荐：4 vCPU / 8 GB RAM / 80 GB SSD
- 数据量大（长期存储/高并发）：8 vCPU / 16 GB RAM / 200 GB SSD

其他：
- 带宽建议 ≥ 5 Mbps
- 需要放行端口：`80`（HTTP）、`443`（HTTPS 可选）、`5000`（后端内网）、`8088`（TCP 接收服务，默认）、MySQL 端口（按实际配置，如 `3306`/`33060`）

---

## 1. 服务器初始化

```bash
sudo apt update && sudo apt upgrade -y
sudo timedatectl set-timezone Asia/Shanghai
sudo apt install -y curl wget vim unzip build-essential ca-certificates
```

可选：创建部署用户（推荐）

```bash
sudo useradd -m -s /bin/bash deploy
sudo passwd deploy
sudo usermod -aG sudo deploy
```

---

## 2. 安装运行环境

### 2.1 Python 与系统依赖

> `mysqlclient` 依赖系统库，必须先装。

```bash
sudo apt install -y python3 python3-pip python3-venv
sudo apt install -y default-libmysqlclient-dev pkg-config
```

### 2.2 Node.js（前端打包）

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
node -v
npm -v
```

### 2.3 Nginx

```bash
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

---

## 3. 上传代码（本地包部署）

将本地项目打包上传到服务器，例如：

```bash
# 在本地执行
zip -r qixiangjiance.zip qixiangjiance
scp qixiangjiance.zip deploy@<server>:/home/deploy/
```

在服务器解压：

```bash
cd /home/deploy
unzip qixiangjiance.zip
cd /home/deploy/qixiangjiance/monitor
```

---

## 4. 后端部署（Django）

```bash
cd /home/deploy/qixiangjiance/monitor/backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

> 说明：`gunicorn` 不在当前 `requirements.txt` 中，需单独安装（如上）。

### 4.1 Python 依赖清单（来自 requirements.txt）

当前核心依赖包括：
- `Django==3.2.25`
- `mysqlclient==2.2.7`
- `PyMySQL==1.0.2`
- `requests==2.32.5`
- `openpyxl==3.1.5`
- `beautifulsoup4`（邮箱正文解析依赖）

建议部署后确认：

```bash
python -c "import django,requests,MySQLdb; print('django/requests/mysql ok')"
python -c "import openpyxl,bs4; print('openpyxl/bs4 ok')"
```

### 4.2 配置数据库（必须）

编辑：`/home/deploy/qixiangjiance/monitor/backend/api_server/settings.py`

确认以下参数为你的生产环境配置：
- `DATABASES.default.NAME`
- `DATABASES.default.USER`
- `DATABASES.default.PASSWORD`
- `DATABASES.default.HOST`
- `DATABASES.default.PORT`

### 4.3 邮件模块配置（新增）

编辑：`/home/deploy/qixiangjiance/monitor/backend/api_server/settings.py`

默认配置：
- `EMAIL_IMAP_HOST = 'imap.163.com'`
- `EMAIL_IMAP_PORT = 993`
- `EMAIL_ATTACHMENT_DIR = 'downloads'`
- `EMAIL_MAX_WORKERS = 16`
- `EMAIL_MAX_QUERY_DAYS = 730`
- `EMAIL_DOWNLOAD_RETRY_TIMES = 3`
- `EMAIL_IMAP_TIMEOUT = 30`

建议：
- `EMAIL_ATTACHMENT_DIR` 建议配置绝对路径（如 `/data/email_downloads`），并确保磁盘空间充足。
- 当前代码已兼容相对路径（默认 `downloads`，实际落在 `backend/downloads`），但生产建议使用绝对路径。
- 放行出站 993 端口（IMAP）。

### 4.4 数据库迁移与初始化（必须）

```bash
cd /home/deploy/qixiangjiance/monitor/backend
source .venv/bin/activate
python manage.py makemigrations
python manage.py migrate
```

> 若历史库中缺少邮箱表，可单独执行：

```bash
python manage.py makemigrations email
python manage.py migrate email
```

### 4.5 启动后端（临时验证）

```bash
cd /home/deploy/qixiangjiance/monitor/backend
source .venv/bin/activate
gunicorn api_server.wsgi:application -b 127.0.0.1:5000 -w 4 --timeout 120
```

---

## 5. 前端部署（Vue）

```bash
cd /home/deploy/qixiangjiance/monitor/frontend/web
npm ci
npm run build
```

构建产物：
- `/home/deploy/qixiangjiance/monitor/frontend/web/dist`

---

## 6. Nginx 配置（前后端同域）

新建配置：

```bash
sudo vim /etc/nginx/sites-available/qixiangjiance.conf
```

写入：

```nginx
server {
    listen 80;
    server_name _;

    client_max_body_size 50m;

    root /home/deploy/qixiangjiance/monitor/frontend/web/dist;
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
sudo ln -s /etc/nginx/sites-available/qixiangjiance.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 7. systemd 托管后端（推荐）

> 如需启用 TCP 接收服务，还需单独托管 `apps.collect_data.run_collect_data`（默认监听 `0.0.0.0:8088`）。
> 可另建服务：`qixiangjiance-collector.service`，执行命令：
> `/home/deploy/qixiangjiance/monitor/backend/.venv/bin/python -m apps.collect_data.run_collect_data`


创建服务：

```bash
sudo vim /etc/systemd/system/qixiangjiance-backend.service
```

内容：

```ini
[Unit]
Description=Qixiangjiance Django Backend
After=network.target

[Service]
User=deploy
Group=deploy
WorkingDirectory=/home/deploy/qixiangjiance/monitor/backend
Environment="PATH=/home/deploy/qixiangjiance/monitor/backend/.venv/bin"
ExecStart=/home/deploy/qixiangjiance/monitor/backend/.venv/bin/gunicorn api_server.wsgi:application -b 127.0.0.1:5000 -w 4 --timeout 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

生效并启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable qixiangjiance-backend
sudo systemctl start qixiangjiance-backend
sudo systemctl status qixiangjiance-backend
```

日志：

```bash
journalctl -u qixiangjiance-backend -f
```

---

## 8. 数据库性能（建议立即执行）

趋势/轨迹查询建议每张业务时序表有复合索引：
- `(devid, time)`

如未执行，请先补索引后再压测。

---

## 9. 更新发布流程（本地包更新）

```bash
# 在本地打包并上传
zip -r qixiangjiance.zip qixiangjiance
scp qixiangjiance.zip deploy@<server>:/home/deploy/

# 在服务器解压覆盖
cd /home/deploy
unzip -o qixiangjiance.zip

# 后端
cd /home/deploy/qixiangjiance/monitor/backend
source .venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
python manage.py migrate
sudo systemctl restart qixiangjiance-backend

# 前端
cd /home/deploy/qixiangjiance/monitor/frontend/web
npm ci
npm run build
sudo systemctl reload nginx
```

---

## 10. 生产环境检查清单

1. `DEBUG=False`
2. `ALLOWED_HOSTS` 仅保留真实域名/IP
3. 数据库不要使用 root，改最小权限账号
4. 开启 HTTPS（Certbot）
5. 密钥/数据库密码改环境变量
6. 配置数据库备份与日志轮转

---

## 11. 常见故障排查

### 11.1 页面可开但接口 502
- `systemctl status qixiangjiance-backend`
- `journalctl -u qixiangjiance-backend -f`
- 检查 Nginx `proxy_pass` 是否 `127.0.0.1:5000`

### 11.2 导出/趋势请求超时
- 提高 gunicorn `--timeout`
- 提高 Nginx `proxy_read_timeout`
- 检查 `(devid,time)` 索引是否已生效

### 11.3 静态资源 404
- 检查 Nginx `root` 是否为 `frontend/web/dist`
- 重新执行 `npm run build`
- `sudo systemctl reload nginx`
