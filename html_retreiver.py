import time
import re
from datetime import datetime
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ===================== CONFIG =====================
OUTPUT_CSV = "snapdeal_products.csv"
HEADLESS = False
MAX_PRODUCTS_PER_SECTION = 10
PAGE_LOAD_TIMEOUT = 60
# ==================================================

BASE_SECTIONS = {
    "Accessories": "https://www.snapdeal.com/search?keyword=accessories&sort=rlvncy",
    "Footwear": "https://www.snapdeal.com/search?keyword=footwear&sort=rlvncy",
    "Kids Fashion": "https://www.snapdeal.com/search?keyword=kids%20fashion&sort=rlvncy",
    "Men Clothing": "https://www.snapdeal.com/search?keyword=men%20clothing&sort=rlvncy",
    "Women Clothing": "https://www.snapdeal.com/search?keyword=women%20clothing&sort=rlvncy",
}

# ---------- Selenium Setup ----------
chrome_opts = Options()
if HEADLESS:
    chrome_opts.add_argument("--headless=new")

chrome_opts.add_argument("--disable-gpu")
chrome_opts.add_argument("--window-size=1920,1080")
chrome_opts.add_argument("--no-sandbox")
chrome_opts.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=chrome_opts)
driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)

wait = WebDriverWait(driver, 20)

# ---------- Helper Functions ----------
def parse_rating_from_style(style):
    if not style:
        return ""
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", style)
    if not m:
        return ""
    pct = float(m.group(1))
    return round(pct / 20, 1)

def safe_get(url):
    try:
        driver.get(url)
        return True
    except TimeoutException:
        print("⚠ Page load timeout, skipping...")
        return False

# ===================== MAIN =====================
all_rows = []

for section, url in BASE_SECTIONS.items():
    print(f"\n=== Scraping {section} ===")

    if not safe_get(url):
        continue

    try:
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-tuple-listing"))
        )
    except TimeoutException:
        print("⚠ Products not loaded, skipping section")
        continue

    time.sleep(3)

    cards = driver.find_elements(By.CSS_SELECTOR, "div.product-tuple-listing")

    for card in cards[:MAX_PRODUCTS_PER_SECTION]:
        try:
            name = card.find_element(By.CSS_SELECTOR, "p.product-title").text.strip()
        except:
            name = ""

        try:
            price = card.find_element(By.CSS_SELECTOR, "span.product-price").text.strip()
        except:
            price = ""

        try:
            rating_style = card.find_element(By.CSS_SELECTOR, ".filled-stars").get_attribute("style")
            rating = parse_rating_from_style(rating_style)
        except:
            rating = ""

        try:
            img = card.find_element(By.TAG_NAME, "img").get_attribute("src")
        except:
            img = ""

        try:
            product_url = card.find_element(By.TAG_NAME, "a").get_attribute("href")
        except:
            product_url = ""

        all_rows.append({
            "Scraped At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Section": section,
            "Product Name": name,
            "Price": price,
            "Rating": rating,
            "Image URL": img,
            "Product URL": product_url,
        })

# ---------- Save CSV ----------
df = pd.DataFrame(all_rows)
df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

print(f"\n✅ DONE! File saved as: {OUTPUT_CSV}")

driver.quit()
