import os, io, json, mimetypes, datetime, http.server, functools
from urllib.parse import unquote, urlparse

TYPE_MAP = {
    'image':    {'.jpg','.jpeg','.png','.gif','.webp','.svg','.ico','.bmp','.tiff'},
    'video':    {'.mp4','.avi','.mov','.mkv','.wmv','.flv','.webm','.m4v'},
    'audio':    {'.mp3','.wav','.flac','.aac','.ogg','.m4a','.wma'},
    'document': {'.pdf','.doc','.docx','.txt','.md','.rtf','.odt','.ppt','.pptx'},
    'code':     {'.py','.js','.ts','.html','.css','.json','.xml','.yaml','.yml',
                 '.toml','.ini','.sh','.bash','.zsh','.rb','.go','.rs','.c',
                 '.cpp','.h','.java','.kt','.swift','.php','.sql','.vue','.jsx','.tsx'},
    'data':     {'.csv','.xlsx','.xls','.db','.sqlite','.parquet'},
    'archive':  {'.zip','.tar','.gz','.rar','.7z','.bz2','.xz','.dmg','.iso'},
}
ICONS  = {'folder':'F','image':'I','video':'V','audio':'A','document':'D',
          'code':'C','data':'S','archive':'Z','file':'F'}
COLORS = {'folder':'#f59e0b','image':'#8b5cf6','video':'#ef4444','audio':'#ec4899',
          'document':'#3b82f6','code':'#10b981','data':'#f97316','archive':'#6366f1','file':'#94a3b8'}
EMO    = {'folder':'\U0001F4C1','image':'\U0001F5BC','video':'\U0001F3AC','audio':'\U0001F3B5',
          'document':'\U0001F4C4','code':'\U0001F4BB','data':'\U0001F4CA','archive':'\U0001F5DC','file':'\U0001F4C4'}

def get_type(ext):
    for t, s in TYPE_MAP.items():
        if ext.lower() in s: return t
    return 'file'

def fmt_size(b):
    if b == 0: return ''
    for u in ['B','KB','MB','GB']:
        if b < 1024: return f"{int(b)} {u}" if u=='B' else f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} TB"

def get_items(directory, url_path):
    items = []
    try:
        entries = sorted(os.scandir(directory), key=lambda e: (not e.is_dir(), e.name.lower()))
        for entry in entries:
            if entry.name.startswith('.'): continue
            is_dir = entry.is_dir(follow_symlinks=False)
            ext = '' if is_dir else os.path.splitext(entry.name)[1].lower()
            ftype = 'folder' if is_dir else get_type(ext)
            try:
                stat = entry.stat()
                size = 0 if is_dir else stat.st_size
                mod  = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
            except Exception:
                size, mod = 0, ''
            url = url_path.rstrip('/') + '/' + entry.name + ('/' if is_dir else '')
            items.append({'name':entry.name,'type':ftype,'ext':ext,'size':size,
                          'size_str':fmt_size(size),'modified':mod,'url':url,
                          'is_dir':is_dir,'icon':EMO.get(ftype,'\U0001F4C4'),
                          'color':COLORS.get(ftype,'#94a3b8')})
    except Exception:
        pass
    return items

def build_breadcrumb(url_path, root_name):
    parts = [p for p in url_path.strip('/').split('/') if p]
    bits  = [f'<a href="/" class="cr">\U0001F3E0 {root_name}</a>']
    for i, p in enumerate(parts):
        href = '/' + '/'.join(parts[:i+1]) + '/'
        if i == len(parts)-1: bits.append(f'<span class="cc">{p}</span>')
        else:                  bits.append(f'<a href="{href}" class="cr">{p}</a>')
    return '<span class="cs">›</span>'.join(bits)

def generate_html(directory, url_path, root_dir):
    items     = get_items(directory, url_path)
    root_name = os.path.basename(root_dir.rstrip('/')) or root_dir
    title     = os.path.basename(directory.rstrip('/')) or root_name
    breadcrumb= build_breadcrumb(url_path, root_name)
    total_sz  = fmt_size(sum(i['size'] for i in items if not i['is_dir']))
    items_json= json.dumps(items, ensure_ascii=False)
    n_folders = sum(1 for i in items if i['is_dir'])
    n_files   = sum(1 for i in items if not i['is_dir'])
    return build_html(title, breadcrumb, total_sz, n_folders, n_files, items_json)

