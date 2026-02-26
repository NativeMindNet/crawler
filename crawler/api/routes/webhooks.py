"""Webhook routes."""

from fastapi import APIRouter, HTTPException
import httpx

from crawler.api.schemas import WebhookTestRequest, WebhookTestResponse

router = APIRouter()


@router.post("/test", response_model=WebhookTestResponse)
async def test_webhook(request_data: WebhookTestRequest):
    """Test webhook endpoint."""
    try:
        async with httpx.AsyncClient() as client:
            # Send test payload
            payload = {
                "event": "test",
                "message": "This is a test webhook",
            }

            headers = {}
            if request_data.secret:
                # Add HMAC signature
                from crawler.webhooks.signer import WebhookSigner
                signer = WebhookSigner(request_data.secret)
                headers["X-Webhook-Signature"] = signer.sign(payload)

            response = await client.post(
                request_data.url,
                json=payload,
                headers=headers,
                timeout=10.0,
            )

            return WebhookTestResponse(
                success=response.status_code < 400,
                status_code=response.status_code,
                response_body=response.text[:1000],  # Limit response size
                error=None,
            )

    except httpx.ConnectError as e:
        return WebhookTestResponse(
            success=False,
            status_code=None,
            response_body=None,
            error=f"Connection failed: {e}",
        )
    except httpx.TimeoutException as e:
        return WebhookTestResponse(
            success=False,
            status_code=None,
            response_body=None,
            error=f"Request timed out: {e}",
        )
    except Exception as e:
        return WebhookTestResponse(
            success=False,
            status_code=None,
            response_body=None,
            error=str(e),
        )


@router.post("/receive")
async def receive_webhook():
    """
    Receive incoming webhook (for bidirectional sync).
    
    This endpoint allows the crawler to receive tasks or updates
    from an external gateway.
    """
    from fastapi import Request
    request = Request.scope.get("request")

    # Parse incoming data
    data = await request.json()

    # Process based on event type
    event = data.get("event")

    if event == "task.create":
        # Create task from gateway
        lpm = request.app.state.lpm
        url = data.get("url")
        platform = data.get("platform", request.app.state.platform)
        priority = data.get("priority", 0)

        if url:
            task_id = await lpm.add_task(url, platform, priority)
            return {"status": "created", "task_id": task_id}

    elif event == "task.cancel":
        # Cancel task
        lpm = request.app.state.lpm
        task_id = data.get("task_id")

        if task_id:
            task = await lpm.get_task(task_id)
            if task and task.status.value == "pending":
                await lpm.task_repo.delete(task_id)
                return {"status": "cancelled"}

    return {"status": "received"}
