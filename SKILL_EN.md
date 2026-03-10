---
name: vip-ec
description: "CLI tool for VIP.com e-commerce platform - search products, browse sales events, and explore brand zones"
---

# VIP.com Skill

A command-line interface for VIP.com (唯品会), one of China's leading flash sale e-commerce platforms. This skill enables automated product search, sales event browsing, and brand zone exploration.

## Description

VIP.com is a comprehensive CLI tool designed for interacting with the VIP.com flash sale platform. It provides product search capabilities with intelligent caching, access to ongoing sales events, and brand zone browsing. The tool is ideal for flash sale shopping, brand discovery, and deal hunting.

### Use Cases

- **Flash Sale Shopping**: Search for products during flash sales
- **Sales Events**: Browse ongoing and upcoming sales events
- **Brand Discovery**: Explore brands by category
- **Price Comparison**: Compare prices across different sales
- **Deal Hunting**: Find the best deals on VIP.com

## Installation

```bash
# Install the ecommerce-core dependency first
pip install -r ../ecommerce-core/requirements.txt

# Install the VIP skill
pip install -e .
```

## Usage

### Commands

#### Search Products
```bash
vip search "连衣裙"
vip search "运动鞋" --page 2 --limit 20
```

Search for products by keyword. Supports pagination and result limit control.

- **Arguments:**
  - `query` - Search keyword (required)
  - `--page` - Page number (default: 1)
  - `--limit` - Number of results per page (default: 20)

#### Login
```bash
vip login
```

Authenticate with VIP.com using QR code. Opens a browser window with a QR code that can be scanned with the VIP.com mobile app. Session tokens are securely stored for future use.

#### Sales Events
```bash
vip sale
```

Browse ongoing sales events and flash sales.

#### Brand Zone
```bash
vip brand
vip brand women
vip brand men
vip brand kids
```

Explore brands by category.

- **Arguments:**
  - `category` - Category name (optional, default: all)

## Features

- **Product Search with Caching**: Fast repeated searches using intelligent caching to reduce API calls and improve response time
- **QR Code Login**: Secure browser-based authentication via QR code scanning
- **Sales Events**: Access to ongoing and upcoming flash sales
- **Brand Zone**: Browse brands by category
- **Anti-Detection Browser Automation**: Stealth browser automation that mimics human behavior to avoid detection
- **Session Management**: Persistent authentication tokens for seamless re-authentication

## Examples

### Basic Product Search
```bash
# Search for a specific product
vip search "handbag"

# Search with custom pagination
vip search "sneakers" --page 3 --limit 50
```

### Sales Events
```bash
# Get all ongoing sales events
vip sale
```

### Brand Zone
```bash
# Get all brands
vip brand

# Get brands by category
vip brand women
vip brand men
vip brand kids
vip brand beauty
```

### Authentication
```bash
# Initialize login (one-time setup)
vip login
# Browser opens with QR code - scan with VIP app
```

## Technical Details

### Data Storage

| Data Type | Location |
|-----------|----------|
| Session Tokens | `~/.openclaw/data/ecommerce/auth.db` |
| Search Cache | `~/.openclaw/data/ecommerce/ecommerce.db` |

### Dependencies

- `ecommerce-core` framework (required)
- Browser automation with anti-detection capabilities
- SQLite for data persistence

### Rate Limiting

The tool implements caching and rate limiting to respect VIP.com's terms of service and avoid account restrictions.

### Anti-Detection

All browser automation includes:
- Random delay intervals between actions
- Human-like scrolling and navigation patterns
- User agent rotation
- Request fingerprint randomization
