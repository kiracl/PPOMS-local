# PPOMS System Design Document (V2.6)

## 1. Project Overview
**Project Name**: PPOMS (Procurement Production Operation Management System)
**Version**: V2.6
**Tech Stack**: Python 3.10+, PySide6 (Qt), SQLite 3
**Description**: A desktop application for managing the entire procurement lifecycle, from planning and ordering to inbound delivery, invoicing, and settlement.

## 2. System Architecture
*   **Frontend**: PySide6 (QWidget-based). Uses `QStackedWidget` for main navigation.
*   **Backend**: Local SQLite database (`purchase.db`).
*   **Deployment**: PyInstaller single-file executable.

## 3. Core Modules

### 3.1. Plan Management
*   **Monthly Plan**: Manages high-level monthly procurement plans (`monthly_plans`).
*   **Purchase Plan**:
    *   Manages specific purchase orders (`orders`) and details (`order_details`).
    *   Generates unique order numbers (e.g., `2601MPB-1`).
    *   Supports generating PDF approval documents.
*   **Plan Release**: Assigns purchase tasks to purchasers (`release_orders`).

### 3.2. Price Audit & Analysis
*   **Price Audit Module**:
    *   **Plan Export**: Exports monthly plans to Excel/Print with formatting.
    *   **Other Quote Audit**: Manages ad-hoc quote audits (`quote_audit_records`, `quote_audit_details`). Supports Excel import/export and smart price filling.
*   **Price Recommendation**:
    *   Analyzes historical prices (`historical_quotes`) and standard items (`standard_items`).
    *   Provides price recommendations based on fuzzy matching of Item Name and Spec Model.
    *   Supports "Reverse Learning" from audit records.

### 3.3. Inbound Management
*   **Inbound Registration**:
    *   Records warehouse entries (`inbound_orders`).
    *   Supports batch entry (one inbound number for multiple items).
    *   Links to `order_details` via `detail_no` (logic-based).

### 3.4. Invoice Management
*   **Invoice Registration**:
    *   Records invoices (`invoices`) and line items (`invoice_items`).
    *   Associates invoice items with inbound records.

### 3.5. Settlement Management
*   **Reconciliation (Statement)**:
    *   Groups invoice items into a reconciliation statement (`reconciliations`).
    *   Tracks status: `待对账` -> `对账中` -> `完成对账`.
*   **Settlement**:
    *   Processes payments for completed reconciliations (`settlements`).
    *   Tracks status: `已结算`.

### 3.6. Contract Management
*   **Contract Ledger**: Manages contracts (`contracts`) and their specifications (`contract_specs`).

### 3.7. System Management
*   **Workbench**: Dashboard with key statistics and quick access.
*   **Data Manager**: Database backup and restore.
*   **Settings**: Configuration of dropdowns (Units, Purchasers, etc.).

### 3.8. AI Assistant (New)
*   **Overview**: Provides intelligent analysis and data interaction capabilities via LLM integration.
*   **Features**:
    *   **Smart Chat**: Context-aware conversation with support for data feeding (Plans, Contracts, Quotes).
    *   **Configuration**: Supports OpenAI, DeepSeek, and local Ollama models.
*   **Future Roadmap**:
    *   **Text-to-SQL (Phase 1)**: Enable natural language database queries (e.g., "Show me total contract amount for last month").
    *   **RAG Knowledge Base (Phase 2)**: Document-based QA for internal policies (Implemented V2.7).
    *   **Generative Actions (Phase 3)**: Automated document generation (Contracts, Invoices).
    *   **Data Visualization (Phase 4)**: On-the-fly chart generation.

### 4.7. Knowledge Base (New)
*   `knowledge_docs`: Metadata for uploaded files (PDF, Word, TXT).
*   `knowledge_chunks`: Text chunks split from documents.
*   `knowledge_fts`: Virtual table for full-text search (FTS5).

## 4. Database Schema (Key Tables)

### 4.1. Core Procurement
*   `orders`: Main purchase orders.
    *   `number` (PK), `yymm`, `category`, `unit`, `date`, `task_name`.
*   `order_details`: Line items.
    *   `id` (PK), `order_number` (FK), `detail_no`, `item_name`, `spec_model`, `purchase_qty`, `unit_price`, `audit_price`, etc.

### 4.2. Inbound & Invoice
*   `inbound_orders`: Warehouse receipts.
    *   `id` (PK), `inbound_no`, `warehouse_no`, `inbound_date`, `supplier`, `items_json` (or individual rows depending on migration).
    *   *Note*: Recent migration removed `UNIQUE` constraint on `inbound_no` to allow multiple rows per inbound slip.
*   `invoices`: Invoice headers.
    *   `id` (PK), `invoice_no`, `supplier`, `invoice_date`, `total_amount`, `tax_rate`.
*   `invoice_items`: Invoice line items.
    *   `id` (PK), `invoice_id` (FK), `inbound_id` (FK), `amount`.

### 4.3. Settlement
*   `reconciliations`: Reconciliation statements.
    *   `id` (PK), `reconciliation_no`, `supplier`, `status`, `total_amount`.
*   `reconciliation_details`: Link table.
    *   `id` (PK), `reconciliation_id` (FK), `invoice_item_id` (FK), `amount_incl_tax`.
*   `settlements`: Payment records.
    *   `id` (PK), `reconciliation_id` (FK), `settlement_date`, `amount`, `method`.

### 4.4. Price Audit (New)
*   `quote_audit_records`: Audit headers.
    *   `id` (PK), `name`, `created_at`, `status`, `remark`.
*   `quote_audit_details`: Audit line items.
    *   `id` (PK), `record_id` (FK), `item_name`, `spec_model`, `inquiry_price`, `audit_price`.

### 4.5. Price Analysis
*   `historical_quotes`: Raw historical data.
*   `standard_items`: Cleaned standard price library.
*   `item_mappings`: Mapping between raw inputs and standard items.

### 4.6. AI Configuration
*   `ai_config`: Stores LLM provider settings (API Key, Base URL, Model Name).

## 5. Recent Changes (V2.6)
1.  **Price Audit Module Refactoring**:
    *   Moved "Plan Export" to a tab within "Price Audit".
    *   Added "Other Quote Audit" for non-plan price reviews.
    *   Implemented Excel import/export and smart price filling for audit records.
2.  **Inbound Logic Update**:
    *   Removed unique constraint on `inbound_no` to support multi-row inbound slips.
3.  **UI/UX**:
    *   Standardized table column width persistence.
    *   Improved navigation with `QStackedWidget` in Price Audit.
4.  **AI Assistant Module**:
    *   Added "AI Assistant" module with "Smart Chat" and "Configuration" tabs.
    *   Implemented data feeding for Monthly Plans, Historical Prices, Contracts, Inbound, Invoice, and Settlement data.

## 6. Known Issues / To-Do
*   **Foreign Keys**: SQLite FK constraints are not strictly enforced (connection does not set `PRAGMA foreign_keys = ON`). Deletions are handled manually in code.
*   **Hardcoded Configuration**: Some initial seed data (e.g., plan months) is hardcoded in `database.py`.
