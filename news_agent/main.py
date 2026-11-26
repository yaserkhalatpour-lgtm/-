"""RSS-based education news monitor; publishing is disabled unless explicitly enabled."""
import hashlib, html, json, logging, os, re, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import feedparser, requests

BASE=Path(__file__).resolve().parent
DB=Path(os.getenv("NEWS_DB_PATH", str(BASE/"news_seen.sqlite3")))
logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO"), format="%(asctime)s %(levelname)s %(message)s")
log=logging.getLogger("edu-news")
TERMS={
 "حقوق":4,"افزایش حقوق":5,"رتبه‌بندی":5,"معلمان":3,"فرهنگیان":3,
 "استخدام":5,"آزمون استخدامی":5,"بازنشستگی":4,"بخشنامه":4,
 "آموزش و پرورش":3,"وزارت آموزش":4,"امتحانات":3,"مدارس":2,
 "دانشگاه فرهنگیان":4,"دانشجو معلم":4,"حق التدریس":4,
 "تبدیل وضعیت":4,"تعطیلی مدارس":3,"کنکور":2
}
MIN_SCORE=int(os.getenv("NEWS_MIN_SCORE","4"))
PUBLISH=os.getenv("NEWS_PUBLISH_ENABLED","false").lower()=="true"

def feeds():
    raw=os.getenv("NEWS_FEEDS_JSON")
    data=json.loads(raw) if raw else json.loads((BASE/"sources.json").read_text(encoding="utf-8"))
    if not isinstance(data,list): raise ValueError("Feed configuration must be a JSON list")
    return [x for x in data if isinstance(x,dict) and x.get("url")]

def clean(s):
    return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",s or ""))).strip()

def init():
    DB.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(DB) as c:
        c.execute("CREATE TABLE IF NOT EXISTS seen(id TEXT PRIMARY KEY,title TEXT,url TEXT,seen_at TEXT,published INTEGER DEFAULT 0)")

def seen(item_id):
    with sqlite3.connect(DB) as c: return c.execute("SELECT 1 FROM seen WHERE id=?",(item_id,)).fetchone() is not None

def remember(item_id,title,url,published=0):
    with sqlite3.connect(DB) as c:
        c.execute("INSERT OR IGNORE INTO seen VALUES(?,?,?,?,?)",(item_id,title[:500],url[:2000],datetime.now(timezone.utc).isoformat(),published))

def score(title,summary):
    text=(title+" "+summary).casefold()
    hits=[(k,v) for k,v in TERMS.items() if k.casefold() in text]
    return sum(v for _,v in hits),[k for k,_ in hits]

def send(message):
    token=os.environ["TELEGRAM_BOT_TOKEN"]; chat=os.environ["TELEGRAM_CHAT_ID"]
    r=requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
      json={"chat_id":chat,"text":message,"parse_mode":"HTML","disable_web_page_preview":False},timeout=20)
    r.raise_for_status()
    if not r.json().get("ok"): raise RuntimeError("Telegram API rejected the message")

def run():
    init(); candidates=[]
    for src in feeds():
        name=str(src.get("name") or urlparse(src["url"]).netloc)
        try:
            parsed=feedparser.parse(src["url"])
            if parsed.bozo and not parsed.entries:
                log.warning("RSS error for %s: %s",name,parsed.bozo_exception); continue
            for e in parsed.entries[:40]:
                title=clean(getattr(e,"title","")); url=str(getattr(e,"link","") or "")
                summary=clean(getattr(e,"summary","") or getattr(e,"description",""))
                if not title or not url: continue
                item_id=hashlib.sha256(str(getattr(e,"id","") or url).encode()).hexdigest()
                if seen(item_id): continue
                points,hits=score(title,summary)
                if points>=MIN_SCORE: candidates.append((points,item_id,title,summary,url,name,hits))
                else: remember(item_id,title,url)
        except Exception: log.exception("Failed reading %s",name)
    candidates.sort(reverse=True,key=lambda x:x[0])
    for points,item_id,title,summary,url,name,hits in candidates[:int(os.getenv("NEWS_MAX_PER_RUN","8"))]:
        post=("🎓 <b>"+html.escape(title[:350])+"</b>\n\n"+
          (html.escape(summary[:650])+"\n\n" if summary else "")+
          "📰 منبع: "+html.escape(name[:100])+"\n🔗 <a href=\""+html.escape(url,quote=True)+"\">متن خبر</a>"+
          "\n\n🤖 پایشگر اخبار آموزش‌وپرورش")
        if PUBLISH:
            try: send(post); remember(item_id,title,url,1); log.info("Published: %s",title)
            except Exception: log.exception("Telegram publish failed: %s",title)
        else:
            log.info("DRY RUN — not sent: %s | %s",title,url); remember(item_id,title,url)
    log.info("Found %d relevant new items. Publish mode=%s",len(candidates),PUBLISH)

if __name__=="__main__": run()
