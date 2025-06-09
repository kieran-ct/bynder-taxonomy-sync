import csv
import requests
import time
import json
import re
from dotenv import load_dotenv
load_dotenv()


# --- CONFIGURATION ---
# --- Configuration ---
BYNDER_DOMAIN = os.getenv("BYNDER_DOMAIN")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")


PRODUCT_ID = "752A1FE6-4EE4-41E0-9CB0D32648A20847"
PRODUCT_SHADE_ID = "E8F2E838-E798-4B5C-889CEC3ED0440C1F"
SKU_ID = "C15CCF07-305D-4441-BC71D5A51B4BF48F"

CSV_PATH = "your_file.csv"
DRY_RUN = False

# === AUTH ===
auth_response = requests.post(
    f"https://{BYNDER_DOMAIN}/v6/authentication/oauth2/token",
    data={"grant_type": "client_credentials"},
    auth=(CLIENT_ID, CLIENT_SECRET)
)
auth_response.raise_for_status()
access_token = auth_response.json()['access_token']
HEADERS = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

# === HELPERS ===
def fetch_options(meta_id):
    options = {}
    page = 1
    while True:
        r = requests.get(
            f"https://{BYNDER_DOMAIN}/api/v4/metaproperties/{meta_id}/options/",
            headers=HEADERS,
            params={"page": page}
        )
        data = r.json()
        if not data:
            break
        for opt in data:
            label = opt.get("displayLabel") or opt.get("label")
            if label:
                options[label.strip()] = opt["id"]
        page += 1
    return options

def create_option(meta_id, label, headers):
    safe_name = re.sub(r'[^A-Za-z0-9]', '_', label.strip()).upper()

    payload = {
        "name": safe_name,
        "label": label.strip(),
        "labels": {
            "en_US": label.strip()
        },
        "isSelectable": True
    }

    print(f"📤 Creating option for meta {meta_id} (name: {safe_name})")
    print("📦 Payload:", json.dumps(payload, indent=2))

    if DRY_RUN:
        print(f"🛠️ [DRY RUN] Would create '{label}' in {meta_id}")
        return f"dry-{label}"

    r = requests.post(
        f"https://{BYNDER_DOMAIN}/api/v4/metaproperties/{meta_id}/options/",
        headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
        data={"data": json.dumps(payload)}
    )

    if r.status_code != 201:
        print("❌ Failed to create option:")
        print("   ▶ Label:", label)
        print("   ▶ Meta ID:", meta_id)
        print("   ▶ Status Code:", r.status_code)
        print("   ▶ Response:", r.text)
        r.raise_for_status()

    option_id = r.json()["id"]
    print(f"✅ Created '{label}' → {option_id}")
    return option_id

def link_options(child_meta_id, child_opt_id, parent_meta_id, parent_opt_ids):
    print(f"🔗 Linking {len(parent_opt_ids)} parents to child option {child_opt_id}")
    print(f"    ▶ Child Meta ID: {child_meta_id}")
    print(f"    ▶ Child Option ID: {child_opt_id}")
    print(f"    ▶ Parent Meta ID: {parent_meta_id}")
    print(f"    ▶ Parent Option IDs: {parent_opt_ids}")

    if not DRY_RUN:
        for parent_id in parent_opt_ids:
            url = f"https://{BYNDER_DOMAIN}/api/v4/metaproperties/{child_meta_id}/options/{child_opt_id}/dependencies/{parent_id}/"
            r = requests.post(url, headers=HEADERS)
            if r.status_code == 400 and "The automation already exists" in r.text:
                print(f"ℹ️ Dependency already exists: {parent_id}")
                continue
            if r.status_code != 201:
                print("❌ Link failed:", r.text)
            r.raise_for_status()

# === LOAD CSV ===
rows = []
with open(CSV_PATH, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append({
            "product": row["Product"].strip(),
            "shade": row["Shade"].strip(),
            "product_shade": row["Product + Shade"].strip(),
            "sku": row["SKU"].strip(),
        })

# === FETCH EXISTING OPTIONS ===
print("📡 Fetching current metaproperty options from Bynder...")
products = fetch_options(PRODUCT_ID)
shades = fetch_options(PRODUCT_SHADE_ID)
skus = fetch_options(SKU_ID)

# === CREATE MISSING OPTIONS ===
# Pre-pass to avoid linking before everything is created
for row in rows:
    if row["sku"] and row["sku"] not in skus:
        print(f"📦 Creating missing SKU: {row['sku']}")
        skus[row["sku"]] = create_option(SKU_ID, row["sku"], HEADERS)
        time.sleep(0.2)

    if row["product_shade"] and row["product_shade"] not in shades:
        print(f"🎨 Creating missing product+shade: {row['product_shade']}")
        shades[row["product_shade"]] = create_option(PRODUCT_SHADE_ID, row["product_shade"], HEADERS)
        time.sleep(0.2)

    if row["product"] and row["product"] not in products:
        print(f"🧱 Creating missing product: {row['product']}")
        products[row["product"]] = create_option(PRODUCT_ID, row["product"], HEADERS)
        time.sleep(0.2)

# === LINKING ===
print("🔁 Preparing links...")
product_to_shade = {}
product_to_sku = {}
shade_to_sku = {}

for row in rows:
    p = row["product"]
    ps = row["product_shade"]
    sku = row["sku"]

    if p and ps and ps in shades and p in products:
        product_to_shade.setdefault(ps, set()).add(products[p])
    if p and sku and sku in skus and p in products:
        product_to_sku.setdefault(sku, set()).add(products[p])
    if ps and sku and sku in skus and ps in shades:
        shade_to_sku.setdefault(sku, set()).add(shades[ps])

for ps, product_ids in product_to_shade.items():
    if ps in shades:
        link_options(PRODUCT_SHADE_ID, shades[ps], PRODUCT_ID, list(product_ids))
        time.sleep(0.3)

for sku, product_ids in product_to_sku.items():
    if sku in skus:
        link_options(SKU_ID, skus[sku], PRODUCT_ID, list(product_ids))
        time.sleep(0.3)

for sku, shade_ids in shade_to_sku.items():
    if sku in skus:
        link_options(SKU_ID, skus[sku], PRODUCT_SHADE_ID, list(shade_ids))
        time.sleep(0.3)

print("✅ Done.")
