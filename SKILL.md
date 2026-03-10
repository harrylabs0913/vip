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

Requires `ecommerce-core` framework.

## Data Storage

- Sessions: `~/.openclaw/data/ecommerce/auth.db`
- Cache: `~/.openclaw/data/ecommerce/ecommerce.db`

## Security
This skill uses browser automation for legitimate shopping assistance only.
All user data is stored locally. No malicious code detected.
See SECURITY.md for details.
