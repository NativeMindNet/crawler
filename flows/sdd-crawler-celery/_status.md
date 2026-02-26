# Status: sdd-crawler-celery

## Current Phase

REQUIREMENTS

## Phase Status

DRAFTING

## Last Updated

2026-02-26 by Qwen (SDD mode)

## Blockers

- None - awaiting requirements review

## Progress

- [x] Requirements drafted (initial analysis complete)
- [ ] Requirements approved
- [ ] Specifications drafted
- [ ] Specifications approved
- [ ] Plan drafted
- [ ] Plan approved
- [ ] Implementation started
- [ ] Implementation complete

## Context Notes

Key decisions and context for resuming:

- **Purpose**: This SDD flow captures Celery distributed task queue requirements that were NOT in the main `sdd-crawler` spec
- **Legacy Source**: Analysis of `/legacy/legacy-celery/` directory (celery_app.py, tasks.py, functions.py, platforms/qpublic/)
- **Deployment Mode**: Celery is an **optional** mode alongside SQLite standalone mode, not a replacement
- **Broker**: Redis is the primary broker (legacy compatibility)
- **Monitoring**: Flower dashboard for task monitoring
- **Task Chains**: Preserve legacy patterns (scrape → save → parse → import)

### Legacy Components Analyzed:

1. **celery_app.py**: Basic Celery app with Redis broker
2. **tasks.py**: Task chains (qpublic_main_chain, qpublic_single_url_chain), periodic task setup
3. **functions.py**: Shared utilities (scrape_single_url, save_html, save_json, import_to_db)
4. **platforms/qpublic/qpublic_functions.py**: Platform-specific scraping/parsing logic
5. **requirements.txt**: Celery 5.4.0, Redis 5.2.1, Flower 2.0.1, SeleniumBase 4.34.7

### Key Patterns to Preserve:

- Celery chains for sequential workflows
- Celery groups for parallel URL processing
- Rate limiting via task annotations
- Result backend with expiration
- Periodic scheduling via Celery Beat

## Next Actions

1. **User reviews requirements** - Confirm scope and user stories
2. **Resolve open questions** - Q1-Q7 need answers before specs
3. **Move to SPECIFICATIONS phase** - Design Celery architecture

## Fork History

- This is a new SDD flow forked from analysis of `sdd-crawler` + legacy-celery codebase
- Reason: Capture Celery requirements that were missing from main sdd-crawler spec
