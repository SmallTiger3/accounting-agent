# WeChat Accounting Bot (OpenClaw)

微信聊天记账机器人，基于 OpenClaw 框架 + 微信官方 ClawBot（iLink）通道 + DeepSeek 大模型解析 + PostgreSQL 存储。

原 FastAPI 全栈记账应用已下线（代码见 git 历史），当前仓库只维护 OpenClaw 记账机器人。

## 仓库结构

```
openclaw-bot/
├── acct.py                          # 数据层 CLI（部署于服务器 /opt/openclaw-accounting/acct.py）
└── skills/
    └── wechat-accounting/
        └── SKILL.md                 # OpenClaw 记账技能（部署于 ~/.openclaw/workspace/skills/）
```

## 功能

- 记支出 / 记收入（自然语言，如「午餐 28 元」「发工资 5000」）
- 月度汇总（含各分类小计，支持查历史月份）
- 最近记录查询
- 删除记错的账
- 首次发消息自动建号（多用户隔离，按微信 ID）

## 部署位置（服务器 101.200.232.229）

| 组件 | 路径 |
|------|------|
| 数据层脚本 | `/opt/openclaw-accounting/acct.py` |
| 记账技能 | `/root/.openclaw/workspace/skills/wechat-accounting/SKILL.md` |
| OpenClaw 网关 | systemd 服务 `openclaw-gateway`，配置 `/root/.openclaw/openclaw.json` |
| 登录重启脚本 | `/root/.openclaw/restart-login.sh`（微信二维码过期时重新生成） |

## 数据表

存于 PostgreSQL 库 `accounting_agent`：

- `bot_users` — 微信用户（wx_id 唯一）
- `bot_transactions` — 收支记录（类型/金额/分类/备注/时间）

> 注意：库中另有旧 Web 应用遗留的表（users/transactions 等），已停用但未删除。

## 运维速查

```bash
# 网关状态
systemctl status openclaw-gateway
openclaw channels status --probe

# 微信二维码过期后重新生成
bash /root/.openclaw/restart-login.sh

# 数据层命令
python3 /opt/openclaw-accounting/acct.py ensure-user <wx_id>
python3 /opt/openclaw-accounting/acct.py add <user_id> expense 28.5 餐饮 午餐
python3 /opt/openclaw-accounting/acct.py month <user_id>
python3 /opt/openclaw-accounting/acct.py recent <user_id> 10
python3 /opt/openclaw-accounting/acct.py delete <user_id> <id>
```

## 修改发布流程

改 `acct.py` 或 `SKILL.md` 后：提交推送本仓库，并同步覆盖服务器上对应文件，然后无需重启网关（技能文件即时生效；acct.py 无状态）。
