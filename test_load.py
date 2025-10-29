from etl.load_dimensions import DimensionLoader

print("Starting dimension load...")
loader = DimensionLoader()
loader.load_all_dimensions()