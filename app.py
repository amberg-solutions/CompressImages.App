from flask import Flask, render_template, redirect, request, send_file, Response
from classes import Handler
from uuid import uuid4
from config import BASE_DIR, FILE_DIR
import os
import json
from io import BytesIO
from datetime import datetime
import zipfile

app = Flask(__name__)

SUPPORTED_LANGS = ["de", "fr", "en", "es", "nl", "it"]
DEFAULT_LANG = "en"

@app.before_request
def detect_language():
    if request.path == '/':
        lang = request.accept_languages.best_match(SUPPORTED_LANGS) or DEFAULT_LANG
        return redirect(f"/{lang}")

def load_translations(lang):
    fpath = os.path.join(BASE_DIR, "translations", f"{lang}.json")
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)

@app.route("/")
def root():
    return redirect(f"/{DEFAULT_LANG}", code=301)

@app.route("/<lang>", methods=["GET", "POST"])
def index(lang):
    if lang not in SUPPORTED_LANGS:
        return redirect(f"/{DEFAULT_LANG}")
    t = load_translations(lang)

    compressed, results = False, None
    if request.method == 'POST':
        images = request.files.getlist("images")
        quality = int(request.form.get("quality", 30))
        format = request.form.get("format", "JPEG")

        results = []

        for img in images[:5]:  
            uid = str(uuid4())
            kbBefore, kbAfter = Handler.compress_img(img, uid, quality, format)
            results.append({
                "uid" : uid,
                "kbBefore" : kbBefore,
                "kbAfter" : kbAfter,
                "saved" : round(kbBefore - kbAfter, 2)
            })

        compressed = bool(results)
        return render_template("index.html", lang=lang, compressed=compressed, results=results, t=t, SUPPORTED_LANGS=SUPPORTED_LANGS, format=format)
    
    return render_template("index.html", lang=lang, compressed=compressed, results=results, t=t, SUPPORTED_LANGS=SUPPORTED_LANGS)

@app.route("/<lang>/why-image-compression")
def why_compression(lang):
    if lang not in SUPPORTED_LANGS:
        return redirect(f"/{DEFAULT_LANG}")
    t = load_translations(lang)
    return render_template("why_compression.html", lang=lang, t=t, SUPPORTED_LANGS=SUPPORTED_LANGS)


@app.route("/<lang>/download/<uid>")
def download(lang, uid):
    format = request.args.get("format", "jpeg").lower()

    if lang not in SUPPORTED_LANGS:
        return redirect(f"/{DEFAULT_LANG}")

    img_bytes = Handler.get_img_bytes(uid, format)
    if not img_bytes:
        return render_template("error.html", t=load_translations(lang))

    return send_file(
        BytesIO(img_bytes),
        as_attachment=True,
        download_name=f"{uid}.{format}",
        mimetype=f"image/{format}"
    )

@app.route("/<lang>/download-all")
def download_all(lang):
    format = request.args.get("format", "jpeg").lower()
    uids = request.args.getlist("uids")

    if lang not in SUPPORTED_LANGS:
        return redirect(f"/{DEFAULT_LANG}")

    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for uid in uids:
            img_bytes = Handler.read_img_file(uid, format)  # nur lesen
            if img_bytes:
                zf.writestr(f"{uid}.{format}", img_bytes)
                os.remove(os.path.join(FILE_DIR, f"{uid}.{format}"))

    memory_file.seek(0)
    return send_file(
        memory_file,
        as_attachment=True,
        download_name="compressed_images.zip",
        mimetype="application/zip"
    )


@app.route("/<lang>/privacy")
def privacy(lang):
    if lang not in SUPPORTED_LANGS:
        return redirect(f"/{DEFAULT_LANG}")
    t = load_translations(lang)

    return render_template("privacy.html", lang=lang, t=t, SUPPORTED_LANGS=SUPPORTED_LANGS)

@app.route("/<lang>/imprint")
def imprint(lang):
    if lang not in SUPPORTED_LANGS:
        return redirect(f"/{DEFAULT_LANG}")
    t = load_translations(lang)

    return render_template("imprint.html", lang=lang, t=t, SUPPORTED_LANGS=SUPPORTED_LANGS)

@app.route("/<lang>/contact")
def contact(lang):
    if lang not in SUPPORTED_LANGS:
        return redirect(f"/{DEFAULT_LANG}")
    t = load_translations(lang)

    return render_template("contact.html", lang=lang, t=t, SUPPORTED_LANGS=SUPPORTED_LANGS)

@app.route("/sitemap.xml", methods=["GET"])
def sitemap():
    pages = []

    lastmod = datetime.now().date().isoformat()

    for lang in SUPPORTED_LANGS:
        pages.append(f"""
        <url>
            <loc>https://compressimages.app/{lang}</loc>
            <lastmod>{lastmod}</lastmod>
            <changefreq>weekly</changefreq>
            <priority>0.8</priority>
        </url>
        """)

        pages.append(f"""
        <url>
            <loc>https://compressimages.app/{lang}/why-image-compression</loc>
            <lastmod>{lastmod}</lastmod>
            <changefreq>monthly</changefreq>
            <priority>0.6</priority>
        </url>
        """)

        for slug in ["imprint", "privacy", "contact"]:
            pages.append(f"""
            <url>
                <loc>https://compressimages.app/{lang}/{slug}</loc>
                <lastmod>{lastmod}</lastmod>
                <changefreq>yearly</changefreq>
                <priority>0.3</priority>
            </url>
            """)

    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        {''.join(pages)}
    </urlset>
    """

    return Response(sitemap_xml, mimetype="application/xml")

@app.route("/robots.txt")
def robots_txt():
    content = """User-agent: *
Allow: /

Sitemap: https://compressimages.app/sitemap.xml
"""
    return Response(content, mimetype="text/plain")

@app.errorhandler(404)
def error(error):
    lang = request.accept_languages.best_match(SUPPORTED_LANGS) or DEFAULT_LANG
    if lang not in SUPPORTED_LANGS:
        return redirect(f"/{DEFAULT_LANG}")
    t = load_translations(lang)
    return render_template("error.html", error=error, lang=lang, t=t), 404

if __name__ == '__main__':
    app.run(debug=False, port=9990)