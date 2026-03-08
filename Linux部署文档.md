# Linux 部署文档（新服务器）

> 适用项目：`monitor`（Django + Vue2 + Nginx）
> 
> 建议系统：Ubuntu 22.04 LTS

---

## 1. 服务器初始化

```bash
sudo apt update && sudo apt upgrade -y
sudo timedatectl set-timezone Asia/Shanghai
sudo apt install -y git curl wget vim unzip build-essential
```

创建运行用户（可选但推荐）：

```bash
sudo useradd -m -s /bin/bash deploy
sudo passwd deploy
sudo usermod -aG sudo deploy
```

---

## 2. 安装运行环境

### 2.1 Python 环境

```bash
sudo apt install -y python3 python3-pip python3-venv
sudo apt install -y default-libmysqlclient-dev pkg-config
```

### 2.2 Node.js 环境（前端构建）

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

## 3. 上传/拉取项目代码

```bash
cd /home/deploy
git clone <你的仓库地址> qixiangjiance
cd qixiangjiance/monitor
```

---

## 4. 后端部署（Django）

进入后端目录并创建虚拟环境：

```bash
cd /home/deploy/qixiangjiance/monitor/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

> 说明：当前 `requirements.txt` 同时有 Django 3.2 和 settings 头注释是 4.2 生成，建议你部署前统一版本（建议固定到 Django 3.2.25，保持与现有代码一致）。

### 4.1 修改数据库配置

当前 `api_server/settings.py` 写死了数据库地址与密码，建议改为环境变量方式（生产强烈建议）。

### 4.2 启动 Gunicorn（临时测试）

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

构建产物在：

- `/home/deploy/qixiangjiance/monitor/frontend/web/dist`

---

## 6. Nginx 配置（前后端同域）

创建配置文件：

```bash
sudo vim /etc/nginx/sites-available/qixiangjiance.conf
```

写入以下内容（按你的域名/路径调整）：

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

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/qixiangjiance.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 7. systemd 托管 Django（推荐）

创建服务文件：

```bash
sudo vim /etc/systemd/system/qixiangjiance-backend.service
```

内容如下：

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

启动并设置开机自启：

```bash
sudo systemctl daemon-reload
sudo systemctl enable qixiangjiance-backend
sudo systemctl start qixiangjiance-backend
sudo systemctl status qixiangjiance-backend
```

查看日志：

```bash
journalctl -u qixiangjiance-backend -f
```

---

## 8. 发布流程（后续更新）

```bash
cd /home/deploy/qixiangjiance
git pull

# 后端
cd monitor/backend
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart qixiangjiance-backend

# 前端
cd ../frontend/web
npm ci
npm run build
sudo systemctl reload nginx
```

---

## 9. 生产建议（务必执行）

1. `DEBUG=False`
2. `ALLOWED_HOSTS` 仅保留实际域名/IP
3. 数据库账号不要用 root，改专用最小权限账号
4. 开启 HTTPS（可用 Certbot）
5. 将密钥、数据库密码改为环境变量
6. 定期备份数据库

---

## 10. 常见排查

### 10.1 前端能打开但接口 502
- 检查 Gunicorn 是否存活：`systemctl status qixiangjiance-backend`
- 检查 Nginx 反代地址是否是 `127.0.0.1:5000`

### 10.2 接口超时
- 增大 Gunicorn `--timeout`
- 增大 Nginx `proxy_read_timeout`
- 检查数据库慢查询与索引（重点：`devid,time` 复合索引）

### 10.3 静态资源 404
- 检查 Nginx `root` 是否指向 `frontend/web/dist`
- 重新执行 `npm run build`
