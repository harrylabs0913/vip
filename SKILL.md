# VIP (唯品会) Skill

CLI tool for VIP.com e-commerce platform.

## Commands

### Search Products
```bash
vip search "连衣裙"
vip search "运动鞋" --page 2 --limit 20
```

### Login
```bash
vip login
```
Opens browser with QR code for authentication.

### Sales Events
```bash
vip sale
```
Query ongoing sales events.

### Brand Zone
```bash
vip brand
vip brand women
vip brand men
```
Query brands by category.

## Features

- Product search with caching
- QR code login
- Sales events query
- Brand zone browsing
- Anti-detection browser automation

## Dependencies

- Python 3.9+
- `playwright>=1.40.0` (浏览器自动化)
- `cryptography>=42.0.0` (加密库)
- 安装命令: `pip install -r requirements.txt`

## 数据存储与安全

### 存储位置
- **主目录**: `~/.openclaw/data/vip/` (加密存储)
- **会话数据**: `cookies.enc` (AES-256 加密存储)
- **缓存数据**: `vip.db` (SQLite数据库)
- **加密密钥**: `.key` (权限 600)

### 隐私保护
1. **加密存储**: 所有敏感数据使用 Fernet 加密
2. **用户同意**: 首次运行需要明确同意数据使用条款
3. **数据控制**: 支持一键清除所有个人数据
4. **透明审计**: 可查看所有存储的文件和权限

### 隐私控制命令
```bash
# 查看隐私信息
vip privacy info

# 清除所有个人数据
vip privacy clear

# 导出加密数据（备份）
vip privacy export
```

## Security
This skill uses browser automation for legitimate shopping assistance only.
All user data is encrypted and stored locally. No data transmission to external servers.
See SECURITY.md for details.
