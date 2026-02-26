"""Bulk ingestion routes."""

from fastapi import APIRouter, HTTPException

from crawler.api.schemas import BulkIngestRequest, BulkStatusResponse

router = APIRouter()


@router.post("/ingest", response_model=BulkStatusResponse)
async def start_bulk_ingest(request_data: BulkIngestRequest):
    """Start bulk ingestion job."""
    from fastapi import Request
    request = Request.scope.get("request")
    lpm = request.app.state.lpm if request else None

    if not lpm:
        raise HTTPException(status_code=500, detail="LPM not initialized")

    # Import pipeline
    from crawler.bulk.pipeline import BulkIngestionPipeline

    pipeline = BulkIngestionPipeline(lpm, request_data.platform)

    try:
        job_id = await pipeline.ingest(
            file_path=request_data.file_path,
            profile_name=request_data.profile,
        )

        job = await lpm.get_bulk_job(job_id)
        if not job:
            raise HTTPException(status_code=500, detail="Failed to create job")

        return BulkStatusResponse.model_validate(job)

    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}", response_model=BulkStatusResponse)
async def get_bulk_status(job_id: str):
    """Get bulk job status."""
    from fastapi import Request
    request = Request.scope.get("request")
    lpm = request.app.state.lpm if request else None

    if not lpm:
        raise HTTPException(status_code=500, detail="LPM not initialized")

    job = await lpm.get_bulk_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return BulkStatusResponse.model_validate(job)
