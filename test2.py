import sys
import os
from typing import TypeVar
import numpy as np
import sexpdata
import subprocess
import math
import time
import matplotlib.pyplot as plt
import itertools

sys.path.append(os.path.dirname(os.path.abspath(__file__)) +
                "/PathPlanning/Search_based_Planning/")

from Search_2D import plotting, env, Astar

def me_call_emacsltl(arg1, arg2):
    arg1 = sexpdata.dumps(arg1)
    arg2 = sexpdata.dumps(arg2)
    ltl_result = subprocess.run(
        ['emacs', '--batch',
         '-l', 'ltl.el', '--eval',
         f'(ltl-doit {arg1} {arg2})'],
        capture_output=True,
        text=True)
    # print(ltl_result.stdout)
    return sexpdata.loads(ltl_result.stdout)

Q = sexpdata.Quoted
S = sexpdata.Symbol

def me_distance(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return distance

class yy_Plotting(plotting.Plotting):
    def __init__(self, xI, xG, env):
        self.xI, self.xG = xI, xG
        self.env = env
        self.obs = self.env.obs
    def anime(self, path):
        self.plot_grid('test')
        plt.pause(0.1)
        self.plot_path(path)
        # plt.show(block=False)
    def plot_grid(self, name):
        obs_x = [x[0] for x in self.obs]
        obs_y = [x[1] for x in self.obs]

        plt.plot(self.xI[0], self.xI[1], "bs")
        plt.plot(self.xG[0], self.xG[1], "gs")
        plt.plot(obs_x, obs_y, "sk")
        plt.title(name)
        plt.axis("equal")

        # display task area in yellow color
        for task in self.env.tasks:
            name = task[0]
            point = task[1]
            plt.plot(point[0], point[1], 'ys')
            plt.annotate(name, point,
                         textcoords="offset points",
                         xytext=(-3, 5), ha='center', color='purple')

class yy_env(env.Env):
    def __init__(self, s_start, init_tasks):
        self.x_range = 51  # size of background
        self.y_range = 31
        self.motions = [(-1, 0), (-1, 1), (0, 1), (1, 1),
                        (1, 0), (1, -1), (0, -1), (-1, -1)]
        # [name, (x, y)]
        self.tasks = []
        self.taskset = set()
        for ta in init_tasks:
            self.add_task(ta[0], ta[1])
        self.start = s_start
        self.obs = self.obs_map()

    # no use
    def add_task(self, name, point):
        self.tasks.append([name, point])
        self.taskset.add(point)
    def task_point(self, name):
        condition = lambda x: x == name
        result = [item for item in self.tasks if condition(item[0])]
        if len(result) == 0:
            raise ValueError('task area not found')
        return result[0][1]

    def simple_distance(self):
        me_array = self.tasks + [['0', self.start]]
        dists = []
        for a, b in itertools.combinations(me_array, 2):
            tmp = [a[0], b[0], me_distance(a[1], b[1])]
            dists.append(tmp)
        return dists
    def conv_distance1(self, step_length, obs_value):
        me_array = self.tasks + [['0', self.start]]
        dists = []
        for a, b in itertools.combinations(me_array, 2):
            name1, name2 = a[0], b[0]
            point1, point2 = a[1], b[1]
            # calculate cost
            p12_dist = me_distance(point1, point2)
            cost = 0.0# p12_dist
            steps = int(p12_dist // step_length)
            dx = point2[0] - point1[0]
            dy = point2[1] - point1[1]
            for i in range(steps + 1):
                t = i / steps
                x = round(point1[0] + t * dx)
                y = round(point1[1] + t * dy)
                if (x, y) in self.obs:
                    cost = cost + obs_value
                else:
                    cost = cost + 1.0

            dists.append([name1, name2, cost])
        return dists

    def obs_map(self):
        x = self.x_range
        y = self.y_range
        obs = set()

        for i in range(x):
            obs.add((i, 0))
        for i in range(x):
            obs.add((i, y - 1))

        for i in range(y):
            obs.add((0, i))
        for i in range(y):
            obs.add((x - 1, i))

        # np method
        len = (x - 2) * (y - 2)
        obstacle_positions = np.random.choice(
            len, size=450, replace=False)
        for pos in obstacle_positions:
            row = pos // (y - 2)
            col = pos % (y - 2)
            ob = (row + 1, col + 1)
            if ob not in self.taskset and ob != self.start:
                obs.add(ob)

        return obs

class yy_AStar(Astar.AStar):
    def __init__(self, s_start, s_goal, env, heuristic_type):
        self.s_start = s_start
        self.s_goal = s_goal
        self.heuristic_type = heuristic_type

        self.Env = env  # class Env

        self.u_set = self.Env.motions  # feasible input set
        self.obs = self.Env.obs  # position of obstacles

        self.OPEN = []  # priority queue / OPEN set
        self.CLOSED = []  # CLOSED set / VISITED order
        self.PARENT = dict()  # recorded parent
        self.g = dict()  # cost to come

def main():
    use_plot = True
    s_start = (5, 5)
    times = []
    count = 0
    NN = 1000
    while (count < NN):
        test_env = yy_env(s_start,
                          [['a1', (10, 20)],
                           ['a2', (20, 27)],
                           ['a3', (30, 10)],
                           ['a4', (40, 25)],
                           ['a5', (45, 5)]])

        a1 = Q([S('and'),
                [S('F'), S(':a1')],
                [S('F'), S(':a2')], [S('F'), S(':a3')],
                [S('F'), S(':a4')], [S('F'), S(':a5')]])
        # a2 = Q(test_env.simple_distance())
        a2 = Q(test_env.conv_distance1(1.5, 1.5))
        res = me_call_emacsltl(a1, a2)
        my_list = res[0]
        my_point = [s_start] + list(map(lambda x: test_env.task_point(x), my_list))
        pairs = list(zip(my_point, my_point[1:]))

        # print the test result
        # JUST ONCE
        try:
            for p in pairs:
                l_start = p[0]
                l_target = p[1]
                astar = yy_AStar(l_start, l_target, test_env, "euclidean")
                # astar = yy_AStar(l_start, l_target, test_env, "manhattan")
                l_plot = yy_Plotting(l_start, l_target, test_env)
                path, visited = astar.searching()
                if use_plot == True:
                    l_plot.anime(path)
        except KeyError:
            continue
        if use_plot == True:
            plt.annotate('start', my_point[0],
                         textcoords="offset points",
                         xytext=(5, -12), ha='center', color='green')
            plt.annotate('end', my_point[-1],
                         textcoords="offset points",
                         xytext=(5, -12), ha='center', color='green')
            plt.show()

        # repeat test time
        N = 10
        total_time = 0.0
        for i in range(0, N):
            me_time = 0.0
            for p in pairs:
                l_start = p[0]
                l_target = p[1]
                astar = yy_AStar(l_start, l_target, test_env, "euclidean")
                # astar = yy_AStar(l_start, l_target, test_env, "manhattan")
                st = time.time()
                path, visited = astar.searching()
                ed = time.time()
                me_time = me_time + ed - st
            total_time = total_time + me_time
        print(f'{count}: {total_time}, {total_time / N}')
        times.append(total_time / N)
        count = count + 1
    print(times)
    print(sum(times) / NN)
if __name__ == '__main__':
    a = time.time()
    main()
    print(f'cost: {time.time() - a}')
