#!/usr/bin/env python3
"""唯品会购物助手 - 支持搜索、特卖活动、品牌专区"""

import argparse
import asyncio
import json
import os
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote, urlparse

try:
    from playwright.async_api import async_playwright, Page, Browser
except ImportError:
    print("请先安装依赖: pip install playwright && playwright install chromium")
    sys.exit(1)

# 配置
CONFIG_DIR = Path.home() / ".vip"
COOKIES_FILE = CONFIG_DIR / "cookies.json"
DB_FILE = CONFIG_DIR / "vip.db"
CONFIG_DIR.mkdir(exist_ok=True)

@dataclass
class Product:
    """商品数据类"""
    id: str
    title: str
    price: float
    original_price: Optional[float]
    shop: str
    url: str
    image: str
    discount: Optional[str] = None
    sales: Optional[str] = None

@dataclass
class SaleEvent:
    """特卖活动数据类"""
    id: str
    title: str
    description: str
    start_time: str
    end_time: str
    url: str
    image: str

@dataclass
class Brand:
    """品牌数据类"""
    id: str
    name: str
    logo: str
    url: str
    category: str

class VipClient:
    """唯品会客户端"""

    BASE_URL = "https://www.vip.com"
    SEARCH_URL = "https://search.vip.com"
    SALE_URL = "https://www.vip.com/special"
    BRAND_URL = "https://www.vip.com/brand"

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.db = self._init_db()

    def _init_db(self) -> sqlite3.Connection:
        """初始化SQLite数据库"""
        conn = sqlite3.connect(DB_FILE)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                title TEXT,
                price REAL,
                original_price REAL,
                shop TEXT,
                url TEXT,
                image TEXT,
                discount TEXT,
                sales TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT,
                price REAL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                start_time TEXT,
                end_time TEXT,
                url TEXT,
                image TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS brands (
                id TEXT PRIMARY KEY,
                name TEXT,
                logo TEXT,
                url TEXT,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        return conn

    async def init_browser(self, headless: bool = True):
        """初始化浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )

        # 加载cookies
        if COOKIES_FILE.exists():
            cookies = json.loads(COOKIES_FILE.read_text())
            await context.add_cookies(cookies)

        self.page = await context.new_page()

        # 注入反检测脚本
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()

    async def login(self):
        """扫码登录"""
        await self.init_browser(headless=False)

        print("正在打开唯品会登录页面...")
        await self.page.goto(f"{self.BASE_URL}/login")

        # 等待用户扫码登录
        print("请使用唯品会APP扫码登录...")
        await self.page.wait_for_selector(".user-info", timeout=120000)

        # 保存cookies
        cookies = await self.page.context.cookies()
        COOKIES_FILE.write_text(json.dumps(cookies))
        print(f"登录成功！Cookies已保存到 {COOKIES_FILE}")

        await self.close()

    async def search(self, keyword: str, page_num: int = 1) -> List[Product]:
        """搜索商品"""
        if not self.page:
            await self.init_browser()

        encoded_keyword = quote(keyword)
        url = f"{self.SEARCH_URL}?keyword={encoded_keyword}&page={page_num}"

        print(f"正在搜索: {keyword}")
        await self.page.goto(url, wait_until="networkidle")
        await asyncio.sleep(3)

        products = []

        try:
            # 等待商品列表加载
            await self.page.wait_for_selector(".goods-item", timeout=10000)
            items = await self.page.query_selector_all(".goods-item")

            for item in items[:20]:
                try:
                    # 提取商品信息
                    link_el = await item.query_selector("a")
                    url = await link_el.get_attribute("href") if link_el else ""
                    if url and not url.startswith("http"):
                        url = f"{self.BASE_URL}{url}"

                    # 提取商品ID
                    product_id = ""
                    if "/detail/" in url:
                        product_id = url.split("/detail/")[-1].split("-")[0]

                    title_el = await item.query_selector(".goods-title")
                    title = await title_el.inner_text() if title_el else ""

                    price_el = await item.query_selector(".goods-price")
                    price_text = await price_el.inner_text() if price_el else "0"
                    price = float(price_text.replace("¥", "").strip() or 0)

                    original_price_el = await item.query_selector(".goods-market-price")
                    original_price_text = await original_price_el.inner_text() if original_price_el else None
                    original_price = float(original_price_text.replace("¥", "").strip() or 0) if original_price_text else None

                    discount_el = await item.query_selector(".goods-discount")
                    discount = await discount_el.inner_text() if discount_el else ""

                    shop_el = await item.query_selector(".shop-name")
                    shop = await shop_el.inner_text() if shop_el else "唯品会自营"

                    img_el = await item.query_selector("img")
                    image = await img_el.get_attribute("src") if img_el else ""

                    product = Product(
                        id=product_id,
                        title=title.strip(),
                        price=price,
                        original_price=original_price,
                        shop=shop,
                        url=url,
                        image=image if image.startswith("http") else f"https:{image}",
                        discount=discount
                    )
                    products.append(product)
                    self._save_product(product)

                except Exception as e:
                    continue

        except Exception as e:
            print(f"搜索解析失败: {e}")

        return products

    def _save_product(self, product: Product):
        """保存商品到数据库"""
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO products
            (id, title, price, original_price, shop, url, image, discount, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (product.id, product.title, product.price, product.original_price,
              product.shop, product.url, product.image, product.discount))

        # 记录价格历史
        cursor.execute("""
            INSERT INTO price_history (product_id, price)
            VALUES (?, ?)
        """, (product.id, product.price))

        self.db.commit()

    async def get_sales(self) -> List[SaleEvent]:
        """获取特卖活动"""
        if not self.page:
            await self.init_browser()

        print("正在获取特卖活动...")
        await self.page.goto(self.SALE_URL, wait_until="networkidle")
        await asyncio.sleep(3)

        sales = []

        try:
            # 等待活动列表加载
            await self.page.wait_for_selector(".sale-item", timeout=10000)
            items = await self.page.query_selector_all(".sale-item")

            for item in items[:15]:
                try:
                    # 提取活动信息
                    link_el = await item.query_selector("a")
                    url = await link_el.get_attribute("href") if link_el else ""
                    if url and not url.startswith("http"):
                        url = f"{self.BASE_URL}{url}"

                    # 提取活动ID
                    sale_id = ""
                    if "/special/" in url:
                        sale_id = url.split("/special/")[-1].split("-")[0]

                    title_el = await item.query_selector(".sale-title")
                    title = await title_el.inner_text() if title_el else ""

                    desc_el = await item.query_selector(".sale-desc")
                    description = await desc_el.inner_text() if desc_el else ""

                    time_el = await item.query_selector(".sale-time")
                    time_text = await time_el.inner_text() if time_el else ""

                    img_el = await item.query_selector("img")
                    image = await img_el.get_attribute("src") if img_el else ""

                    sale = SaleEvent(
                        id=sale_id,
                        title=title.strip(),
                        description=description.strip(),
                        start_time=time_text,
                        end_time="",
                        url=url,
                        image=image if image.startswith("http") else f"https:{image}"
                    )
                    sales.append(sale)

                    # 保存到数据库
                    cursor = self.db.cursor()
                    cursor.execute("""
                        INSERT OR REPLACE INTO sales (id, title, description, start_time, end_time, url, image)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (sale.id, sale.title, sale.description, sale.start_time, sale.end_time, sale.url, sale.image))
                    self.db.commit()

                except Exception as e:
                    continue

        except Exception as e:
            print(f"获取特卖活动失败: {e}")

        return sales

    async def get_brands(self, category: str = "all") -> List[Brand]:
        """获取品牌专区"""
        if not self.page:
            await self.init_browser()

        print("正在获取品牌专区...")
        url = self.BRAND_URL
        if category != "all":
            url = f"{url}/{category}"

        await self.page.goto(url, wait_until="networkidle")
        await asyncio.sleep(3)

        brands = []

        try:
            # 等待品牌列表加载
            await self.page.wait_for_selector(".brand-item", timeout=10000)
            items = await self.page.query_selector_all(".brand-item")

            for item in items[:20]:
                try:
                    # 提取品牌信息
                    link_el = await item.query_selector("a")
                    url = await link_el.get_attribute("href") if link_el else ""
                    if url and not url.startswith("http"):
                        url = f"{self.BASE_URL}{url}"

                    # 提取品牌ID
                    brand_id = ""
                    if "/brand/" in url:
                        brand_id = url.split("/brand/")[-1].split("-")[0]

                    name_el = await item.query_selector(".brand-name")
                    name = await name_el.inner_text() if name_el else ""

                    img_el = await item.query_selector("img")
                    logo = await img_el.get_attribute("src") if img_el else ""

                    cat_el = await item.query_selector(".brand-category")
                    cat = await cat_el.inner_text() if cat_el else category

                    brand = Brand(
                        id=brand_id,
                        name=name.strip(),
                        logo=logo if logo.startswith("http") else f"https:{logo}",
                        url=url,
                        category=cat
                    )
                    brands.append(brand)

                    # 保存到数据库
                    cursor = self.db.cursor()
                    cursor.execute("""
                        INSERT OR REPLACE INTO brands (id, name, logo, url, category)
                        VALUES (?, ?, ?, ?, ?)
                    """, (brand.id, brand.name, brand.logo, brand.url, brand.category))
                    self.db.commit()

                except Exception as e:
                    continue

        except Exception as e:
            print(f"获取品牌专区失败: {e}")

        return brands

