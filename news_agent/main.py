"""RSS news monitor with a persistent pending queue and retry-safe Telegram publishing."""
import hashlib, html, json, logging, os, re, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import requests

BASE = Path(__file__).resolve().parent
DB = Path(os.getenv("NEWS_DB_PATH", str(BASE / "news_seen.sqlite3")))
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("edu-news")

TERMS = {
    "حقوق": 4, "افزایش حقوق": 5, "رتبه‌بندی": 5, "معلمان": 3, "فرهنگیان": 3,
    "استخدام": 5, "آزمون استخدامی": 5, "بازنشستگی": 4, "بخشنامه": 4,
    "آموزش و پرورش": 3, "وزارت آموزش": 4, "امتحانات": 3, "مدارس": 2,
    "دانشگاه فرهنگیان": 4, "دانشجو معلم": 4, "حق التدریس": 4,
    "تبدیل وضعیت": 4, "تعطیلی مدارس": 3, "کنکور": 2
}
MIN_SCORE = int(os.getenv("NEWS_MIN_SCORE", "4"))
PUBLISH = os.getenv("NEWS_PUBLISH_ENABLED", "false").lower() == "true"
MAX_PER_RUN = int(os.getenv("NEWS_MAX_PER_RUN", "8"))


def feeds():
    raw = os.getenv("NEWS_FEEDS_JSON")
    data = json.loads(raw) if raw else json.loads((BASE / "sources.json").read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Feed configuration must be a JSON list")
    return [x for x in data if isinstance(x, dict) and x.get("url")]


def clean(value):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value or ""))).strip()


def init():
    DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seen (
                id TEXT PRIMARY KEY, title TEXT, url TEXT, seen_at TEXT,
                published INTEGER DEFAULT 0, summary TEXT DEFAULT '',
                source TEXT DEFAULT '', score INTEGER DEFAULT 0,
                eligible INTEGER DEFAULT 0, published_at TEXT DEFAULT ''
            )
        """)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(seen)")}
        migrations = {
            "summary": "ALTER TABLE seen ADD COLUMN summary TEXT DEFAULT ''",
            "source": "ALTER TABLE seen ADD COLUMN source TEXT DEFAULT ''",
            "score": "ALTER TABLE seen ADD COLUMN score INTEGER DEFAULT 0",
            "eligible": "ALTER TABLE seen ADD COLUMN eligible INTEGER DEFAULT 0",
            "published_at": "ALTER TABLE seen ADD COLUMN published_at TEXT DEFAULT ''",
        }
        for name, sql in migrations.items():
            if name not in columns:
                conn.execute(sql)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_seen_queue ON seen(eligible, published, published_at)")


def score_item(title, summary):
    text = (title + " " + summary).casefold()
    hits = [(word, points) for word, points in TERMS.items() if word.casefold() in text]
    return sum(points for _, points in hits), [word for word, _ in hits]


def entry_date(entry):
    parsed = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if parsed:
        try:
            from calendar import timegm
            return datetime.fromtimestamp(timegm(parsed), timezone.utc).isoformat()
        except (OverflowError, ValueError, TypeError):
            pass
    return datetime.now(timezone.utc).isoformat()


def collect():
    added = 0
    for source_config in feeds():
        source_name = str(source_config.get("name") or urlparse(source_config["url"]).netloc)
        try:
            parsed = feedparser.parse(source_config["url"])
            if parsed.bozo and not parsed.entries:
                log.warning("RSS error for %s: %s", source_name, parsed.bozo_exception)
                continue
            for entry in parsed.entries[:60]:
                title = clean(getattr(entry, "title", ""))
                url = str(getattr(entry, "link", "") or "")
                summary = clean(getattr(entry, "summary", "") or getattr(entry, "description", ""))
                if not title or not url:
                    continue
                raw_id = str(getattr(entry, "id", "") or url)
                item_id = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()
                points, hits = score_item(title, summary)
                eligible = 1 if points >= MIN_SCORE else 0
                with sqlite3.connect(DB) as conn:
                    cur = conn.execute(
                        """INSERT OR IGNORE INTO seen
                           (id,title,url,seen_at,published,summary,source,score,eligible,published_at)
                           VALUES(?,?,?,?,0,?,?,?,?,?)""",
                        (item_id, title[:500], url[:2000], datetime.now(timezone.utc).isoformat(),
                         summary[:3000], source_name[:100], points, eligible, entry_date(entry))
                    )
                    if cur.rowcount and eligible:
                        added += 1
                        log.info("Queued: %s | score=%d | matched=%s", title, points, ", ".join(hits))
        except Exception:
            log.exception("Failed reading %s", source_name)
    log.info("New relevant items added to queue: %d", added)


def send(message):
    token = os.environ["TELEGRAM_BOT_TOKEN"].strip()
    chat = os.environ["TELEGRAM_CHAT_ID"].strip()
    if not token or not chat:
        raise RuntimeError("Telegram configuration error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is empty")
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat, "text": message, "parse_mode": "HTML", "disable_web_page_preview": False},
        timeout=25
    )
    try:
        result = response.json()
    except ValueError:
        result = {}
    if not response.ok or not result.get("ok"):
        description = result.get("description") or response.text[:500] or "No error description returned"
        error_code = result.get("error_code", response.status_code)
        raise RuntimeError(f"Telegram API error {error_code}: {description}")


def pending_items():
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(
            """SELECT id,title,url,summary,source,score FROM seen
               WHERE eligible=1 AND published=0
               ORDER BY published_at ASC, seen_at ASC LIMIT ?""",
            (MAX_PER_RUN,)
        ).fetchall()


def mark_published(item_id):
    with sqlite3.connect(DB) as conn:
        conn.execute("UPDATE seen SET published=1 WHERE id=?", (item_id,))


def publish_queue():
    rows = pending_items()
    log.info("Pending relevant news waiting to publish: %d (showing up to %d)", len(rows), MAX_PER_RUN)
    if not PUBLISH:
        log.warning("Publish mode is OFF; queued news are being kept for later.")
        return
    sent = 0
    for item in rows:
        title = item["title"] or ""
        url = item["url"] or ""
        summary = item["summary"] or ""
        source = item["source"] or "منبع خبری"
        post = (
            "🎓 <b>" + html.escape(title[:350]) + "</b>\n\n" +
            (html.escape(summary[:650]) + "\n\n" if summary else "") +
            "📰 منبع: " + html.escape(source[:100]) +
            "\n🔗 <a href=\"" + html.escape(url, quote=True) + "\">متن خبر</a>" +
            "\n\n🤖 پایشگر اخبار آموزش‌وپرورش | @amoozeshjam"
        )
        try:
            send(post)
            mark_published(item["id"])
            sent += 1
            log.info("Published: %s", title)
        except Exception:
            log.exception("Telegram publish failed; item remains queued for retry: %s", title)
            break
    log.info("Successfully published this run: %d", sent)


def run():
    init()
    collect()
    publish_queue()


if __name__ == "__main__":
    run()
