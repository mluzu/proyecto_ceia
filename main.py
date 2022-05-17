from imagery import Collection
from imagery import bounds
import time


collection = Collection('Sentinel-2', 'S2MSI2A', 'Level-2A')
collection \
    .filter_bonds(bounds()) \
    .filter_cloudcoverage(0, 10) \
    .filter_date('NOW-20DAYS', 'NOW')\
    .filter_bands('B01', 'B02', 'B03')

start_time = time.time()
prod = collection.read()
print(prod)
print("--- %s seconds ---" % (time.time() - start_time))
