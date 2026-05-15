from pathlib import Path


ASSETS_DIR = Path("repeater/web/html/assets")

patched_preload = False
patched_router = False

for path in ASSETS_DIR.glob("*.js"):
    text = path.read_text(encoding="utf-8")
    text = text.replace("`/assets/", "`assets/")
    text = text.replace('"/assets/', '"assets/')
    text = text.replace("'/assets/", "'assets/")
    text = text.replace("`/images/", "`images/")
    text = text.replace('"/images/', '"images/')
    text = text.replace("'/images/", "'images/")
    text = text.replace("`/static/", "`static/")
    text = text.replace('"/static/', '"static/')
    text = text.replace("'/static/", "'static/")
    if "function(e){return`/`+e}" in text:
        text = text.replace(
            "function(e){return`/`+e}",
            "function(e){return(window.PyMCHAJoinAsset?window.PyMCHAJoinAsset(e):e)}",
            1,
        )
        patched_preload = True
    if "history:r(`/`),routes:" in text:
        text = text.replace(
            "history:r(`/`),routes:",
            "history:r(window.PyMCHABasePath||`/`),routes:",
            1,
        )
        patched_router = True
    path.write_text(text, encoding="utf-8")

for path in ASSETS_DIR.glob("*.css"):
    text = path.read_text(encoding="utf-8")
    text = text.replace("url(/assets/", "url(")
    text = text.replace('url("/assets/', 'url("')
    text = text.replace("url('/assets/", "url('")
    text = text.replace("url(/images/", "url(../images/")
    text = text.replace('url("/images/', 'url("../images/')
    text = text.replace("url('/images/", "url('../images/")
    text = text.replace("url(/static/", "url(../static/")
    text = text.replace('url("/static/', 'url("../static/')
    text = text.replace("url('/static/", "url('../static/")
    path.write_text(text, encoding="utf-8")

if not patched_preload:
    raise RuntimeError("Could not patch Vite modulepreload asset base in upstream pyMC UI")

if not patched_router:
    raise RuntimeError("Could not patch Vue router base in upstream pyMC UI")
