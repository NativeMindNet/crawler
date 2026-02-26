# Requirements: Local Storage & Synchronization for Tax Lien Parser

> Version: 1.1  
> Status: DRAFT  
> Last Updated: 2026-01-30

## Problem Statement

The parser currently lacks a robust local storage mechanism and a synchronization flow with the rest of the ecosystem. This leads to data loss if the ecosystem (API/Gateway) is unavailable and prevents efficient asynchronous processing of results.

## Goals
1.  **Resilience**: Save scraped/parsed data locally if the Gateway is unavailable.
2.  **Asynchronicity**: De-couple scraping from uploading to allow workers to keep working even with intermittent connectivity.
3.  **Reliability**: Ensure every result is eventually uploaded to the ecosystem.
4.  **Local Task Cache**: Pre-fetch tasks and store them locally to handle temporary "get_work" failures.

## User Stories

### Primary

**As a** system operator  
**I want** the parser to save results locally when the ecosystem is unreachable  
**So that** no collected data is lost during downtime.

**As a** system operator  
**I want** the parser to automatically synchronize local results to the ecosystem once it becomes available  
**So that** data processing remains continuous and automated.

**As a** developer  
**I want** a local queue of tasks/parcels to process  
**So that** I can manage the parsing workload independently of the central API and handle large runs without constant connectivity.

## Acceptance Criteria

### Must Have

1. **Local SQLite Persistence**: Use `aiosqlite` for non-blocking storage.
2. **Offline Buffer**: If the API Gateway is offline, results MUST be saved locally with `synced=false`.
3. **Background Synchronization**: A background task must periodically attempt to upload unsynced results to the Gateway.
4. **Resumable Tasks**: Locally stored tasks should track their status (pending, processing, completed, failed).
5. **Immediate Sync Attempt**: When a task is completed, an immediate upload attempt should be made, falling back to background sync on failure.

### Should Have

1. **Exponential Backoff**: Retries for synchronization with increasing delays.
2. **Local Storage Health**: Basic monitoring/logging of storage status.
3. **Logging**: Detailed logs of synchronization successes and failures.
4. **WAL Mode**: Use Write-Ahead Logging in SQLite for concurrent read/write access.

### Won't Have (This Iteration)

1. Complex conflict resolution.
2. UI for managing the local queue (CLI/Logs only).
3. Encryption of local data.

## Constraints

- **Technical**: Must be compatible with existing Python-based parsers.
- **Performance**: Local storage operations should not bottleneck the scraping process.
- **Platform**: Darwin (development) and Linux (production).

## Open Questions

- [ ] What is the maximum size of the local storage?
- [ ] How long should we keep "synced" results before purging?

## Approval

- [ ] Reviewed by: [name]
- [ ] Approved on: [date]
- [ ] Notes: [any conditions or clarifications]