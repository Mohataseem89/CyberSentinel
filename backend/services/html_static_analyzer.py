"""Static HTML heuristics. This module never renders HTML or performs network I/O."""
import base64, re
from bs4 import BeautifulSoup

DANGEROUS_SCHEMES=('javascript:','data:text/html','vbscript:','file:')
EXECUTABLE_EXT=('.exe','.msi','.scr','.bat','.cmd','.ps1','.jar','.apk','.dmg','.pkg','.deb','.rpm')
URL_ATTRS=('href','src','action','data')

def analyze_html_bytes(raw: bytes) -> dict:
    text=raw.decode('utf-8', errors='replace')
    soup=BeautifulSoup(text, 'html.parser')
    indicators=[]
    scripts=soup.find_all('script')
    inline_handlers=sum(1 for tag in soup.find_all(True) for a in tag.attrs if str(a).lower().startswith('on'))
    if scripts: indicators.append({'code':'scripts_present','severity':'medium','count':len(scripts)})
    if inline_handlers: indicators.append({'code':'inline_event_handlers','severity':'medium','count':inline_handlers})
    forms=soup.find_all('form')
    if forms: indicators.append({'code':'forms_present','severity':'low','count':len(forms)})
    embedded=sum(len(soup.find_all(t)) for t in ('iframe','embed','object'))
    if embedded: indicators.append({'code':'embedded_content','severity':'medium','count':embedded})
    meta_redirects=0; external_refs=0; dangerous=0; downloads=0
    for meta in soup.find_all('meta'):
        if str(meta.get('http-equiv','')).lower()=='refresh': meta_redirects+=1
    for tag in soup.find_all(True):
        for attr in URL_ATTRS:
            value=tag.get(attr)
            if not isinstance(value,str): continue
            v=value.strip().lower()
            if v.startswith(('http://','https://','//')): external_refs+=1
            if v.startswith(DANGEROUS_SCHEMES): dangerous+=1
            if any(v.split('?',1)[0].endswith(ext) for ext in EXECUTABLE_EXT): downloads+=1
    if meta_redirects: indicators.append({'code':'meta_redirect','severity':'medium','count':meta_redirects})
    if external_refs: indicators.append({'code':'external_resources','severity':'low','count':external_refs})
    if dangerous: indicators.append({'code':'dangerous_uri_scheme','severity':'high','count':dangerous})
    if downloads: indicators.append({'code':'executable_reference','severity':'high','count':downloads})
    encoded=len(re.findall(r'(?:atob\s*\(|fromCharCode|base64,|%[0-9a-fA-F]{2})', text))
    if encoded: indicators.append({'code':'encoded_or_obfuscated_content','severity':'medium','count':encoded})
    suspicious_dom=len(re.findall(r'(?:display\s*:\s*none|opacity\s*:\s*0|position\s*:\s*fixed)', text, re.I))
    if suspicious_dom: indicators.append({'code':'suspicious_dom_pattern','severity':'low','count':suspicious_dom})
    level='none'
    if any(i['severity']=='high' for i in indicators): level='high'
    elif any(i['severity']=='medium' for i in indicators): level='medium'
    elif indicators: level='low'
    return {'risk_level':level,'indicators':indicators,'summary':{'scripts':len(scripts),'forms':len(forms),'embedded_elements':embedded,'external_references':external_refs}}
