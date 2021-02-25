import pandas as pd

df = pd.DataFrame(columns=['Item','quantity','Time'])
counter = 0
print(df.head())

new = [["apple",2000.0,"13:24"]]

df = pd.DataFrame(new,index=[0],columns=['Item','quantity','Time'])
df = pd.DataFrame(new,index=[1],columns=['Item','quantity','Time'])
print(df.head())