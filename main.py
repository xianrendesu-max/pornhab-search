from fastapi import FastAPI, HTTPException, Query
import requests
from bs4 import BeautifulSoup
import urllib.parse

app = FastAPI()

# ユーザーエージェントを設定（ブロック対策）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

@app.get("/")
def read_root():
    return {"message": "Pornhub Search API is running. Use /search?q=keyword"}

@app.get("/search")
def search_videos(q: str = Query(..., min_length=1)):
    try:
        # キーワードをURLエンコード
        encoded_query = urllib.parse.quote(q)
        url = f"https://www.pornhub.com/video/search?search={encoded_query}"
        
        # ページ取得
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        # スクレイピング解析
        soup = BeautifulSoup(response.text, "html.parser")
        video_elements = soup.select("ul#videoSearchResult li.pcVideoListItem")
        
        results = []
        for item in video_elements:
            # 広告や無効な要素をスキップ
            if "js-pop" in item.get("class", []):
                continue
                
            title_tag = item.select_one("span.title a")
            img_tag = item.select_one("div.img img")
            duration_tag = item.select_one("var.duration")
            
            if title_tag:
                results.append({
                    "title": title_tag.get_text(strip=True),
                    "url": "https://www.pornhub.com" + title_tag["href"],
                    "thumbnail": img_tag.get("data-mediumthumb") or img_tag.get("src") if img_tag else None,
                    "duration": duration_tag.get_text(strip=True) if duration_tag else None
                })
        
        return {
            "query": q,
            "count": len(results),
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Vercel用にアプリを公開
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
