from fastapi import FastAPI, HTTPException, Query
import requests
from bs4 import BeautifulSoup
import urllib.parse

app = FastAPI()

# ユーザーエージェントとCookieを強化
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Cookie": "age_verified=1; accessAgeDisclaimerPH=1;" # 年齢制限を回避するCookie
}

@app.get("/")
def read_root():
    return {"message": "Pornhub Search API is running. Use /search?q=keyword"}

@app.get("/search")
def search_videos(q: str = Query(..., min_length=1)):
    try:
        encoded_query = urllib.parse.quote(q)
        # 検索パラメータを追加して、より一般的な結果を表示させる
        url = f"https://www.pornhub.com/video/search?search={encoded_query}"
        
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 動画リストを包括的に取得
        video_elements = soup.select("ul#videoSearchResult li.pcVideoListItem, .videoRow, li[data-video-vkey]")
        
        results = []
        for item in video_elements:
            # 不要な要素（広告など）を除外
            if "js-pop" in item.get("class", []) or "advatisement" in item.get("class", []):
                continue
                
            title_tag = item.select_one("span.title a")
            img_tag = item.select_one("img")
            duration_tag = item.select_one(".duration, var.duration")
            
            if title_tag:
                # サムネイル取得ロジック（PornhubのLazyLoadに対応）
                thumb = None
                if img_tag:
                    # 優先順に属性をチェック
                    thumb = (
                        img_tag.get("data-mediumthumb") or 
                        img_tag.get("data-src") or 
                        img_tag.get("data-thumb_url") or 
                        img_tag.get("src")
                    )

                # タイトルとリンク
                title_text = title_tag.get_text(strip=True)
                link = "https://www.pornhub.com" + title_tag["href"]
                
                # 重複チェック（同じ動画が複数取れるのを防ぐ）
                if not any(r['url'] == link for r in results):
                    results.append({
                        "title": title_text,
                        "url": link,
                        "thumbnail": thumb,
                        "duration": duration_tag.get_text(strip=True) if duration_tag else None,
                        "vkey": item.get("data-video-vkey")
                    })
        
        return {
            "query": q,
            "count": len(results),
            "results": results
        }

    except Exception as e:
        # エラー発生時は詳細を返す
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
