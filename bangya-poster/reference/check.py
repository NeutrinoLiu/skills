#!/usr/bin/env python3
"""Report every box whose children spill outside it, measured by real geometry.

scrollHeight is unreliable for overflowing flex children in Chrome, so this
compares each container's rect against the union rect of its descendants.
"""
import json, os, re, subprocess
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SNIP = """<pre id="OV"></pre><script>
function ready(){
  var imgs = Array.prototype.slice.call(document.images);
  var pending = imgs.filter(function(i){return !(i.complete && i.naturalWidth>0);});
  return Promise.all(pending.map(function(i){
    return new Promise(function(res){ i.addEventListener('load',res); i.addEventListener('error',res); });
  })).then(function(){ return document.fonts ? document.fonts.ready : null; });
}
function go(){
  var out=[];
  document.querySelectorAll('.poster,.sheet,.cols,.cl,.col,.half,.grid,.gr,.seqs,.quad,.rt,ol.pipe,dl.metrics,.stages,.hd').forEach(function(e){
    var r=e.getBoundingClientRect(), b=r.bottom, rt=r.right, ok=true;
    var kids=e.querySelectorAll('*');
    var maxB=r.top, maxR=r.left;
    for(var i=0;i<kids.length;i++){
      var k=kids[i].getBoundingClientRect();
      if(k.width===0&&k.height===0) continue;
      if(k.bottom>maxB) maxB=k.bottom;
      if(k.right>maxR) maxR=k.right;
    }
    var oy=maxB-b, ox=maxR-rt;
    if(oy>1.5||ox>1.5){
      var h=e.querySelector('.sh,.bar,.sub,th');
      out.push({sel:e.className.split(' ').slice(0,2).join('.'),
                lbl:(h?h.textContent:'').replace(/\\s+/g,' ').slice(0,40),
                oy:Math.round(oy), ox:Math.round(ox),
                w:Math.round(r.width), h:Math.round(r.height)});
    }});
  var imgs=Array.prototype.slice.call(document.images);
  var ok=imgs.filter(function(i){return i.complete&&i.naturalWidth>0;}).length;
  document.getElementById('OV').textContent='J'+JSON.stringify({loaded:ok,total:imgs.length,boxes:out})+'J';
}
ready().then(go);
setTimeout(go,6000);
</script>"""

src = open(os.path.join(HERE, "poster.html"), encoding="utf-8").read()
# must live beside poster.html so relative asset paths resolve
tmp = os.path.join(HERE, "_check.tmp.html")
open(tmp, "w", encoding="utf-8").write(src.replace("</body>", SNIP + "</body>"))
dom = subprocess.run([CHROME, "--headless", "--disable-gpu", "--virtual-time-budget=20000",
                      "--window-size=1400,1000", "--dump-dom", "file://" + tmp],
                     capture_output=True, text=True).stdout
os.remove(tmp)
m = re.search(r"J(\{.*?\})J", dom, re.S)
data = json.loads(m.group(1)) if m else {"loaded":0,"total":0,"boxes":[]}
items = data["boxes"]
if data["loaded"] != data["total"]:
    print(f"!! only {data['loaded']}/{data['total']} images loaded — measurement is NOT trustworthy")
else:
    print(f"{data['total']} images loaded")
if not items:
    print("no overflow — every box contains its children")
else:
    print(f"{len(items)} box(es) whose children spill out:\n")
    print(f"{'element':16}{'label':42}{'box':>13}{'over-y':>8}{'over-x':>8}")
    for i in sorted(items, key=lambda x: -max(x['oy'], x['ox'])):
        print(f"{i['sel']:16}{i['lbl']:42}{f'{i[chr(119)]}x{i[chr(104)]}':>13}"
              f"{i['oy']:>8}{i['ox']:>8}")
