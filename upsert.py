# db/upsert.py

import pandas as pd
from sqlalchemy import MetaData, Table, inspect, and_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from db.session import engine

metadata = MetaData()

def upsert_df(
    df: pd.DataFrame,
    table_name: str,
    index_cols: list,
    schema: str = None
) -> None:
    """
    Upsert a DataFrame into a table.  
    On SQLite: deletes+inserts.  
    On Postgres: uses ON CONFLICT DO UPDATE.
    """
    inspector = inspect(engine)

    if not inspector.has_table(table_name, schema=schema):
        df.head(0).to_sql(table_name, engine, index=False, schema=schema)
        print(f"🆕 Created table '{table_name}'")

    tbl = Table(table_name, metadata, autoload_with=engine, schema=schema)
    records = df.to_dict(orient="records")

    if engine.dialect.name == "sqlite":
        with Session(engine) as session:
            for rec in records:
                cond = [tbl.c[col] == rec[col] for col in index_cols]
                session.execute(tbl.delete().where(and_(*cond)))
            session.execute(tbl.insert().values(records))
            session.commit()
        return

    stmt = insert(tbl).values(records)
    update_cols = {
        col.name: col
        for col in stmt.excluded
        if col.name not in index_cols
    }
    stmt = stmt.on_conflict_do_update(
        index_elements=index_cols,
        set_=update_cols
    )
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()
