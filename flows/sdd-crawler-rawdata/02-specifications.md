# Specifications: Tax Lien Parser Raw Data Storage

> Version: 1.0
> Status: DRAFT
> Last Updated: 2026-02-23
> Requirements: [01-requirements.md](01-requirements.md)

## Overview

Стандартизация хранения raw данных (HTML, JSON, PDF, images) для всех платформ парсинга налоговых залогов. Спецификация определяет единую структуру директорий, форматы именования файлов, и правила организации данных across все существующие и новые платформы.

**Ключевые принципы:**
- Raw HTML хранится отдельно от parsed JSON
- Данные организуются по иерархии: platform → state → county → parcel_id
- Каждый parcel имеет свою директорию со всеми связанными файлами
- PDF и images хранятся per-parcel (без глобальной дедупликации)
- Старые HTML файлы сжимаются после N дней

---

## Affected Systems

| System | Impact | Notes |
|--------|--------|-------|
| `storage/db.py` | Modify | LocalPersistenceManager — изменить пути сохранения |
| `client/gateway.py` | Modify | ParcelResult — добавить raw_html_path поле |
| `orchestrator/storage/` | Migrate | Перейти на новую структуру |
| `storage/scraped/` | Migrate | Перейти на новую структуру |
| `storage/data/` | Migrate | Перейти на новую структуру |
| `parsers/base_parser.py` | Modify | BaseParser — сохранить raw HTML перед парсингом |
| `docker-compose.yml` | Modify | Обновить volume mounts |

