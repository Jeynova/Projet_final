[tags: sqlalchemy, models]
- Declarative Base: `from sqlalchemy.orm import declarative_base`
- Types: Integer, String(255), Float, Boolean, DateTime
- Id PK: `id = Column(Integer, primary_key=True, index=True)`
- Unique: `unique=True`
- Nullable par défaut True sauf PK
