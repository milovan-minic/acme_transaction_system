import os
 
def pytest_sessionstart(session):
    db_path = "./test.db"
    if os.path.exists(db_path):
        os.remove(db_path) 