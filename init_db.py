from bdi_api.settings import engine
from bdi_api.s7.api import Base

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
