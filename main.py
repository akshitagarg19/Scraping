from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from bs4 import BeautifulSoup

app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

WIKI_BASE_URL = "https://en.wikipedia.org/wiki/"

@app.get("/api/outline", response_model=str)
async def get_outline(country: str = Query(..., description="Country name to fetch Wikipedia outline for")):
    url = WIKI_BASE_URL + country.replace(" ", "_")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Wikipedia page not found")

    soup = BeautifulSoup(response.text, "html.parser")

    # Find page title from <h1 id="firstHeading">
    page_title_tag = soup.find("h1", id="firstHeading")
    if not page_title_tag:
        raise HTTPException(status_code=500, detail="Could not find page title")

    page_title = page_title_tag.text.strip()

    # Extract all headings (h1 to h6) inside the content div (to avoid nav/ads)
    content_div = soup.find("div", id="mw-content-text")
    if not content_div:
        raise HTTPException(status_code=500, detail="Could not find content on page")

    headings = content_div.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])

    # Build markdown outline
    markdown_lines = ["## Contents", "", f"# {page_title}", ""]

    for h in headings:
        level = int(h.name[1])
        text = h.get_text(strip=True)
        if text:
            markdown_lines.append(f"{'#' * level} {text}")

    markdown_result = "\n\n".join(markdown_lines)

    return markdown_result