---

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    SCRAPER / PARSER                         │
│                                                             │
│  1. Download HTML ──→ Save Raw ──→ Parse ──→ Save JSON     │
│         │                │                      │           │
│         │                │                      │           │
│         ▼                ▼                      ▼           │
│    (memory)      raw/html/{path}        parsed/{path}      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    STORAGE LAYER                            │
│                                                             │
│  {root}/                                                    │
│  ├── raw/                                                   │
│  │   ├── html/       # Сжатые и несжатые HTML              │
│  │   └── debug/      # Временные failed scrape файлы       │
│  ├── parsed/                                                │
│  │   ├── parcels/    # JSON + metadata + PDF + images      │
│  │   └── parties/    # Party data (future)                 │
│  ├── queue/                                                 │
│  │   └── worker_state.db                                   │
│  └── archive/                                               │
│      └── compressed/ # Старые сжатые данные                │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
URL → Download → Raw HTML (save) → Parse → Structured Data (save)
                      │                        │
                      │                        ├─→ parcel.json
                      │                        ├─→ metadata.json
                      │                        ├─→ documents/*.pdf
                      │                        └─→ images/*.jpg
                      │
                      └─→ hash computed → dedup check
```

---

## Directory Structure Specification

### Root Path Template

```
{root}/{tier}/{platform}/{state}/{county}/{parcel_id}/
```

**Где:**
- `{root}` — Базовая директория (настраивается через env: `RAW_STORAGE_ROOT`)
- `{tier}` — Tier платформы (1, 2, 3) для организации
- `{platform}` — Название платформы (custom_gis, beacon, qpublic, etc.)
- `{state}` — Код штата (FL, AZ, IL, etc.)
- `{county}` — Название округа (Clay, Maricopa, Cook, etc.)
- `{parcel_id}` — ID парсела (URL-safe, sanitized)

### Raw HTML Storage

**Путь:**
```
{root}/raw/html/{tier}/{platform}/{state}/{county}/{parcel_id}/{timestamp}.html[.gz]
```

**Формат именования:**
- Активные HTML: `{parcel_id}_{YYYYMMDD_HHMMSS}.html`
- Сжатые HTML: `{parcel_id}_{YYYYMMDD_HHMMSS}.html.gz` (после 30 дней)
- Latest symlink: `latest.html` → текущий файл

**Пример:**
```
/raw/html/tier1/custom_gis/FL/Clay/123-45-67/
├── 123-45-67_20260223_143022.html
├── 123-45-67_20260215_091504.html
├── 123-45-67_20260201_182344.html.gz  # compressed
└── latest.html → 123-45-67_20260223_143022.html
```

**Хеш:**
- SHA256 хеш вычисляется при сохранении
- Сохраняется в metadata.json

### Parsed JSON Storage

**Путь:**
```
{root}/parsed/parcels/{tier}/{platform}/{state}/{county}/{parcel_id}/
```

**Файлы в директории parcel:**
```
{parcel_id}/
├── parcel.json           # Основные данные (ParcelData schema)
├── metadata.json         # Метаданные парсинга
├── documents/            # PDF файлы
│   ├── tax_bill_{doc_id}.pdf
│   ├── deed_{doc_id}.pdf
│   └── notice_{doc_id}.pdf
└── images/               # Изображения
    ├── property_001.jpg
    ├── property_002.png
    └── aerial_001.jpg
```

### parcel.json Structure

```json
{
  "parcel_id": "123-45-67",
  "county": "Clay",
  "state": "FL",
  "platform": "custom_gis",
  "has_assessor_data": true,
  "has_tax_data": true,
  "has_gis_data": false,
  "has_recorder_data": false,
  "owner_name": "John Doe",
  "property_address": "123 Main St",
  "assessed_value": 150000.00,
  "tax_amount": 2500.00,
  "tax_year": 2025
}
```

### metadata.json Structure

```json
{
  "scrape_id": "uuid-v4",
  "parcel_id": "123-45-67",
  "platform": "custom_gis",
  "state": "FL",
  "county": "Clay",
  "scraped_at": "2026-02-23T14:30:22Z",
  "parsed_at": "2026-02-23T14:30:23Z",
  "parse_duration_ms": 145,
  "parser_version": "1.2.0",
  
  "raw_html": {
    "path": "../../raw/html/tier1/custom_gis/FL/Clay/123-45-67/123-45-67_20260223_143022.html",
    "sha256": "abc123...",
    "size_bytes": 45678,
    "compressed": false
  },
  
  "documents": [
    {
      "type": "tax_bill",
      "filename": "tax_bill_doc123.pdf",
      "path": "documents/tax_bill_doc123.pdf",
      "url": "https://...",
      "sha256": "...",
      "size_bytes": 123456,
      "downloaded_at": "2026-02-23T14:30:24Z"
    }
  ],
  
  "images": [
    {
      "type": "property",
      "filename": "property_001.jpg",
      "path": "images/property_001.jpg",
      "url": "https://...",
      "sha256": "...",
      "size_bytes": 89012,
      "dimensions": {"width": 800, "height": 600},
      "downloaded_at": "2026-02-23T14:30:25Z"
    }
  ],
  
  "sync_status": "pending",
  "synced_at": null
}
```

### Failed Scrape Storage (Debug)

**Путь:**
```
{root}/raw/debug/{platform}/{state}/{county}/{timestamp}_{parcel_id}.html
```

**Политика:**
- Сохраняется только последняя неудачная попытка
- Удаляется при успешном парсинге
- Не сжимается
- Максимум 1 файл на parcel в момент времени

---

## Compression Policy

### HTML Compression Schedule

| Age | Action |
|-----|--------|
| 0-7 days | Keep uncompressed |
| 7-30 days | Keep uncompressed |
| 30+ days | Compress to .gz |
| 365+ days | Move to archive (optional) |

### Compression Job

```python
# Запускается ежедневно через cron/worker
def compress_old_html(root_dir: str, days_threshold: int = 30):
    cutoff = datetime.now() - timedelta(days=days_threshold)
    for html_file in find_html_files(root_dir):
        if file_mtime(html_file) < cutoff and not html_file.endswith('.gz'):
            compress_gzip(html_file)  # Creates .html.gz
            os.remove(html_file)      # Remove original
```

---

## Database Schema Changes

### results Table (existing)

**Current:**
```sql
CREATE TABLE results (
    id INTEGER PRIMARY KEY,
    task_id TEXT,
    parcel_id TEXT,
    platform TEXT,
    state TEXT,
    county TEXT,
    json_path TEXT,
    html_path TEXT,
    scraped_at TIMESTAMP,
    sync_status TEXT DEFAULT 'pending'
);
```

**Updated:**
```sql
CREATE TABLE results (
    id INTEGER PRIMARY KEY,
    task_id TEXT,
    parcel_id TEXT,
    platform TEXT,
    state TEXT,
    county TEXT,
    tier INTEGER DEFAULT 1,
    
    -- File paths (relative to RAW_STORAGE_ROOT)
    parcel_dir TEXT,           -- parsed/parcels/tier1/.../{parcel_id}
    json_path TEXT,            -- parcel.json внутри parcel_dir
    html_path TEXT,            -- raw/html/.../{timestamp}.html
    html_latest_path TEXT,     -- symlink на latest
    
    -- Metadata
    raw_html_sha256 TEXT,
    raw_html_size INTEGER,
    parse_duration_ms INTEGER,
    parser_version TEXT,
    
    scraped_at TIMESTAMP,
    parsed_at TIMESTAMP,
    sync_status TEXT DEFAULT 'pending',
    synced_at TIMESTAMP
);
```

---

## Interfaces

### Modified: ParcelResult (client/gateway.py)

**Current:**
```python
@dataclass
class ParcelResult:
    task_id: str
    parcel_id: str
    platform: str
    state: str
    county: str
    data: Dict[str, Any]
    scraped_at: datetime
    parse_duration_ms: int
    raw_html_hash: Optional[str] = None
```

**Updated:**
```python
@dataclass
class ParcelResult:
    task_id: str
    parcel_id: str
    platform: str
    state: str
    county: str
    tier: int  # NEW: platform tier
    
    data: Dict[str, Any]
    scraped_at: datetime
    parsed_at: datetime  # NEW
    parse_duration_ms: int
    
    # File paths (relative to RAW_STORAGE_ROOT)
    parcel_dir: str        # NEW: parsed/parcels/.../{parcel_id}
    json_path: str         # NEW: relative path to parcel.json
    html_path: str         # NEW: relative path to raw HTML
    raw_html_hash: Optional[str] = None
    raw_html_size: Optional[int] = None  # NEW
    
    # Embedded documents/images
    documents: List[Dict[str, Any]] = field(default_factory=list)  # NEW
    images: List[Dict[str, Any]] = field(default_factory=list)     # NEW
```

### New: RawStorageManager Class

```python
class RawStorageManager:
    """Unified raw data storage handler."""
    
    def __init__(self, root: str, compression_days: int = 30):
        self.root = root
        self.compression_days = compression_days
    
    def get_parcel_dir(self, tier: int, platform: str, state: str, 
                       county: str, parcel_id: str) -> str:
        """Returns parsed/parcels/tier{N}/{platform}/{state}/{county}/{parcel_id}"""
    
    def save_raw_html(self, html: bytes, tier: int, platform: str, 
                      state: str, county: str, parcel_id: str) -> Tuple[str, str]:
        """Saves raw HTML, returns (relative_path, sha256)"""
    
    def save_parcel_json(self, data: Dict, parcel_dir: str) -> str:
        """Saves parcel.json, returns relative path"""
    
    def save_metadata(self, metadata: Dict, parcel_dir: str) -> str:
        """Saves metadata.json"""
    
    def save_document(self, pdf_bytes: bytes, parcel_dir: str, 
                      doc_type: str, doc_id: str) -> str:
        """Saves PDF to documents/ subdirectory"""
    
    def save_image(self, image_bytes: bytes, parcel_dir: str,
                   image_type: str, seq: int) -> str:
        """Saves image to images/ subdirectory"""
    
    def create_latest_symlink(self, parcel_dir: str, html_filename: str):
        """Creates/updates latest.html symlink"""
    
    def compress_old_html(self, dry_run: bool = False) -> Dict[str, int]:
        """Compresses HTML files older than compression_days"""
```

---

## Behavior Specifications

### Happy Path: Save Scraped Data

1. Scraper downloads HTML
2. **Before parsing:** Save raw HTML to `raw/html/{path}/{timestamp}.html`
3. Compute SHA256 hash of raw HTML
4. Parser extracts structured data from HTML
5. Save `parcel.json` to `parsed/parcels/{path}/`
6. Save `metadata.json` with links to raw HTML
7. Download PDFs/images if present
8. Create `latest.html` symlink
9. Update database with file paths

### Edge Cases

| Case | Trigger | Expected Behavior |
|------|---------|-------------------|
| Duplicate parcel | Same parcel_id scraped again | Save new HTML with new timestamp, keep old HTML, update latest symlink |
| Failed parse | Parser throws exception | Save HTML to `raw/debug/`, don't create parsed/ entry |
| Missing parcel_id | Can't extract from HTML | Use `{timestamp}_{hash}` as directory name, flag in metadata |
| Large PDF (>50MB) | Download streaming required | Stream directly to disk, don't load in memory |
| Image URL broken | 404 on download | Log warning, skip image, continue with rest |
| Disk full | No space | Raise exception, don't partial-save |

### Error Handling

| Error | Cause | Response |
|-------|-------|----------|
| Permission denied | File system readonly | Log error, mark task as failed, retry later |
| Invalid characters in parcel_id | Special chars in ID | Sanitize: replace `/\<>:"|?*` with `_` |
| Path too long | Deep nesting + long names | Use hash-based subdirectory if path > 255 chars |
| Concurrent write | Two workers same parcel | File locking via SQLite, serialize writes |

---

## Migration Plan

### Phase 1: Backward Compatibility

**Goal:** Новая структура работает параллельно со старой

```
RAW_STORAGE_ROOT = "storage/raw_v2"  # Новая структура
LEGACY_STORAGE = "storage"           # Старая структура
```

- Новые данные пишутся в новую структуру
- Чтение из обеих структур (проверка legacy first)
- Постепенная миграция через background job

### Phase 2: Data Migration

**Script:** `scripts/migrate_storage_v2.py`

```python
# Миграция orchestrator/storage/custom_gis/pending/
# → storage/raw_v2/raw/html/tier1/custom_gis/...

# Миграция storage/data/floridatax/FL/Clay/*.json
# → storage/raw_v2/parsed/parcels/tier1/floridatax/FL/Clay/...

# Миграция storage/scraped/beacon/FL/Clay/
# → storage/raw_v2/raw/html/tier2/beacon/FL/Clay/...
```

### Phase 3: Cutover

- Переключить все парсеры на новую структуру
- Old directories archived or deleted
- Update docker-compose.yml volume mounts

---

## Dependencies

### Requires

- Python 3.x с поддержкой gzip
- Docker volumes для persistence
- SQLite для queue management

### Blocks

- None (обратно совместимая миграция)

---

## Integration Points

### External Systems

- **CI/CD:** Docker volume mounts должны указывать на `RAW_STORAGE_ROOT`
- **Gateway:** ParcelResult dataclass expansion

### Internal Systems

- **parsers/base_parser.py:** Вызов RawStorageManager.save_raw_html()
- **storage/db.py:** Обновление paths в results table
- **orchestrator/scraper_instance.py:** Переход на новую структуру

---

## Testing Strategy

### Unit Tests

- [ ] RawStorageManager.save_raw_html() — сохраняет и возвращает hash
- [ ] RawStorageManager.save_parcel_json() — корректный JSON
- [ ] RawStorageManager.compress_old_html() — сжимает старые файлы
- [ ] Path sanitization — special chars replaced

### Integration Tests

- [ ] Full scrape → parse → save pipeline
- [ ] Migration script на sample data
- [ ] Concurrent writes to same parcel

### Manual Verification

- [ ] Проверить структуру директорий после миграции
- [ ] Убедиться что latest.html symlink работает
- [ ] Проверить что сжатые .gz файлы читаются

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RAW_STORAGE_ROOT` | `storage/raw_v2` | Базовая директория для raw storage |
| `RAW_COMPRESSION_DAYS` | `30` | Через сколько дней сжимать HTML |
| `RAW_DEBUG_ON_FAIL` | `true` | Сохранять ли failed scrape HTML |
| `RAW_COMPRESS_ENABLED` | `true` | Включить ли компрессию |

---

## Open Design Questions

- [ ] **Tier в пути или нет?** Сейчас spec включает `{tier}` в путь. Альтернатива: flat structure без tier.
- [ ] **Latest symlink per-parcel или per-county?** Сейчас per-parcel.
- [ ] **Архивация старше 1 года?** Вынести в отдельный volume или S3?

---

## Approval

- [ ] Reviewed by: [name]
- [ ] Approved on: [date]
- [ ] Notes: [any conditions or clarifications]
