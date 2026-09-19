from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base , sessionmaker

DATABASE_URL = "mysql+pymysql://g8m76zmm3kxVjGG.root:NwGF9arG7VhWBegk@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/test"


engine = create_engine(
  DATABASE_URL,
  pool_pre_ping=True,
  connect_args={
    "ssl":{
      "ca":r"C:/Users/riyas/Desktop/AI/ca.pem"
    }
  }
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

