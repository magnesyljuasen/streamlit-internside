from deta import Deta

deta = Deta("a0558p23_1qnSrugdeUhAokVe8AvE5w9HyNSnt6yx")

db = deta.Base("Bergvarmekalkulatoren")

def fetch_all_data():
    res = db.fetch()
    return res.items

def get_data(address):
    return db.get(address)



