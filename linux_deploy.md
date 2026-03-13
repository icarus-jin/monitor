# Linux 部署文档（新服务器）

适用项目：`monitor`（Django + Vue2 + Nginx）

---

## 0. 资源需求（建议）

- 最低：2 vCPU / 4 GB RAM / 40 GB SSD
- 推荐：4 vCPU / 8 GB RAM / 80 GB SSD
- 数据量大（长期存储/高并发）：8 vCPU / 16 GB RAM / 200 GB SSD

其他：
- 带宽建议 ≥ 5 Mbps
- 需要放行端口：`80`、`443`（可选）、`5000`（后端内网）、TCP 接收端口（按配置）

---

## 1. 基础环境

```bash
sudo apt update && sudo apt upgrade -y
sudo timedatectl set-timezone Asia/Shanghai
sudo apt install -y curl wget vim unzip build-essential
```

---

## 2. 安装依赖

### 2.1 Python

```bash
sudo apt install -y python3 python3-pip python3-venv
sudo apt install -y default-libmysqlclient-dev pkg-config
```

### 2.2 Node.js

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### 2.3 Nginx

```bash
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

---

## 3. 上传代码（本地包部署）

```bash
# 本地打包并上传
zip -r qixiangjiance.zip qixiangjiance
scp qixiangjiance.zip deploy@<server>:/home/deploy/

# 服务器解压
cd /home/deploy
unzip qixiangjiance.zip
cd /home/deploy/qixiangjiance/monitor
```

---

## 4. 后端部署

```bash
cd /home/deploy/qixiangjiance/monitor/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

启动（临时）：

```bash
gunicorn api_server.wsgi:application -b 127.0.0.1:5000 -w 4 --timeout 120
```

---

## 5. 前端部署

```bash
cd /home/deploy/qixiangjiance/monitor/frontend/web
npm ci
npm run build
```

前端静态目录：`/home/deploy/qixiangjiance/monitor/frontend/web/dist`

---

## 6. Nginx 配置

创建 `/etc/nginx/sites-available/qixiangjiance.conf`：

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

## 7. systemd 托管后端

创建 `/etc/systemd/system/qixiangjiance-backend.service`：

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

执行：

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

## 8. 索引建议（趋势/轨迹）

每个业务时序表建议建 `(devid, time)` 复合索引。
