import pandas as pd

# Create Example data with types
df = pd.DataFrame({
    'words': ['foo', 'bar', 'spam', 'eggs'],
    'nums': [1, 2, 3, 4]
}).astype(dtype={
    'words': 'object',
    'nums': 'int8'
})