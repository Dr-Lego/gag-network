import pandas as pd

# Create a sample DataFrame
data = {'i': [0, 1, 2, 3], 'a': [1, 45, 5, 6], 'b': [2, 6, 9, 9], 'c': [3, 8, 3, 34]}
df = pd.DataFrame(data)

# Convert the DataFrame to a dictionary
result_dict = df.set_index('i').to_dict('index')

print(result_dict)