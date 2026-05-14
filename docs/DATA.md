# **Datasets**

Every dataset used by the project must be listed here with source, version,  
license, and download command. Datasets must NOT be committed to the repo.

## **Dataset 1: Static Menu Index**

* **Source URL:** N/A (Hardcoded in codebase to prevent hallucination)  
* **Version:** v1.0  
* **sha256:** N/A  
* **License:** Proprietary (Mock Data)  
* **Size:** \< 10 KB  
* **Cite as:** Neon Trompo Mock Menu

### **Download**

make download-data

Because the architecture demands absolute determinism for Semantic Checkout and pricing calculation, the system explicitly avoids using massive unstructured Vector DBs or RAG for inventory. The menu is a strict Python Dictionary (src/myproject/menu.py), and therefore no external data download is required. The make download-data command acts as a successful no-op.

### **Preprocessing**

No preprocessing is required.