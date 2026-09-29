import glob
 
# list all csv files only
csv_files = glob.glob('*.{}'.format('csv'))
print(csv_files)


import pandas as pd
 
 
df_csv_concat = pd.concat([pd.read_csv(file) for file in csv_files ], ignore_index=True)
df_csv_concat
