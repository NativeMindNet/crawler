"""Scrape operation routes."""

from fastapi import APIRouter, HTTPException
import uuid
import asyncio

from crawler.api.schemas import ScrapeRequest, ScrapeResponse

router = APIRouter()


@router.post("", response_model=ScrapeResponse)
async def scrape_url(request_data: ScrapeRequest):
    """
    Scrape and optionally parse a single URL.
    
    This is a synchronous operation that:
    1. Fetches the URL
    2. Optionally parses the content
    3. Saves results
    4. Returns the parsed data
    """
    from fastapi import Request
    request = Request.scope.get("request")
    lpm = request.app.state.lpm if request else None
    config_loader = request.app.state.config_loader if request else None

    if not lpm or not config_loader:
        raise HTTPException(status_code=500, detail="Services not initialized")

    # Load platform config
    config = config_loader.load(request_data.platform)
    if not config:
        raise HTTPException(
            status_code=400,
            detail=f"Platform '{request_data.platform}' not found",
        )

    task_id = str(uuid.uuid4())

    try:
        # Import scraper and parser
        from crawler.scraper.scraper import Scraper
        from crawler.parser.parser import Parser

        # Initialize components
        scraper = Scraper(config, headless=True)
        parser = Parser(config)

        # Fetch content
        content = await scraper.fetch(request_data.url)

        # Parse if requested
        result = None
        if request_data.parse:
            result = parser.parse(content.html)
            result.task_id = task_id

        # Save raw HTML
        raw_path = lpm.get_raw_html_path(task_id, request_data.platform)
        await lpm.save_text(content.html, raw_path)

        # Save result if parsed
        result_path = None
        if result:
            result_path = await lpm.save_result(
                task_id,
                request_data.platform,
                result.to_dict(),
            )

        # Build response
        response = ScrapeResponse(
            task_id=task_id,
            status="completed",
            parcel_id=result.parcel_id if result else None,
            data=result.data if result else None,
            image_urls=result.image_urls if result else [],
            external_links=result.external_links if result else {},
            raw_paths={
                "html": str(raw_path),
            },
            error=None,
        )

        await scraper.close()
        return response

    except Exception as e:
        # Mark task as failed
        await lpm.fail_task(task_id, str(e))

        return ScrapeResponse(
            task_id=task_id,
            status="failed",
            parcel_id=None,
            data=None,
            image_urls=[],
            external_links={},
            raw_paths={},
            error=str(e),
        )
