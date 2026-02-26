"""Health check CLI command."""

import httpx


async def health_command(api_url: str) -> None:
    """Check crawler health."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_url}/health")
            response.raise_for_status()
            data = response.json()

            print("✓ Crawler is healthy")
            print(f"  Status: {data.get('status', 'unknown')}")
            print(f"  Queue depth: {data.get('queue_depth', 0)}")
            print(f"  Platform: {data.get('platform', 'unknown')}")

    except httpx.ConnectError:
        print(f"✗ Cannot connect to {api_url}")
        print("  Is the API server running?")
    except httpx.HTTPStatusError as e:
        print(f"✗ HTTP error: {e.response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")
