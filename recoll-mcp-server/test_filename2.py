import os
from recoll import recoll

os.environ['RECOLL_CONFDIR'] = os.path.expanduser('~/.recoll')
db = recoll.connect()

url = "file:///home/piotr/Documents/ksiazki/algorithms/[Marc_Moonen]_SVD_and_Signal_Processing_III_Algor(Bookos.org).pdf"

# Test 1: Query by url
query1 = db.query()
nres1 = query1.execute(f'url:"{url}"')
print("URL search nres:", nres1)

# Test 2: Query by dir and filename
filepath = url[7:]
basename = os.path.basename(filepath)
dirname = os.path.dirname(filepath)
query2 = db.query()
# dir needs to be just the path, filename the basename
nres2 = query2.execute(f'dir:"{dirname}" filename:"{basename}"')
print("Dir+Filename search nres:", nres2)

