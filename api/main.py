from fastapi import FastAPI, HTTPException, Query
import requests
from bs4 import BeautifulSoup
import urllib.parse

app = FastAPI()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
}

@app.get("/")
def read_root():
    return {"message": "Pornhub Search API is running. Use /search?q=keyword"}

@app.get("/search")
def search_videos(q: str = Query(..., min_length=1)):
    try:
        encoded_query = urllib.parse.quote(q)
        # 検索結果を確実に取得するため、パラメータを少し追加
        url = f"https://www.pornhub.com/video/search?search={encoded_query}"
        
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # セレクタをより柔軟に変更
        video_elements = soup.select("ul#videoSearchResult li[data-video-vkey]")
        
        # 万が一上記で取れない場合の予備セレクタ
        if not video_elements:
            video_elements = soup.select(".pcVideoListItem")

        results = []
        for item in video_elements:
            if "js-pop" in item.get("class", []):
                continue
                
            title_tag = item.select_one("span.title a")
            img_tag = item.select_one("img")
            duration_tag = item.select_one(".duration")
            
            if title_tag:
                # サムネイルURLの取得ロジックを強化
                thumb = None
                if img_tag:
                    thumb = img_tag.get("data-mediumthumb") or img_tag.get("data-src") or img_tag.get("src")

                results.append({
                    "title": title_tag.get_text(strip=True),
                    "url": "https://www.pornhub.com" + title_tag["href"],
                    "thumbnail": thumb,
                    "duration": duration_tag.get_text(strip=True) if duration_tag else None,
                    "vkey": item.get("data-video-vkey") # 動画固有ID
                })
        
        return {
            "query": q,
            "count": len(results),
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