def format_product(p: Product, index: int) -> str:
    """格式化商品输出"""
    price_str = f"¥{p.price:.2f}"
    original_str = f" (原价: ¥{p.original_price:.2f})" if p.original_price else ""
    discount_str = f" [{p.discount}]" if p.discount else ""
    return f"""
[{index}]{discount_str} {p.title[:50]}{'...' if len(p.title) > 50 else ''}
    价格: {price_str}{original_str}
    店铺: {p.shop}
    链接: {p.url}
"""

def format_sale(s: SaleEvent, index: int) -> str:
    """格式化特卖活动输出"""
    return f"""
[{index}] {s.title}
    描述: {s.description}
    时间: {s.start_time}
    链接: {s.url}
"""

def format_brand(b: Brand, index: int) -> str:
    """格式化品牌输出"""
    return f"""
[{index}] {b.name}
    分类: {b.category}
    链接: {b.url}
"""

async def main():
    parser = argparse.ArgumentParser(description="唯品会购物助手")
    parser.add_argument("command", choices=["search", "sale", "brand", "login"])
    parser.add_argument("arg", nargs="?", help="搜索关键词/分类")
    parser.add_argument("--page", type=int, default=1, help="页码")
    parser.add_argument("--category", type=str, default="all", help="品牌分类")

    args = parser.parse_args()

    client = VipClient()

    try:
        if args.command == "login":
            await client.login()

        elif args.command == "search":
            if not args.arg:
                print("请提供搜索关键词")
                return
            products = await client.search(args.arg, args.page)
            print(f"\n找到 {len(products)} 个商品:\n")
            for i, p in enumerate(products, 1):
                print(format_product(p, i))

        elif args.command == "sale":
            sales = await client.get_sales()
            print(f"\n特卖活动 ({len(sales)} 个):\n")
            for i, s in enumerate(sales, 1):
                print(format_sale(s, i))

        elif args.command == "brand":
            category = args.arg or args.category
            brands = await client.get_brands(category)
            print(f"\n品牌专区 ({len(brands)} 个):\n")
            for i, b in enumerate(brands, 1):
                print(format_brand(b, i))

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
