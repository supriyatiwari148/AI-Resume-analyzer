from sqlalchemy import inspect
from db import engine, Base
import models


print("Creating database tables...")

Base.metadata.create_all(bind=engine)

print("Tables created successfully")


inspector = inspect(engine)

tables = inspector.get_table_names()

print("Current Database Tables:")
print(tables)