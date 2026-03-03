# 气象监测系统 - 前端

基于 Vue 2 + Element UI 的前端管理端，提供登录、用户管理、设备管理与数据可视化页面。

## 环境要求

- Node.js 14+
- npm 6+

## 安装依赖

```bash
npm install
```

## 开发运行

```bash
npm run serve
```

默认通过 `vue.config.js` 将 `/api` 代理到后端 `http://localhost:5000`。

## 生产构建

```bash
npm run build
```

构建产物输出到 `dist/` 目录。

## 代码检查

```bash
npm run lint
```

## 目录说明

- `src/components/`：页面与业务组件
- `src/router/`：路由与登录态守卫
- `src/utils/`：前端工具函数
- `public/`：静态资源模板

## 登录态说明

前端路由守卫会检查 `sessionStorage.token`：

- 访问 `/login` 无需 token
- 其他页面未登录会自动跳转到 `/login`

## 相关文档

- 后端说明：`../backend/readme.md`
- 总体说明：`../spec.md`
