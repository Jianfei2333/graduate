import networkx as nx
import matplotlib.pyplot as plt
import random as rand
from functools import cmp_to_key

# 节点总数
num_of_nodes = 200
# 初始网络距离上限的比率
alpha = 0.1
# 节点失效的阈值
threshold = 1.0
# 子图
plotid = 121

#节点的四种状态
NORMAL = 0
OVERLOAD = 1
FAIL = 2
UNREACHABLE = 3

# Er = nx.random_graphs.watts_strogatz_graph(num_of_nodes, 3, 0.3)
# Er = nx.random_regular_graph(3, num_of_nodes)
Er = nx.random_graphs.barabasi_albert_graph(num_of_nodes, 4)
# Er = nx.read_adjlist("sample.adjlist")
# print(Er.nodes)
# 初始负载情况
loads = nx.betweenness_centrality(Er)
# 每个节点的额定负载
overload_threshold = {}
# 每个节点的超额负载积累量
overload_acc = {}
# 每个节点的相邻节点列表
neighbors = {}

def draw_graph(G):
  pos = nx.shell_layout(G)
  nodes_normal = []
  nodes_overload = []
  nodes_fail = []
  nodes_unreachable = []
  for key in G.nodes:
    if G.nodes[key]['status'] == NORMAL:
      nodes_normal.append(key)
    elif G.nodes[key]['status'] == OVERLOAD:
      nodes_overload.append(key)
    elif G.nodes[key]['status'] == FAIL:
      nodes_fail.append(key)
    else:
      nodes_unreachable.append(key)
  edges_fail = []
  edges_normal = []
  for e in G.edges:
    u = G.nodes[e[0]]['status']
    v = G.nodes[e[1]]['status']
    if u == FAIL or v == FAIL:
      edges_fail.append(e)
    else:
      edges_normal.append(e)
    
  # 各种状态节点print
  nx.draw_networkx_nodes(G, pos, nodelist=nodes_normal, node_color='g')
  nx.draw_networkx_nodes(G, pos, nodelist=nodes_overload, node_color='r')
  nx.draw_networkx_nodes(G, pos, nodelist=nodes_fail, node_color='k')
  nx.draw_networkx_nodes(G, pos, nodelist=nodes_unreachable, node_color='b')
  # 失效节点的边改为虚线
  nx.draw_networkx_edges(G, pos, edgelist=edges_normal)
  nx.draw_networkx_edges(G, pos, edgelist=edges_fail, style='dashed')
  nx.draw_networkx_labels(G, pos)
  plt.show()

def draw_graph_without_fail(G):
  Gt = G.copy()
  faillist = []
  for key in Gt.nodes:
    faillist.append(key)
  for val in faillist:
    Gt.remove_node(val)
  pos = nx.shell_layout(Gt)
  nx.draw_networkx_nodes(Gt, pos, node_color='g')
  nx.draw_networkx_edges(Gt, pos)
  nx.draw_networkx_labels(Gt, pos)
  plt.show()

def next_fail_node(G):
  Gt = G.copy()
  stable = True
  failnodes = []
  overloadnodes = []
  for key in Gt.nodes:
    if Gt.nodes[key]['status'] == FAIL:
      failnodes.append(key)
    elif Gt.nodes[key]['status'] == OVERLOAD:
      overloadnodes.append(key)
  # 清除临时图中失效节点
  for val in failnodes:
    Gt.remove_node(val)
  # 若无过载节点，则处于稳定状态
  if len(overloadnodes) == 0:
    return -1
  # 计算每个节点的
  load = nx.betweenness_centrality(Gt)
  # 计算节点过载比率
  overload = {}
  for key in load:
    overload[key] = load[key] - overload_threshold[key]
    # print(key)
    # print(overload_threshold[key])
    overload[key] = overload[key]/overload_threshold[key]
  # 计算每个节点的失效时间
  time_to_fail = {}
  for key in overload:
    if overload[key] <= 0:
      continue
    else:
      time_to_fail[key] = (threshold-overload_acc[key])/overload[key]
  # 计算下一个失效节点
  time_slice = float("Inf")
  nextfail = -1
  for key in time_to_fail:
    if time_slice > time_to_fail[key]:
      time_slice = time_to_fail[key]
      nextfail = key
  # 更新过载积累量
  for key in overload:
    t = overload_acc[key] + overload[key] * time_slice
    if t < 0:
      overload_acc[key] = 0
    else:
      overload_acc[key] = t
  
  return nextfail

def change_state(G):
  Gt = G.copy()
  failnodes = []
  for key in Gt.nodes:
    if Gt.nodes[key]['status'] == FAIL:
      failnodes.append(key)
  for key in failnodes:
    Gt.remove_node(key)
  load = nx.betweenness_centrality(Gt)
  for key in load:
    if load[key] > overload_threshold[key]:
      G.nodes[key]['status'] = OVERLOAD
    else:
      G.nodes[key]['status'] = NORMAL

