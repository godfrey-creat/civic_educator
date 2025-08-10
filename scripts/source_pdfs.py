import os
import requests
from pathlib import Path
from urllib.parse import urlparse

document_links = [
    "https://nairobi.go.ke/wp-content/uploads/NCCG_Service_Charter_2025.pdf",
    "https://nairobi.go.ke/wp-content/uploads/Nairobi-City-County-Solid-Waste-Management-Act-2015-2.pdf",
    "https://nairobiassembly.go.ke/ncca/wp-content/uploads/committee_documents/Report-On-Solid-Waste-Management-Bill.pdf",
    "https://nairobiassembly.go.ke/ncca/wp-content/uploads/weeklyschedule/2024/22-Weekly-Schedule-week-commencing-Wednesday-30th-October-2024-1.pdf",
    "https://ad.nema.go.ke/wp-content/uploads/2024/10/Environmental-Best-Practices-in-Waste-Management.pdf",
    "https://nairobiassembly.go.ke/ncca/wp-content/uploads/paperlaid/2023/NAIROBI-CITY-COUNTY-INTEGRATED-DEVELOPMENT-PLAN-FOR-2023-2027-1.pdf",
    "https://parliament.go.ke/sites/default/files/2022-05/GARBAGE%20COLLECTION%20SERVICES%201.pdf"
]

download_dir = Path("knowledge_base/sourced_pdfs")
download_dir.mkdir(parents=True, exist_ok=True)

for url in document_links:
    try:
        filename = Path(urlparse(url).path).name
        file_path = download_dir / filename

        response = requests.get(url)
        response.raise_for_status()

        with open(file_path, "wb") as f:
            f.write(response.content)

        print(f"Downloaded: {filename}")
    except Exception as e:
        print(f"Failed to download {url} — {e}")
