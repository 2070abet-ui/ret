/**
 * _worker.js 相当（Workers Static Assets + Worker構成のエントリポイント）
 *
 * 役割:
 * 1. 旧URL（.html 付き）へのリクエストを拡張子なし正規URLへ **301 Permanent Redirect** する。
 *    - これによりGoogleが旧URLを恒久的な移転として処理し、正規URL（sitemap/canonical記載の
 *      拡張子なしURL）へシグナルを集約できるようになる。
 *    - 背景: Cloudflareの html_handling="auto-trailing-slash" が返す307は「一時」扱いのため、
 *      GSCで旧URLが「Redirect error」と判定されていた（docs/GSC_REDIRECT_ERROR_CAUSE_AUDIT_2026_08_31.md）。
 * 2. それ以外のリクエストは静的アセットとして配信する。
 *    - env.ASSETS.fetch() が html_handling / not_found_handling を適用するため、
 *      拡張子なしURLの200配信・存在しないURLの404配信は従来通り。
 */
export default {
	async fetch(request, env) {
		const url = new URL(request.url);
		const path = url.pathname;

		// .html 付き旧URL → 拡張子なし正規URLへ 301 Permanent Redirect
		if (path !== '/' && path.endsWith('.html')) {
			let newPath = path.slice(0, -5); // ".html" を除去
			if (newPath.endsWith('/index')) {
				// ディレクトリの index.html → ディレクトリの末尾スラッシュ付き
				newPath = newPath.slice(0, -6) + '/';
			}
			if (newPath === '') {
				// ルート index.html → "/"
				newPath = '/';
			}
			const target = new URL(newPath, url.origin);
			target.search = url.search; // クエリ文字列は維持
			return Response.redirect(target.toString(), 301);
		}

		// それ以外は静的アセットとして配信
		return env.ASSETS.fetch(request);
	},
};
