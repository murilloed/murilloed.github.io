"""Build a small attributed UCI/MnDOT sample; no private operational data."""
import csv
import gzip
import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path

URL='https://archive.ics.uci.edu/static/public/492/metro+interstate+traffic+volume.zip'
def fetch(folder=None):
    folder=Path(folder or Path(__file__).parent)
    with urllib.request.urlopen(URL,timeout=60) as response:payload=response.read()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        member=next(n for n in archive.namelist() if n.endswith('.csv.gz'))
        raw=gzip.decompress(archive.read(member)).decode('utf-8-sig')
    rows=list(csv.DictReader(io.StringIO(raw)));unique={}
    for row in rows:unique.setdefault(row['date_time'],int(row['traffic_volume']))
    sample=sorted(unique.items())[-2016:]
    with (folder/'observed.csv').open('w',newline='',encoding='utf-8') as handle:
        writer=csv.writer(handle);writer.writerow(['timestamp','volume']);writer.writerows(sample)
    provenance={'citation':'Hogue, J. (2019). Metro Interstate Traffic Volume. UCI Machine Learning Repository. DOI:10.24432/C5X60B','url':URL,'license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/','station':'MnDOT ATR 301, westbound I-94, Minneapolis–St Paul','time_basis':'local CST timestamps as supplied; no timezone conversion','upstream_zip_sha256':hashlib.sha256(payload).hexdigest(),'upstream_rows':len(rows),'unique_timestamps':len(unique),'sample_rows':len(sample),'sample_start':sample[0][0],'sample_end':sample[-1][0],'transformations':'Keep first row per timestamp (weather duplicates), retain timestamp and traffic_volume, sort, select last 2016 available records. No missing hours imputed.'}
    (folder/'DATA_SOURCE.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    print(json.dumps(provenance,indent=2))
if __name__=='__main__':fetch()
