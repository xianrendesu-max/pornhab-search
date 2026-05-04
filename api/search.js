const pornhub = require('@justalk/pornhub-api');

module.exports = async (req, res) => {
    // クエリパラメータから検索ワードを取得
    const { q } = req.query;

    if (!q) {
        return res.status(400).json({ error: 'Query parameter "q" is required' });
    }

    try {
        // ライブラリを使用して検索
        // page: 検索ページ, thumbsize: サムネイルサイズ
        const results = await pornhub.search(q);

        // Vercelは自動的にJSONとしてレスポンスを返します
        res.status(200).json({
            query: q,
            count: results.results.length,
            results: results.results.map(video => ({
                title: video.title,
                url: video.link,
                thumbnail: video.preview, // ライブラリが正しいサムネURLを抽出してくれます
                duration: video.duration,
                hd: video.hd,
                premium: video.premium
            }))
        });
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Failed to fetch data from Pornhub' });
    }
};
