import sys
import os

import sexpdata
import subprocess
import math
import time
import matplotlib.pyplot as plt
import itertools
import numpy as np
import random

sys.path.append(os.path.dirname(os.path.abspath(__file__)) +
                "/PathPlanning/Search_based_Planning/")

from Search_2D import plotting, env, Astar

class yy_Plotting(plotting.Plotting):
    def __init__(self, xI, xG, env):
        self.xI, self.xG = xI, xG
        self.env = env
        self.obs = self.env.obs_map()
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
                         xytext=(-3, 5), ha='center')


class yy_env(env.Env):
    def __init__(self, init_tasks):
        self.x_range = 51  # size of background
        self.y_range = 31
        self.motions = [(-1, 0), (-1, 1), (0, 1), (1, 1),
                        (1, 0), (1, -1), (0, -1), (-1, -1)]
        # [name, (x, y)]
        self.tasks = []
        self.taskset = set()
        for ta in init_tasks:
            self.add_task(ta[0], ta[1])
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

    def simple_distance(self, point):
        me_array = self.tasks + [['0', point]]
        dists = []
        for a, b in itertools.combinations(me_array, 2):
            tmp = [a[0], b[0], me_distance(a[1], b[1])]
            dists.append(tmp)
        return dists

    def obs_map(self):
        x = self.x_range
        y = self.y_range
        obs = set()

        # down
        for i in range(x):
            obs.add((i, 0))
        # up
        for i in range(x):
            obs.add((i, y - 1))
        # left
        for i in range(y):
            obs.add((0, i))
        # right
        for i in range(y):
            obs.add((x - 1, i))

        # np method
        len = (x - 2) * (y - 2)
        obstacle_positions = np.random.choice(
            len, size=150, replace=False)
        for pos in obstacle_positions:
            row = pos // (y - 2)
            col = pos % (y - 2)
            obs.add((row + 1, col + 1))
        return obs

# print(np.random.choice([0, 1], size=10, p=[0.7, 0.3]))

e = yy_env()
p = yy_Plotting((5, 5), (45, 25), e)

p.plot_grid('123')

plt.show()
