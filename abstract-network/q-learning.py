# import graphlib

import networkx as nx
import matplotlib.pyplot as plt
import random as rand
from functools import cmp_to_key

# 衰减
gamma = 0.9
# 学习率
alpha = 0.8
# e-greedy
e = 0.8
# 时间折扣
time_discount = 0.7

# 节点总数
num_of_nodes = 30
# 初始网络距离上限的比率
alpha_cap = 0.1
# 节点失效的阈值
threshold = 1.0

#节点的四种状态
NORMAL = 0
OVERLOAD = 1
FAIL = 2
UNREACHABLE = 3

q_table = {}

data = open("e8td2.data", "w")

# Er = nx.random_graphs.watts_strogatz_graph(num_of_nodes, 3, 0.3)
# Er = nx.random_regular_graph(3, num_of_nodes)
# Er = nx.random_graphs.barabasi_albert_graph(num_of_nodes, 4)
Er = nx.read_adjlist("sample.adjlist", nodetype=int)
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
  # print(load)
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
  # draw_graph(G)
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

def restore(G, faillist):
  for key in G.nodes:
    G.nodes[key]['status'] = NORMAL
  for val in faillist:
    G.nodes[val]['status'] = FAIL

def repairable(G, nid):
  Gt = G.copy()
  Gt.nodes[nid]['status'] = NORMAL
  current_load = nx.betweenness_centrality(Gt)
  if current_load[nid] > overload_threshold[nid]:
    return False
  else:
    return True


def finish(G):
  for key in G.nodes:
    if G.nodes[key]['status'] == FAIL:
      return False
  return True

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

# draw_graph(Er)

# test_repariable(Er)

# 生成随机初始失效节点
#
# failnode = rand.randint(0, num_of_nodes-1)

# 修改为初始失效最大负载的节点
failnode = 0
for key in loads:
  if loads[key] > loads[failnode]:
    failnode = key

while failnode != -1:
  Er.nodes[failnode]['status'] = FAIL
  overload_acc[failnode] = 0
  change_state(Er)
  failnode = next_fail_node(Er)

print ("Max component subgraph: ", max_component(Er))
# draw_graph(Er)

global_faillist = []
for key in Er.nodes:
  if Er.nodes[key]['status'] == FAIL:
    global_faillist.append(key)

print("Total fails: ", len(global_faillist))



def compute_reward(G, nid):
  Gt = G.copy()
  repair(Gt, nid)
  max_subgraph_before = max_component(G)
  max_subgraph_after = max_component(Gt)
  return max_subgraph_after - max_subgraph_before

def build_q_entry(G):
  faillist = []
  for key in G.nodes:
    if G.nodes[key]['status'] == FAIL and repairable(G, key):
      faillist.append(key)
  entry = {}
  for val in faillist:
    entry[val] = 0
  key = hash(str(list(G.nodes(data='status'))))
  q_table[key] = entry
  return entry

def update_q_value(G, action, select_time):
  reward = compute_reward(G, action)
  current_state_index = hash(str(list(G.nodes(data='status'))))
  repair(G, action)
  next_state_index = hash(str(list(G.nodes(data='status'))))
  max_next_q = 0
  if q_table.__contains__(next_state_index):
    maxkey = 0
    if len(q_table[next_state_index]) != 0:
      maxkey = findmax(q_table[next_state_index])
      max_next_q = q_table[next_state_index][maxkey]
    else:
      max_next_q = 100
  else:
    build_q_entry(G)
  # print(q_table)
  # print(current_state_index)
  # print(action)
  q = q_table[current_state_index][action]
  q_table[current_state_index][action] = (1-alpha)*q + alpha*(reward-time_discount*select_time+gamma*max_next_q)


def findmax(actions):
  # print(list(actions.keys()))
  res = list(actions.keys())[0]
  for key in actions:
    if actions[key] > actions[res]:
      res = key
  return res

def train_one_episode(G, select_time):
  index_in_q_table = hash(str(list(G.nodes(data='status'))))
  if q_table.__contains__(index_in_q_table):
    actions = q_table[index_in_q_table]
    key = 0
    if len(actions) != 0:
      key = findmax(actions)
    if rand.random() >= e:
      key = rand.randint(0, len(actions)-1)
      key = list(actions.keys())[key]
    update_q_value(G, key, select_time)
  else:
    actions = build_q_entry(G)
    key = rand.randint(0, len(actions)-1)
    key = list(actions.keys())[key]
    
    update_q_value(G, key, select_time)

def run_validation(G):
  Gt = G.copy()
  restore(Gt, global_faillist)
  repair_list=[]
  max_subplot_list=[]
  for _ in range(50):
    index = hash(str(list(Gt.nodes(data='status'))))
    if q_table.__contains__(index):
      if len(q_table[index]) != 0:
        key = findmax(q_table[index])
      else:
        print("Repair finished")
        break
      # if rand.random() >= e:
      #   randkey = rand.randint(0, len(q_table[index])-1)
      #   randkey = list(q_table[index])[randkey]
      #   key = randkey
      print("Repairing node #", _, ": ", key)
      repair_list.append(key)
      repair(Gt, key)
      max_subplot = max_component(Gt)
      print("Max subplot: ", max_subplot)
      max_subplot_list.append(max_subplot)
    else:
      print("No entry found")
      actions = build_q_entry(Gt)
      if len(actions) != 0:
        key = rand.randint(0, len(actions)-1)
        key = list(actions.keys())[key]
      else:
        print("Repair finished")
        break;
      print("random Repairing node #", _, ": ", key)
      repair_list.append(key)
      repair(Gt, key)
      max_subplot = max_component(Gt)
      print("random Max subplot: ", max_subplot)
      max_subplot_list.append(max_subplot)
  print (repair_list)
  print (max_subplot_list)
  data.write("repair_list:\n")
  data.write(str(repair_list))
  data.write("max_subplot_list:\n")
  data.write(str(max_subplot_list))
  data.write("\n")
  # print("Wait for continue.")
  # input()

def main():
  # Er, overload_threshold, overload_acc, neighbors = init_graph()
  testcase = 0
  select_time = 0
  while True:
    print("Train episode #", testcase)
    testcase += 1
    train_one_episode(Er, select_time)
    select_time += 1
    if finish(Er):
      print("Finish one train, restore the network")
      restore(Er, global_faillist)
      select_time = 0
      continue
    if testcase % 100 == 0:
      print("Running validation after #", testcase, "trains:")
      # print (q_table)
      data.write("After " + str(testcase) + " of trains")
      run_validation(Er)
      # restore(Er, global_faillist)
      if testcase % 1000 == 0:
        # print("Waiting for command to quit.")
        # input()
        break

main()