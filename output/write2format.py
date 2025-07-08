import pandas as pd
df = pd.read_excel("distance_matrix.xlsx")
df2 = pd.read_excel("location_中百仓储_武汉市.xlsx")

txt = [[0, 23, 47, 32, 0], [0, 33, 52, 50, 20, 0], [0, 63, 29, 55, 16, 0], [0, 45, 27, 64, 0], [0, 48, 2, 11, 0], [0, 28, 54, 60, 9, 0], [0, 35, 21, 41, 38, 0], [0, 3, 61, 43, 36, 0], [0, 17, 18, 5, 40, 0], [0, 25, 66, 39, 37, 0], [0, 8, 30, 4, 56, 0], [0, 46, 59, 53, 0], [0, 15, 57, 24, 6, 0], [0, 44, 62, 34, 0], [0, 22, 1, 58, 0], [0, 26, 14, 13, 0], [0, 49, 42, 19, 10, 0], [0, 65, 7, 31, 12, 0], [0, 51, 0]]
"""
ACO最短距离： 1222.3558947426202
ACO最短路径： [[0, 63, 33, 56, 46, 0], [0, 62, 59, 51, 0], [0, 3, 61, 53, 4, 0], [0, 28, 57, 35, 25, 0], [0, 45, 11, 38, 27, 0], [0, 15, 20, 10, 37, 0], [0, 58, 40, 44, 12, 0], [0, 17, 48, 5, 2, 0], [0, 31, 23, 26, 0], [0, 19, 22, 30, 42, 0], [0, 24, 16, 64, 7, 0], [0, 52, 65, 60, 0], [0, 32, 54, 43, 0], [0, 39, 50, 66, 21, 0], [0, 9, 6, 41, 49, 0], [0, 55, 47, 14, 29, 0], [0, 18, 13, 1, 0], [0, 36, 34, 8, 0]]
ACO运行时间： 592.6582541465759
ACO-IC最短距离： 1209.3242567649604
ACO-IC最短路径： [[0, 63, 33, 46, 56, 0], [0, 62, 59, 51, 0], [0, 3, 61, 53, 4, 0], [0, 28, 57, 25, 35, 0], [0, 45, 11, 38, 27, 0], [0, 15, 10, 37, 20, 0], [0, 44, 40, 58, 12, 0], [0, 17, 48, 5, 2, 0], [0, 31, 23, 26, 0], [0, 30, 19, 22, 42, 0], [0, 16, 24, 64, 7, 0], [0, 52, 60, 65, 0], [0, 32, 54, 43, 0], [0, 39, 50, 66, 21, 0], [0, 9, 6, 41, 49, 0], [0, 55, 47, 14, 29, 0], [0, 18, 13, 1, 0], [0, 36, 8, 34, 0]]
"""

"""for i in txt2:
  if i == 0 and i != txt2[-1]:
    txt[-1].append(0)
    txt.append([0])
  else:
    txt[-1].append(i)"""
route_list = []
distance_list = []
cargo_list = []

for i in txt:
  child_route = ""
  child_distance = 0
  child_cargo = 0
  for j, k in enumerate(i):
    if j != len(i) - 1:
      child_route += str(k) + "->"
      print(str(k)+"-"+str(i[j+1])+":"+str(df.iloc[k, i[j+1]]))
      child_distance += df.iloc[k, i[j+1]+1]
    else:
      child_route += str(k)
    # print(k,df2["demand"][k],sep=": ")
    child_cargo += df2["demand"][k]

  route_list.append(child_route)
  distance_list.append(child_distance)
  cargo_list.append(child_cargo)

#print(route_list,end="\n\n")
#print(distance_list,end="\n\n")
#print(cargo_list)

df3 = pd.DataFrame({"route":route_list,"distance":distance_list,"cargo":cargo_list})
df3.to_excel("route-aco.xlsx")

sum_distance = 0
for i in distance_list:
  sum_distance += i
print(sum_distance)