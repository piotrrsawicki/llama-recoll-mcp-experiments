import os
from recoll import recoll

os.environ['RECOLL_CONFDIR'] = os.path.expanduser('~/.recoll')
db = recoll.connect()
query = db.query()
query.execute("SVD_and_Signal_Processing")
for i in range(query.rowcount):
    doc = query.fetchone()
    print("filename:", doc.filename)
    print("url:", doc.url)
    break
