# smartdog 智能狗

一个宠物主人交流社区 Web 应用。养宠人可以注册账号、发布帖子、评论、点赞、互相关注，并为自己的宠物建立档案。

## 功能

- 注册 / 登录 / 退出（邮箱 + 密码，密码 PBKDF2 加盐哈希存储）
- 首页帖子流（「最新」与「热门」排序）
- 发布帖子（标题 + 正文 + 图片上传）
- 帖子详情与评论
- 帖子点赞 / 取消点赞
- 个人主页 + 宠物档案（名字、品种、生日、简介、头像）
- 关注 / 取关，以及「关注动态」流

## 技术栈

- 后端：FastAPI + SQLAlchemy 2.0 + SQLite
- 前端：Jinja2 服务端渲染 + 原生 JS + Tailwind CSS（CDN）
- 认证：签名 session cookie（HTTP-only、SameSite=Lax）
- 图片：上传至本地 `uploads/` 目录并静态托管

## 快速开始

```bash
# 1. 创建虚拟环境并安装依赖
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2.（可选）写入演示数据
.venv/bin/python seed.py

# 3. 启动服务
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

浏览器访问 <http://127.0.0.1:8000>。演示账号（若已执行 seed.py）：`alice@example.com` / `secret123`。

## 测试

```bash
.venv/bin/python -m pytest -q
```

## 项目结构

```
smartdog/
├── app/
│   ├── main.py            # FastAPI 入口
│   ├── config.py          # 配置
│   ├── database.py        # SQLAlchemy 引擎 / 会话
│   ├── models.py          # 数据模型
│   ├── security.py        # 密码哈希 + 会话令牌
│   ├── deps.py            # 依赖（当前用户、Cookie）
│   ├── uploads.py         # 图片上传
│   ├── templating.py      # Jinja2 模板与过滤器
│   ├── routers/
│   │   ├── auth.py        # 注册 / 登录 / 退出
│   │   ├── posts.py       # 帖子 / 评论 / 点赞
│   │   └── users.py       # 主页 / 宠物档案 / 关注
│   ├── templates/         # Jinja2 页面
│   └── static/            # CSS / JS
├── uploads/               # 用户上传图片（运行时生成）
├── tests/                 # pytest
├── requirements.txt
└── seed.py
```

## 配置

通过环境变量覆盖默认配置：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `SMARTDOG_DATABASE_URL` | `sqlite:///./smartdog.db` | 数据库连接串 |
| `SMARTDOG_SECRET_KEY` | `dev-secret-change-me-in-production` | 会话签名密钥（生产环境务必修改） |

## 说明

- 认证 Cookie 设置了 `SameSite=Lax`，可缓解跨站 POST 的 CSRF 风险。
- 生产部署请设置强随机 `SMARTDOG_SECRET_KEY`，并考虑将图片上传改为对象存储。
