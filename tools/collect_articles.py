"""Collect reusable Europe PMC articles; fail closed on missing licenses."""
import json, pathlib, urllib.request, urllib.parse, xml.etree.ElementTree as ET, time
out=pathlib.Path("content/Articles"); out.mkdir(parents=True,exist_ok=True)
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"MedicalAI educational content builder/0.8"}),timeout=60) as r: return r.read()
base="https://www.ebi.ac.uk/europepmc/webservices/rest/"
query='OPEN_ACCESS:Y AND HAS_FT:Y AND (laparoscopic surgery OR surgical anatomy OR surgical instruments)'
data=json.loads(get(base+"search?"+urllib.parse.urlencode({"query":query,"format":"json","pageSize":50,"resultType":"core"})))
report=[]
for row in data.get("resultList",{}).get("result",[]):
    pmc=row.get("pmcid","")
    if not pmc.startswith("PMC") or not pmc[3:].isdigit(): continue
    try:
        raw=get(base+pmc+"/fullTextXML")
        root=ET.fromstring(raw)
        licenses=root.findall(".//license")
        links=[v for e in licenses for node in e.iter() for k,v in node.attrib.items() if k.endswith("href")]
        allowed={"https://creativecommons.org/licenses/by/4.0/","http://creativecommons.org/licenses/by/4.0/","https://creativecommons.org/licenses/by/3.0/","http://creativecommons.org/licenses/by/3.0/"}
        approved=[l for l in links if l in allowed]
        body=root.find("body")
        if not approved or body is None: continue
        # Preserve original XML, including author details, references, and attribution.
        # Third-party figures may have separate restrictions; no external images are copied.
        (out/(pmc+".xml")).write_bytes(raw)
        report.append({"id":pmc,"title":row.get("title"),"license":approved[0],"source":"https://pmc.ncbi.nlm.nih.gov/articles/"+pmc+"/","bytes":len(raw),"review_required":True})
        if len(report)>=12: break
        time.sleep(.4)
    except Exception as e: print(pmc,type(e).__name__,str(e)[:200])
(out/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("Collected",len(report),"original XML articles")
if not report: raise SystemExit("No licensed articles collected")