def max_component(G):
  Gt = G.copy()
  faillist = []
  for key in Gt.nodes:
    if Gt.nodes[key]['status'] == FAIL:
      faillist.append(key)
  for val in faillist:
    Gt.remove_node(val);
  Gc = max(nx.connected_component_subgraphs(Gt), key=len)
  return len(Gc.nodes.keys())

def repair(G, nid1):
  # 将每个节点的累计超额负载归位
  for key in overload_acc:
    overload_acc[key] = 0
  # 修复节点
  G.nodes[nid1]['status'] = NORMAL
  # overload_threshold[nid] = overload_threshold[nid] * 1.1
  # 计算超压
  change_state(G)
  draw_graph(G)
  # 级联失效
  failnode = next_fail_node(G)
  while failnode != -1:
    G.node[failnode]['status'] = FAIL
    overload_acc[failnode] = 0
    change_state(Er)
    # draw_graph(Er)
    failnode = next_fail_node(Er)

def test_repariable(G):
  for i in range(0, num_of_nodes):
    print("Fail: ", i)
    Gt = G.copy()
    for k in range(0, num_of_nodes):
      overload_acc[k] = 0
    failnode = i
    while failnode != -1:
      Gt.nodes[failnode]['status'] = FAIL
      overload_acc[failnode] = 0
      change_state(Gt)
      failnode = next_fail_node(Gt)
    print("Max normal component: ", max_component(Gt))
    draw_graph(Gt)

def restore(G):
  print (1)
  for key in G.nodes:
    G.nodes[key]['status'] = NORMAL
  failnode = rand.randint(0, num_of_nodes - 1)
  print(2)
  while failnode != -1:
    G.nodes[failnode]['status'] = FAIL
    overload_acc[failnode] = 0
    change_state(G)
    failnode = next_fail_node(G)

def repairable(G, nid):
  Gt = G.copy()
  repair(Gt, nid)
  if Gt.nodes[nid]['status'] == FAIL:
    return False
  else:
    return True

# 初始化

for key in Er.nodes:
  Er.nodes[key]['status'] = NORMAL
  neighbors[key] = Er.adj[key]

for key in loads:
  overload_threshold[key] = loads[key]*(1+alpha)
  overload_acc[key] = 0

# 修匀，防止出现节点阈值为0的状况
totalloads = 0
for key in overload_threshold:
  totalloads += overload_threshold[key]

for key in overload_threshold:
  if overload_threshold[key] == 0:
    overload_threshold[key] = totalloads/num_of_nodes

draw_graph(Er)

# test_repariable(Er)

# 生成随机初始失效节点
#
failnode = rand.randint(0, num_of_nodes-1)

# 修改为初始失效最大负载的节点
# failnode = 0
# for key in loads:
#   if loads[key] > loads[failnode]:
#     falinode = key

while failnode != -1:
  Er.nodes[failnode]['status'] = FAIL
  overload_acc[failnode] = 0
  change_state(Er)
  failnode = next_fail_node(Er)

# nx.write_adjlist(Er, "sample.adjlist")

print ("Max component subgraph: ", max_component(Er))
draw_graph(Er)

faillist = []
for key in Er.nodes:
  if Er.nodes[key]['status'] == FAIL:
    faillist.append(key)

print("Total fails: ", len(faillist))
restore(Er)
draw_graph(Er)


# 随机选取修复点

# testcase = 0
# maxcomplist = {}
# for key in range(0, num_of_nodes+1):
#   maxcomplist[key] = 0
# while True:
#   faillist = []
#   for key in Er.nodes:
#     if Er.nodes[key]['status'] == FAIL:
#       faillist.append(key)
#   val = rand.randint(0, len(faillist)-1)
#   # print("repairing: ", faillist[val])
#   repair(Er, faillist[val])
#   count = 0
#   for key in Er.nodes:
#     if Er.nodes[key]['status'] == FAIL:
#       count = count + 1
#   testcase += 1
#   maxcomp = max_component(Er)
#   if maxcomplist[maxcomp] == 0:
#     maxcomplist[maxcomp] = testcase
#     print ("Found ", maxcomp, " component in testcase #", testcase)
#     draw_graph(Er)
#   if (count == 0):
#     break
#   draw_graph(Er)

# recover_list = []
# testcase = 0
# while True:
#   faillist = []
#   for key in Er.nodes:
#     if Er.nodes[key]['status'] == FAIL:
#       faillist.append(key)
#   if (len(faillist) == 0):
#     break
#   node_to_recover = faillist[0]
#   for key in range(1, len(faillist)):
#     if len(neighbors[faillist[key]]) > len(neighbors[node_to_recover]):
#       node_to_recover = faillist[key]
#   repair(Er, node_to_recover)
#   print ("Testcase ", testcase, ": ")
#   print ("Max Subgraph: ", max_component(Er))
#   draw_graph(Er)

draw_graph(Er)