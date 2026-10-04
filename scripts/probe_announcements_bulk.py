"""Approved five-request, one-week read-only NSE parity probe; never ingestion."""
import json
from pathlib import Path
import sys
import time
import requests
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.ingestion.nse_market_data.announcements import build_announcement_rows

START,END='07-09-2026','13-09-2026'
SYMBOLS=('RELIANCE','TCS','KOTAKBANK')

def canonical_rows(symbol,raw):
    rows=build_announcement_rows(symbol,raw,'parity_probe')
    return {json.dumps({k:v for k,v in r.items() if k!='source_file'},sort_keys=True) for r in rows}

def compare(bulk,per_symbol):
    output={}
    for symbol,rows in per_symbol.items():
        a=canonical_rows(symbol,[r for r in bulk if r.get('symbol')==symbol])
        b=canonical_rows(symbol,rows)
        output[symbol]=dict(bulk=len(a),per_symbol=len(b),only_bulk=len(a-b),only_per_symbol=len(b-a),equal=a==b)
    return output

def main():
    out=ROOT/'data/processed/announcements_bulk_probe_20260907_13'
    out.mkdir(exist_ok=True)
    session=requests.Session()
    session.headers.update({'User-Agent':'Mozilla/5.0','Accept':'application/json'})
    trace=[]
    def get(label,url,params=None):
        if len(trace)>=5:
            raise RuntimeError('Approved request budget exhausted')
        item=dict(label=label,params=params);trace.append(item);started=time.monotonic()
        try:
            response=session.get(url,params=params,timeout=25,allow_redirects=False)
            item.update(status=response.status_code,seconds=round(time.monotonic()-started,3))
            (out/(label+'.response')).write_bytes(response.content)
            if response.status_code!=200:
                raise RuntimeError('Non-200 response')
            return response
        except Exception as exc:
            item['error_type']=type(exc).__name__
            raise
    report=dict(week=['2026-09-07','2026-09-13'],requests=trace,status='INCOMPLETE')
    try:
        get('cookie','https://www.nseindia.com')
        params=dict(index='equities',from_date=START,to_date=END)
        bulk=get('bulk','https://www.nseindia.com/api/corporate-announcements',params).json()
        if not isinstance(bulk,list):
            raise ValueError('Bulk payload is not a list')
        if any(not r.get('symbol') or not r.get('seq_id') or not '2026-09-07'<=str(r.get('sort_date',''))[:10]<='2026-09-13' for r in bulk):
            raise ValueError('Missing identity or out-of-week bulk row')
        per={symbol:get(symbol,'https://www.nseindia.com/api/corporate-announcements',params|dict(symbol=symbol)).json() for symbol in SYMBOLS}
        if any(not isinstance(rows,list) for rows in per.values()):
            raise ValueError('Per-symbol payload is not a list')
        report.update(status='COMPLETE',bulk_rows=len(bulk),bulk_symbols=len({r['symbol'] for r in bulk}),parity=compare(bulk,per))
        (out/'payloads.json').write_text(json.dumps(dict(bulk=bulk,per_symbol=per)),encoding='utf-8')
    except Exception as exc:
        report['failure_type']=type(exc).__name__
    finally:
        session.close()
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    return 0 if report['status']=='COMPLETE' else 1
if __name__=='__main__':
    sys.exit(main())
