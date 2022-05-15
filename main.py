from imagery import Collection
from imagery import bounds


collection = Collection('Sentinel-2', 'S2MSI2A', 'Level-2A')
collection \
    .filter_bonds(bounds()) \
    .filter_cloudcoverage(0, 10) \
    .filter_date('NOW-20DAYS', 'NOW')

prod = collection.read(1)
print(prod)
