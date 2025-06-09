# Bynder Taxonomy Sync

This script automates the creation and linking of Bynder metaproperty product heirachy options based on a CSV input.  
It ensures Level 1 → Level 2 → Level 3 dependencies are created and managed correctly via Bynder's API.

Before running `updatemetadata.py`, you can run `skucheck.py` to identify which SKUs are currently missing in Bynder, comparing Bynder to a Google product feed. This allows you to prepare the CSV file with the necessary product, shade, and SKU data to ensure everything is up to date before the taxonomy sync.


---

## 🛠 Prerequisites

- Python 3.8+
- A Bynder OAuth2 client with API access to manage metaproperties

---

## 📦 Installation

```bash
git clone https://github.com/kieran-ct/bynder-taxonomy-sync.git
cd bynder-taxonomy-sync
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## ⚙️ Configuration

Create a `.env` file in the project root with the following values:

```env
BYNDER_DOMAIN=your-bynder-domain.com
CLIENT_ID=your-client-id
CLIENT_SECRET=your-client-secret
CSV_PATH=sample.csv
DRY_RUN=false
```

The `DRY_RUN` flag allows you to simulate the process without making changes.

---

## 📄 Input Format

The script expects a CSV file (default `your:_file.csv`) with the following headers:

```
Product,Shade,Product + Shade,SKU
```

Example:

```csv
Product,Shade,Product + Shade,SKU
JASMIN PALETTE,,JASMIN PALETTE,CAI034
VANESSAS KIT,,VANESSAS KIT,CAI037
BERRY KISS,,BERRY KISS,CAI096
```

---

## 🚀 Running the Script

```bash
python updatemetadata.py
```

The script will:
- Read your CSV
- Create missing options for Product, Product + Shade, and SKU metaproperties
- Link options according to your dependency hierarchy:
  - Product → Product + Shade
  - Product → SKU
  - Product + Shade → SKU

---

## 🧼 Notes

- Existing options are not duplicated.
- Existing dependencies are detected and skipped with a log.
- The script will retry fetching metaproperty options after creation to ensure fresh linking.

---

## 📁 Repository Structure

```
bynder-taxonomy-sync/
├── updatemetadata.py
├── sample.csv
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

---





