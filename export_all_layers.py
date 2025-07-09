# export_all_layers.py

import os
import pandas as pd
import inspect
from datetime import date

# -------------- IMPORT YOUR UPDATED LAYER FUNCTIONS ------------
# Each layerX function should itself:
#  1) Do an incremental, parallelized fetch.
#  2) NOT re-download all historic data every run.
#  3) Return a DataFrame quickly if nothing new is needed.
from layerone      import fetch_layer_one      as fetch_layerone
from layertwo      import fetch_layer_two      as fetch_layertwo
from layerthreeA   import fetch_layer_threeA   as fetch_layerthreeA
from layerfour     import fetch_layer_four     as fetch_layerfour
from layerfive     import fetch_layer_five     as fetch_layerfive
from layersix      import fetch_layer_six      as fetch_layersix
from layerseven    import fetch_layer_seven    as fetch_layerseven
from layereight    import fetch_layer_eight    as fetch_layereight
from layerten      import fetch_layer_ten      as fetch_layerten
from layereleven   import fetch_layer_eleven   as fetch_layereleven
from layer12       import fetch_layer_twelve   as fetch_layertwelve
from layer13       import fetch_layer_thirteen as fetch_layerthirteen


def load_or_fetch(layer_name, fetch_fn, date_str, checkpoint_dir="checkpoints"):
    """
    1. If a parquet checkpoint exists for this layer+date, load and return it.
    2. Otherwise, call fetch_fn appropriately:
       - If fetch_fn accepts one parameter, call fetch_fn(date_str).
       - If fetch_fn accepts zero parameters, call fetch_fn().
       Save the resulting DataFrame to parquet and return it.
    """
    os.makedirs(checkpoint_dir, exist_ok=True)
    filepath = os.path.join(checkpoint_dir, f"{layer_name}_{date_str}.parquet")

    # If checkpoint exists, load it immediately
    if os.path.exists(filepath):
        print(f"🔄 Loading {layer_name} from {filepath}")
        return pd.read_parquet(filepath)

    # Determine how many parameters fetch_fn expects
    sig = inspect.signature(fetch_fn)
    param_count = len(sig.parameters)

    print(f"▶️  Running {layer_name} (no checksum found)…")
    if param_count == 1:
        df = fetch_fn(date_str)
    else:
        df = fetch_fn()

    # Attempt to write checkpoint
    try:
        df.to_parquet(filepath, index=False)
        print(f"✅ Checkpointed {layer_name} → {filepath}")
    except Exception as e:
        print(f"⚠️  Could not write checkpoint for {layer_name}: {e}")

    return df


def main():
    today_str = date.today().strftime("%Y-%m-%d")

    # 1) Fetch each layer—but load from disk if checkpoint already exists
    df1  = load_or_fetch("layerone",     fetch_layerone,     today_str)
    df2  = load_or_fetch("layertwo",     fetch_layertwo,     today_str)
    df3  = load_or_fetch("layerthreeA",  fetch_layerthreeA,  today_str)
    df4  = load_or_fetch("layerfour",    fetch_layerfour,    today_str)
    df5  = load_or_fetch("layerfive",    fetch_layerfive,    today_str)
    df6  = load_or_fetch("layersix",     fetch_layersix,     today_str)
    df7  = load_or_fetch("layerseven",   fetch_layerseven,   today_str)
    df8  = load_or_fetch("layereight",   fetch_layereight,   today_str)
    df10 = load_or_fetch("layerten",     fetch_layerten,     today_str)
    df11 = load_or_fetch("layereleven",  fetch_layereleven,  today_str)
    df12 = load_or_fetch("layer12",      fetch_layertwelve,  today_str)
    df13 = load_or_fetch("layer13",      fetch_layerthirteen, today_str)

    # 2) Gather them all into a dict for writing
    all_dfs = {
        "layerone":     df1,
        "layertwo":     df2,
        "layerthreeA":  df3,
        "layerfour":    df4,
        "layerfive":    df5,
        "layersix":     df6,
        "layerseven":   df7,
        "layereight":   df8,
        "layerten":     df10,
        "layereleven":  df11,
        "layer12":      df12,
        "layer13":      df13,
    }

    # 3) Write them all into an Excel file—just once, at the end
    output_file = f"all_layers_{today_str}.xlsx"
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        for layer_name, df in all_dfs.items():
            if not df.empty:
                df.to_excel(writer, sheet_name=layer_name, index=False)
            else:
                # create a one-row sheet if no data
                pd.DataFrame({"Message": [f"No data for {layer_name}"]}) \
                  .to_excel(writer, sheet_name=layer_name, index=False)

    print(f"🏁 Done. Exported all layers to {output_file}")


if __name__ == "__main__":
    main()
