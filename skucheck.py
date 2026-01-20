import requests
import xml.etree.ElementTree as ET
import time
import csv
import os
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
BYNDER_DOMAIN = os.getenv("BYNDER_DOMAIN")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SKU_METAPROPERTY_ID = os.getenv("SKU_METAPROPERTY_ID")

# --- Step 1: Get OAuth token ---
auth_response = requests.post(
    f"https://{BYNDER_DOMAIN}/v6/authentication/oauth2/token",
    data={"grant_type": "client_credentials"},
    auth=(CLIENT_ID, CLIENT_SECRET)
)
access_token = auth_response.json()['access_token']
headers = {"Authorization": f"Bearer {access_token}"}

# --- FETCH EXISTING SKU OPTIONS FROM BYNDER ---
bynder_skus = set()
page = 1
while True:
    print(f"🔄 Fetching page {page} of SKU options from Bynder...")

    response = requests.get(
        f"https://{BYNDER_DOMAIN}/api/v4/metaproperties/{SKU_METAPROPERTY_ID}/options/",
        headers=headers,
        params={"page": page}
    )

    if response.status_code != 200:
        print(f"❌ Failed to fetch page {page}: {response.status_code}")
        print(response.text)
        break

    options = response.json()

    if not options:
        print(f"✅ No more options after page {page - 1}.")
        break

    print(f"📦 Page {page} returned {len(options)} options")

    for opt in options:
        if isinstance(opt, dict):
            label = opt.get("displayLabel") or opt.get("label")
            if label:
                bynder_skus.add(label.strip())
        else:
            print("⚠️ Unexpected format:", opt)

    page += 1

print(f"\n✅ Total SKU options collected from Bynder: {len(bynder_skus)}")
# Show an example SKU from Bynder
if bynder_skus:
    print(f"🟣 Example SKU from Bynder: {next(iter(bynder_skus))}")
else:
    print("⚠️ No SKUs retrieved from Bynder.")

# --- PARSE CHANNABLE FEED ---
feed_url = "https://caiacosmetics.com/agent/Google_SE_products_sa6Jg8T_all.xml?hej=hej"
print("🌐 Downloading Channable feed...")
response = requests.get(feed_url)

print("🧪 Parsing XML...")
root = ET.fromstring(response.content)

# Register namespaces to handle g:id and similar
namespaces = {'g': 'http://base.google.com/ns/1.0'}

# Register namespaces to handle g:id and similar
namespaces = {'g': 'http://base.google.com/ns/1.0'}

feed_skus = set()
sku_to_title = {}
item_count = 0

for i, item in enumerate(root.findall('.//item')):
    sku_elem = item.find('g:id', namespaces)
    title_elem = item.find('title')
    
    if sku_elem is not None:
        sku = sku_elem.text.strip()
        feed_skus.add(sku)

        title = title_elem.text.strip() if title_elem is not None and title_elem.text is not None else ""
        sku_to_title[sku] = title

    item_count += 1
    if i > 0 and i % 100 == 0:
        print(f"🔄 Processed {i} items...")

print(f"✅ Parsed {item_count} items from Channable feed")
print(f"✅ Retrieved {len(feed_skus)} unique SKUs from feed")
# Show an example SKU from Channable
if feed_skus:
    print(f"🟡 Example SKU from Channable feed: {next(iter(feed_skus))}")
else:
    print("⚠️ No SKUs retrieved from Channable feed.")

missing_skus = sorted(feed_skus - bynder_skus)

print(f"\n❌ Missing SKUs in Bynder ({len(missing_skus)}):")
for sku in missing_skus:
    print(sku)

# --- EXPORT MISSING SKUs TO CSV ---
output_file = "missing_skus.csv"
with open(output_file, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["SKU", "Title"])  # Header row

    for sku in missing_skus:
        title = sku_to_title.get(sku, "")
        writer.writerow([sku, title])

print(f"📄 CSV file created: {output_file} with {len(missing_skus)} missing SKUs")