def build_html(title, breadcrumb, total_sz, n_folders, n_files, items_json):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Global Directory</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{--bg:#f1f5f9;--sur:#fff;--bdr:#e2e8f0;--acc:#6366f1;
      --txt:#1e293b;--t2:#64748b;--t3:#94a3b8;--r:12px}}
body{{font-family:'Inter',sans-serif;background:var(--bg);color:var(--txt);font-size:14px;min-height:100vh}}
a{{text-decoration:none;color:inherit}}.hidden{{display:none!important}}
.hdr{{background:var(--sur);border-bottom:1px solid var(--bdr);padding:0 20px;height:54px;
      display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:99;
      box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.logo{{font-weight:700;font-size:15px;white-space:nowrap;flex-shrink:0}}
.bc{{flex:1;display:flex;align-items:center;gap:2px;flex-wrap:wrap;font-size:12px;overflow:hidden}}
.cr{{color:var(--acc);padding:2px 5px;border-radius:5px;font-weight:500;white-space:nowrap}}
.cr:hover{{background:#6366f112}}.cc{{padding:2px 5px;font-weight:600;white-space:nowrap}}
.cs{{color:var(--t3);font-size:14px;padding:0 2px}}
.vb{{display:flex;gap:3px;flex-shrink:0}}
.vbtn{{width:30px;height:30px;border:1.5px solid var(--bdr);background:var(--bg);border-radius:7px;
       cursor:pointer;font-size:14px;display:flex;align-items:center;justify-content:center;transition:all .15s}}
.vbtn:hover,.vbtn.on{{background:var(--acc);color:#fff;border-color:var(--acc)}}
.sbar{{display:flex;align-items:center;gap:10px;padding:10px 20px;background:var(--sur);
       border-bottom:1px solid var(--bdr);flex-wrap:wrap}}
.stat{{font-size:12px;color:var(--t2)}} .stat b{{color:var(--txt);font-weight:600}}
.sdot{{color:var(--bdr);font-size:18px}}
.ctrl{{padding:10px 20px;background:var(--sur);border-bottom:1px solid var(--bdr);
       display:flex;gap:8px;align-items:center;flex-wrap:wrap}}
.sw{{display:flex;align-items:center;gap:7px;border:1.5px solid var(--bdr);border-radius:9px;
     padding:0 11px;height:34px;min-width:200px;background:var(--bg);transition:border .2s}}
.sw:focus-within{{border-color:var(--acc);background:var(--sur)}}
.si{{color:var(--t3);font-size:13px}}.sw input{{border:none;background:transparent;outline:none;
     font-family:inherit;font-size:13px;color:var(--txt);width:100%}}
.xb{{background:none;border:none;cursor:pointer;color:var(--t3);font-size:12px}}
.xb:hover{{color:var(--txt)}}
.tabs{{display:flex;gap:3px;flex-wrap:wrap}}
.tab{{padding:4px 10px;border-radius:7px;border:1.5px solid var(--bdr);background:var(--bg);
      cursor:pointer;font-size:11px;font-weight:500;font-family:inherit;color:var(--t2);
      transition:all .15s;white-space:nowrap}}
.tab:hover{{border-color:var(--acc);color:var(--acc)}}
.tab.on{{background:var(--acc);color:#fff;border-color:var(--acc)}}
.er{{padding:6px 20px 10px;display:flex;align-items:center;gap:6px;flex-wrap:wrap;min-height:36px}}
.el{{font-size:10px;color:var(--t3);font-weight:700;text-transform:uppercase;letter-spacing:.5px}}
.ec{{padding:2px 9px;border-radius:20px;border:1.5px solid var(--bdr);background:var(--sur);
     cursor:pointer;font-size:11px;font-weight:600;font-family:inherit;color:var(--t2);
     transition:all .15s;display:inline-flex;align-items:center;gap:3px}}
.ec:hover{{border-color:var(--acc);color:var(--acc)}}
.ec.on{{background:var(--acc);color:#fff;border-color:var(--acc)}}
.ecn{{background:rgba(0,0,0,.1);border-radius:20px;padding:0 4px;font-size:9px}}
.ec.on .ecn{{background:rgba(255,255,255,.25)}}
.sr{{padding:7px 20px;display:flex;align-items:center;gap:6px;background:var(--bg);
     border-bottom:1px solid var(--bdr)}}
.sl{{font-size:10px;color:var(--t3);font-weight:700;text-transform:uppercase;letter-spacing:.5px}}
.sbtn{{padding:3px 9px;border-radius:5px;border:1px solid var(--bdr);background:var(--sur);
       cursor:pointer;font-size:11px;font-weight:500;font-family:inherit;color:var(--t2);transition:all .15s}}
.sbtn:hover{{border-color:var(--acc);color:var(--acc)}}.sbtn.on{{color:var(--acc);border-color:var(--acc);font-weight:700}}
.wrap{{padding:18px 20px;min-height:300px}}
.gv{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}}
.lv{{display:flex;flex-direction:column;gap:3px}}
.lhdr{{display:grid;grid-template-columns:32px 1fr 80px 70px 120px 28px;gap:8px;
       padding:5px 12px;font-size:10px;font-weight:700;color:var(--t3);text-transform:uppercase;letter-spacing:.4px}}
.card{{display:flex;flex-direction:column;gap:6px;padding:12px;border-radius:var(--r);
       border:1.5px solid var(--bdr);background:var(--sur);transition:all .2s;cursor:pointer;overflow:hidden}}
.card:hover{{box-shadow:0 4px 20px rgba(0,0,0,.08);transform:translateY(-1px);border-color:transparent}}
.fdc{{border-color:#fde68a;background:linear-gradient(135deg,#fffbeb,#fef3c7)}}
.fdc:hover{{box-shadow:0 4px 20px rgba(245,158,11,.15)}}
.ci{{font-size:28px;line-height:1}}.cn{{font-size:11px;font-weight:600;word-break:break-word;line-height:1.4}}
.cm{{font-size:10px;color:var(--t3);margin-top:auto}}
.ct{{display:flex;align-items:flex-start;justify-content:space-between;gap:3px}}
.eb{{font-size:9px;font-weight:700;padding:2px 5px;border-radius:5px;white-space:nowrap;flex-shrink:0}}
.lrow{{display:grid;grid-template-columns:32px 1fr 80px 70px 120px 28px;align-items:center;
       gap:8px;padding:8px 12px;border-radius:8px;background:var(--sur);border:1px solid var(--bdr);
       transition:all .15s;cursor:pointer}}
.lrow:hover{{box-shadow:0 2px 10px rgba(0,0,0,.06);border-color:var(--acc)}}
.lrow.fd{{background:#fffbeb;border-color:#fde68a}}
.ri{{font-size:18px;text-align:center}}.rn{{font-size:12px;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.rt{{font-size:10px;color:var(--t3);text-transform:capitalize}}.rs{{font-size:11px;color:var(--t2);text-align:right}}
.rd{{font-size:10px;color:var(--t3);text-align:right}}.rdl{{text-align:center;font-size:14px;color:var(--t3);opacity:0;transition:opacity .15s}}
.lrow:hover .rdl{{opacity:1;color:var(--acc)}}
.empty{{text-align:center;padding:60px 20px;color:var(--t3);line-height:2}}
.empty .ei{{font-size:44px;margin-bottom:8px}}
</style>
</head>
<body>
<header class="hdr">
  <div class="logo">\U0001F4C1 Global Directory</div>
  <div class="bc">{breadcrumb}</div>
  <div class="vb">
    <button class="vbtn on" id="gb" title="Grid">&#9638;</button>
    <button class="vbtn" id="lb" title="List">&#9776;</button>
  </div>
</header>
<div class="sbar">
  <div class="stat">\U0001F4C1 <b id="sf">{n_folders}</b> Folders</div>
  <span class="sdot">|</span>
  <div class="stat">\U0001F4C4 <b id="sfi">{n_files}</b> Files</div>
  <span class="sdot">|</span>
  <div class="stat">\U0001F4BE <b>{total_sz or '0 B'}</b></div>
  <span class="sdot">|</span>
  <div class="stat">Shown: <b id="sv">{n_folders + n_files}</b></div>
</div>
<div class="ctrl">
  <div class="sw">
    <span class="si">&#128269;</span>
    <input id="si" type="text" placeholder="Search..." autocomplete="off">
    <button class="xb hidden" id="xb">&#10005;</button>
  </div>
  <div class="tabs">
    <button class="tab on" data-f="all">All</button>
    <button class="tab" data-f="folder">\U0001F4C1 Folders</button>
    <button class="tab" data-f="image">\U0001F5BC Images</button>
    <button class="tab" data-f="video">\U0001F3AC Video</button>
    <button class="tab" data-f="audio">\U0001F3B5 Audio</button>
    <button class="tab" data-f="document">\U0001F4C4 Docs</button>
    <button class="tab" data-f="code">\U0001F4BB Code</button>
    <button class="tab" data-f="data">\U0001F4CA Data</button>
    <button class="tab" data-f="archive">\U0001F5DC Archives</button>
  </div>
</div>
<div class="er" id="er"></div>
<div class="sr">
  <span class="sl">Sort</span>
  <button class="sbtn on" data-s="name">Name &#9650;</button>
  <button class="sbtn" data-s="size">Size</button>
  <button class="sbtn" data-s="modified">Date</button>
  <button class="sbtn" data-s="type">Type</button>
</div>
<div class="wrap" id="wrap"></div>
<div class="empty hidden" id="emp"><div class="ei">&#128371;</div><div>Nothing here.</div></div>
<script type="application/json" id="gd">{items_json}</script>
<script>
var ALL = JSON.parse(document.getElementById('gd').textContent);
var ft='all', fe=null, fs='name', fa=true, fq='', vm='grid';
window.onload = function() {{ init(); }};
function init() {{
  buildChips();
  render();
  document.getElementById('si').oninput = function(e) {{
    fq = e.target.value.toLowerCase();
    document.getElementById('xb').classList.toggle('hidden', !fq);
    render();
  }};
  document.getElementById('xb').onclick = function() {{
    fq=''; document.getElementById('si').value='';
    document.getElementById('xb').classList.add('hidden'); render();
  }};
  document.querySelectorAll('.tab').forEach(function(b) {{
    b.onclick = function() {{
      document.querySelectorAll('.tab').forEach(function(x){{x.classList.remove('on');}});
      b.classList.add('on'); ft=b.dataset.f; fe=null;
      document.querySelectorAll('.ec').forEach(function(x){{x.classList.remove('on');}});
      render();
    }};
  }});
  document.querySelectorAll('.sbtn').forEach(function(b) {{
    b.onclick = function() {{
      var k=b.dataset.s;
      if(fs===k){{fa=!fa;}}else{{fs=k;fa=true;}}
      document.querySelectorAll('.sbtn').forEach(function(x){{
        x.textContent=x.textContent.replace(' \u25b2','').replace(' \u25bc','');
        x.classList.remove('on');
      }});
      b.classList.add('on');
      b.textContent+=fa?' \u25b2':' \u25bc';
      render();
    }};
  }});
  document.getElementById('gb').onclick=function(){{
    vm='grid'; document.getElementById('gb').classList.add('on');
    document.getElementById('lb').classList.remove('on'); render();
  }};
  document.getElementById('lb').onclick=function(){{
    vm='list'; document.getElementById('lb').classList.add('on');
    document.getElementById('gb').classList.remove('on'); render();
  }};
}}
function buildChips() {{
  var counts={{}};
  ALL.forEach(function(i){{ if(!i.is_dir && i.ext) counts[i.ext]=(counts[i.ext]||0)+1; }});
  var keys=Object.keys(counts).sort(function(a,b){{return counts[b]-counts[a];}});
  if(!keys.length) return;
  var er=document.getElementById('er');
  var lbl=document.createElement('span'); lbl.className='el'; lbl.textContent='Extensions:';
  er.appendChild(lbl);
  keys.forEach(function(ext) {{
    var c=document.createElement('button'); c.className='ec'; c.dataset.ext=ext;
    c.innerHTML=ext+'<span class="ecn">'+counts[ext]+'</span>';
    c.onclick=function(){{
      if(fe===ext){{fe=null;c.classList.remove('on');}}
      else{{
        fe=ext; document.querySelectorAll('.ec').forEach(function(x){{x.classList.remove('on');}});
        c.classList.add('on'); ft='all';
        document.querySelectorAll('.tab').forEach(function(x){{x.classList.remove('on');}});
        document.querySelector('.tab[data-f="all"]').classList.add('on');
      }}
      render();
    }};
    er.appendChild(c);
  }});
}}
function filtered() {{
  return ALL.filter(function(i) {{
    if(ft!=='all' && i.type!==ft) return false;
    if(fe && i.ext!==fe) return false;
    if(fq && i.name.toLowerCase().indexOf(fq)<0) return false;
    return true;
  }}).sort(function(a,b) {{
    if(a.is_dir!==b.is_dir) return a.is_dir?-1:1;
    var c=0;
    if(fs==='name') c=a.name.localeCompare(b.name);
    else if(fs==='size') c=a.size-b.size;
    else if(fs==='modified') c=a.modified.localeCompare(b.modified);
    else c=a.ext.localeCompare(b.ext);
    return fa?c:-c;
  }});
}}
function render() {{
  var items=filtered();
  document.getElementById('sf').textContent=items.filter(function(i){{return i.is_dir;}}).length;
  document.getElementById('sfi').textContent=items.filter(function(i){{return !i.is_dir;}}).length;
  document.getElementById('sv').textContent=items.length;
  var wrap=document.getElementById('wrap');
  var emp=document.getElementById('emp');
  if(!items.length){{wrap.innerHTML='';emp.classList.remove('hidden');return;}}
  emp.classList.add('hidden');
  if(vm==='list') {{
    wrap.className='wrap lv';
    wrap.innerHTML='<div class="lhdr"><span></span><span>Name</span><span>Type</span><span style="text-align:right">Size</span><span style="text-align:right">Date</span><span></span></div>'+
      items.map(lrow).join('');
  }} else {{
    wrap.className='wrap gv';
    wrap.innerHTML=items.map(gcard).join('');
  }}
}}
function gcard(i) {{
  if(i.is_dir) return '<a href="'+i.url+'" class="card fdc"><div class="ci">'+i.icon+'</div><div class="cn">'+esc(i.name)+'</div><div class="cm">Folder</div></a>';
  var badge=i.ext?'<span class="eb" style="background:'+i.color+'20;color:'+i.color+'">'+i.ext+'</span>':'';
  return '<a href="'+i.url+'" class="card" download><div class="ct"><div class="ci">'+i.icon+'</div>'+badge+'</div><div class="cn">'+esc(i.name)+'</div><div class="cm">'+i.size_str+'</div></a>';
}}
function lrow(i) {{
  var dl=i.is_dir?'':'↓';
  var cls='lrow'+(i.is_dir?' fd':'');
  var extra=i.is_dir?'':' download';
  return '<a href="'+i.url+'" class="'+cls+'"'+extra+'><span class="ri">'+i.icon+'</span><span class="rn" title="'+esc(i.name)+'">'+esc(i.name)+'</span><span class="rt">'+i.type+'</span><span class="rs">'+i.size_str+'</span><span class="rd">'+i.modified+'</span><span class="rdl">'+dl+'</span></a>';
}}
function esc(s){{var d=document.createElement('div');d.appendChild(document.createTextNode(s));return d.innerHTML;}}
</script>
</body>
</html>"""


class FileServerHandler(http.server.SimpleHTTPRequestHandler):
    root_dir = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=self.__class__.root_dir, **kwargs)

    def list_directory(self, path):
        url_path = unquote(urlparse(self.path).path)
        html     = generate_html(path, url_path, self.__class__.root_dir)
        data     = html.encode('utf-8')
        f = io.BytesIO(data)
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(data))
        self.end_headers()
        return f

    def log_message(self, *args):
        pass
    def log_error(self, *args):
        pass


def run_server(directory, port):
    FileServerHandler.root_dir = os.path.realpath(directory)
    server = http.server.HTTPServer(('127.0.0.1', port), FileServerHandler)
    server.serve_forever()
