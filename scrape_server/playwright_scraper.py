import asyncio
from playwright.async_api import async_playwright
import json
import re
from datetime import datetime
from typing import Set, List, Dict, Any

class Scraper:
    def __init__(self, 
                 navigation_timeout: int = 60000,
                 wait_for: str = 'domcontentloaded'):
        self.video_urls: Set[str] = set()
        self.context = None
        self.browser = None
        self.page = None
        self.navigation_timeout = navigation_timeout
        self.wait_for = wait_for

    async def __aenter__(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        self.page = await self.context.new_page()
        # self.page.on("request", lambda request: print(">>", request.method, request.url))
        self.page.on("response", self.process_response)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def process_response(self, response):
        content_type = response.headers.get("content-type", "")
        # Try to get response body
        response_data = ""
        try:
            if any(text_type in content_type.lower() for text_type in ['text', 'json', 'xml', 'javascript']):
                # Retrieve the response body
                response_data = await response.text()
            else:
                response_data = f'Binary content type: {content_type}'
        except Exception as body_error:
            response_data = f'Could not retrieve body: {str(body_error)}'

        # Check for video URLs
        if '.mp4' in response.url:
            self.video_urls.add(response.url)

        if len(response_data) != 0:
            mp4_urls = re.findall(r'https?://[^\s<>"]+?\.mp4', response_data)
            self.video_urls.update(mp4_urls)

    async def get_videolinks(self):
        src_urls = []

        # Get video elements
        video_elements = await self.page.query_selector_all('video')
        for video in video_elements:
            src = await video.get_attribute('src')
            if src:
                src_urls.append(src)

        # Get iframe elements
        iframe_elements = await self.page.query_selector_all('iframe')
        for iframe in iframe_elements:
            src = await iframe.get_attribute('src')
            if src:
                src_urls.append(src)

        # Get Source elements
        src_elements = await self.page.query_selector_all("source[type='video/mp4']")
        for source in src_elements:
            src = await source.get_attribute('src')
            if src:
                src_urls.append(src)

        # Filter for video URLs
        video_src_pattern = r'https?://[^\s<>"]+?\.mp4'
        src_urls = [s for s in src_urls if re.search(video_src_pattern, s)]

        print(f"Source URLs FOUND = {src_urls}")
        self.video_urls.update(src_urls)

    async def scrape_page(self, url: str):
        try:
            self.video_urls.clear()

            print(f"Navigating to {url}...")
            await self.page.goto(
                url,
                timeout=self.navigation_timeout,
                wait_until=self.wait_for
            )
            await asyncio.sleep(3)  # Allow for dynamic content to load

            # Process the document for potential video tags, iframes
            await self.get_videolinks()
            return list(self.video_urls)

        except Exception as e:
            print(f"Error during scraping: {e}")

    async def save_responses(self, filename: str):
        try:
            output = {
                'video_urls': list(self.video_urls),
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, default=str)
            
            print(f"Successfully saved {len(self.video_urls)} video URLs to {filename}")
        except Exception as e:
            print(f"Error saving responses: {e}")

    async def close(self):
        self.video_urls.clear()
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

# # Example usage:
# async def main():
#     async with Scraper(navigation_timeout=60000, wait_for='domcontentloaded') as scraper:
#         await scraper.scrape_page("https://www.koco.com/article/oklahoma-city-i40-anderson-road-multivehicle-crash-traffic/62827738")
#         await scraper.save_responses("video_urls.json")

# if __name__ == "__main__":
#     asyncio.run(main())