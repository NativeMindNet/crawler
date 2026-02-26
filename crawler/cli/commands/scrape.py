"""Scrape CLI command."""

import asyncio
from pathlib import Path
from typing import Optional

from crawler.lpm import LocalPersistenceManager
from crawler.config_loader import ConfigLoader
from crawler.scraper.scraper import Scraper
from crawler.parser.parser import Parser


async def scrape_command(
    url: str,
    platform: str,
    output: Optional[Path],
    parse: bool,
) -> None:
    """Scrape and optionally parse a single URL."""
    import os

    # Setup paths
    config_dir = os.environ.get("CONFIG_DIR", "/config")
    data_dir = os.environ.get("DATA_DIR", "/data")
    db_path = os.environ.get("DB_PATH", "/data/state/crawler.db")

    # Load config
    config_loader = ConfigLoader(config_dir)
    config = config_loader.load(platform)

    if not config:
        print(f"Error: Platform '{platform}' not found in {config_dir}")
        return

    # Initialize LPM
    lpm = LocalPersistenceManager(db_path, data_dir)
    await lpm.initialize()

    try:
        # Scrape
        print(f"Scraping {url}...")
        scraper = Scraper(config, headless=True)
        content = await scraper.fetch(url)
        print(f"Scraped {len(content.html)} bytes")

        # Save raw HTML
        raw_path = lpm.get_raw_html_path("manual", platform)
        await lpm.save_text(content.html, raw_path)
        print(f"Saved raw HTML to {raw_path}")

        if parse:
            # Parse
            print("Parsing...")
            parser = Parser(config)
            result = parser.parse(content.html)
            result.task_id = "manual"
            result.platform = platform

            if output:
                # Save to specified output
                import json
                output.parent.mkdir(parents=True, exist_ok=True)
                with open(output, "w") as f:
                    json.dump(result.to_dict(), f, indent=2, default=str)
                print(f"Saved result to {output}")
            else:
                # Save to LPM
                result_path = lpm.get_result_path("manual", platform)
                await lpm.save_result("manual", platform, result.to_dict())
                print(f"Saved result to {result_path}")

            print(f"\nParsed data:")
            print(f"  Parcel ID: {result.parcel_id}")
            print(f"  Fields: {len(result.data)}")
            print(f"  Images: {len(result.image_urls)}")
            print(f"  Discovered links: {len(result.discovered_links)}")

    finally:
        await lpm.close()
        if 'scraper' in locals():
            await scraper.close()
