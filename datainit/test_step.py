import plcApi
import ipdb

data = plcApi.get_hoist_position(list(range(0, 30)))
print(data)
data = plcApi.get_bar_position(list(range(0, 40)))
print(data)