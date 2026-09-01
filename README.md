# 个人资产管理系统

纯本地的个人资产管理系统，管理实体资产、虚拟资产和订阅，支持自定义字段与分类。所有数据存储在本地 SQLite 文件中，不依赖任何外部网络服务。

## 功能概览

| 模块 | 说明 |
|------|------|
| 统一资产管理 | 基于资产类型的动态表单，支持实体、虚拟、订阅三类资产 |
| 资产类型管理 | 自定义资产类型及字段配置（text/number/date/select/computed/relation） |
| 分类管理 | 按资产类型组织的树形分类体系 |
| 订阅周期管理 | 预置及自定义订阅周期（日付/月付/年付等） |
| 动态表单引擎 | 根据字段配置自动渲染表单，支持 API 数据源、关联字段、计算字段 |
| 表达式引擎 | 计算字段支持四则运算表达式，自动联动计算 |
| 账单导入 | 支持 CSV/JSON 等多种格式导入 |
| 交易管理 | 资产相关交易记录，含独立分类体系 |
| 账户管理 | 用户账户与认证 |
| 审计日志 | 操作记录追踪 |
| Dashboard | 资产总览与统计图表 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11+ / FastAPI / SQLAlchemy 2.0 / Pydantic 2.0 |
| 前端 | React 18 / TypeScript / Vite / Ant Design 5 / Tailwind CSS |
| 数据请求 | TanStack Query (React Query) / Axios |
| 状态管理 | Zustand |
| 图表 | Recharts |
| 国际化 | i18next / react-i18next |
| 测试 | pytest (后端) / Vitest (前端) / Playwright (E2E) |
| 数据库 | SQLite (WAL 模式) |
| 环境管理 | Conda |

## 项目结构

```
assetSubManager/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口，路由注册
│   │   ├── database.py          # 数据库初始化、迁移、系统预设
│   │   ├── config.py            # 配置加载
│   │   ├── auth.py              # 认证模块
│   │   ├── orm_base.py          # SQLAlchemy ORM 基类
│   │   ├── models/              # Pydantic 数据模型
│   │   ├── repositories/        # 数据访问层
│   │   ├── services/            # 业务逻辑层
│   │   └── routers/             # API 路由
│   └── tests/                   # 后端测试
├── web/
│   ├── src/
│   │   ├── App.tsx              # 路由配置
│   │   ├── main.tsx             # 入口
│   │   ├── pages/               # 页面组件
│   │   ├── components/          # 通用组件
│   │   │   ├── DynamicForm/     # 动态表单引擎
│   │   │   ├── layout/          # 布局组件
│   │   │   └── common/          # 通用小组件
│   │   ├── api/                 # API 客户端与 Hooks
│   │   └── types/               # TypeScript 类型定义
│   └── package.json
├── data/                        # 数据目录（SQLite 文件、附件）
├── Makefile                     # 开发命令
└── requirements.txt             # Python 依赖
```

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- Conda（推荐）
- pnpm

### 安装

```bash
# 1. 创建 conda 环境
conda env create -f backend/environment.yml
conda activate asset-manager

# 2. 安装后端依赖
pip install -r requirements.txt

# 3. 安装前端依赖
cd web && pnpm install
```

### 开发模式

```bash
# 终端 1：启动后端（端口 8080）
make dev
# 或: conda run -n asset-manager uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8080

# 终端 2：启动前端（端口 5173）
make dev-web
# 或: cd web && pnpm dev
```

访问 http://localhost:5173 使用应用。

### 生产部署

```bash
# 构建前端并部署到后端静态目录
make deploy-web

# 启动生产服务
conda run -n asset-manager uvicorn backend.app.main:app --host 0.0.0.0 --port 8080
```

访问 http://localhost:8080 使用应用。

### 运行测试

```bash
# 后端测试
make test
# 或: conda run -n asset-manager pytest backend/tests -v

# 前端测试
cd web && pnpm test

# E2E 测试
cd web && pnpm e2e
```

## API 概览

所有 API 前缀为 `/api/v1`，需认证。

| 端点 | 说明 |
|------|------|
| `/assets/` | 统一资产 CRUD |
| `/asset-types/` | 资产类型管理 |
| `/asset-types/{type_id}/categories/` | 类型级分类管理 |
| `/subscription-periods/` | 订阅周期管理 |
| `/transactions/` | 交易记录 |
| `/transaction-categories/` | 交易分类 |
| `/accounts/` | 账户管理 |
| `/dashboard/` | 仪表板统计 |
| `/import/` `/export/` | 数据导入导出 |
| `/audit-log/` | 审计日志 |
| `/auth/login` | 登录认证 |

## 数据模型

### 统一资产架构

系统采用统一的资产模型，通过 `asset_types` 定义资产类型及其字段配置：

- **asset_types**: 资产类型定义（如"订阅"、"游戏账号"等）
- **assets**: 统一资产表，关联资产类型
- **categories**: 统一分类表，按资产类型组织
- **category_fields**: 分类级自定义字段
- **asset_field_values / asset_values**: 资产自定义字段值

### 预置资产类型

系统内置三种资产类型，启动时自动初始化字段配置：

1. **实体资产** (`physical`): 购买日期、价格、位置、序列号、保修期等
2. **虚拟资产** (`virtual`): 账号、密码、许可证号、有效期、平台等
3. **订阅** (`subscription`): 订阅周期（API 动态加载）、下次续费、自动续费、续费金额等

## 开发约定

- **TDD** — 先写测试再实现
- **避免低级错误** — UI 修改完整考虑所有元素

## 许可

MIT License
