# db/create_tables.py

from datetime import datetime
import pandas as pd
from sqlalchemy import inspect
from db.session import engine

from baseball_data.layerone      import fetch_layer_one
from baseball_data.layertwo      import fetch_layer_two
from baseball_data.layerthreeA   import fetch_layer_threeA
from baseball_data.layerfour     import fetch_layer_four
from baseball_data.layerfive     import fetch_layer_five
from baseball_data.layersix      import fetch_layer_six
from baseball_data.layerseven    import fetch_layer_seven
from baseball_data.layereight    import fetch_layer_eight
from baseball_data.layerten      import fetch_layer_ten
from baseball_data.layereleven   import fetch_layer_eleven
from baseball_data.layer12       import fetch_layer_twelve
from baseball_data.layer13       import fetch_layer_thirteen

# Use today's date for layers that accept a date argument
today = datetime.today().strftime('%Y-%m-%d')

layers = {
    "layer_one":    (fetch_layer_one,      (today,)),
    "layer_two":    (fetch_layer_two,      ()),
    "layer_threeA": (fetch_layer_threeA,   ()),
    "layer_four":   (fetch_layer_four,     ()),
    "layer_five":   (fetch_layer_five,     ()),
    "layer_six":    (fetch_layer_six,      ()),
    "layer_seven":  (fetch_layer_seven,    ()),
    "layer_eight":  (fetch_layer_eight,    ()),
    "layer_ten":    (fetch_layer_ten,      ()),
    "layer_eleven": (fetch_layer_eleven,   ()),
    "layer_12":     (fetch_layer_twelve,   ()),
    "layer_13":     (fetch_layer_thirteen, ())
}

inspector = inspect(engine)

for table_name, (func, args) in layers.items():
    # skip if table already exists
    if inspector.has_table(table_name):
        print(f"⏭ Skipping existing table '{table_name}'")
        continue

    df = func(*args)
    # create table schema only (no rows) if it doesn't exist
    df.head(0).to_sql(table_name, engine, index=False)
    print(f"✅ Created table '{table_name}' with columns: {list(df.columns)}")
