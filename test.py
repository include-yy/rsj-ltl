import sys
import os
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
    print(ltl_result.stdout)
    return sexpdata.loads(ltl_result.stdout)

Q = sexpdata.Quoted
S = sexpdata.Symbol

def me_distance(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return distance

# test

# a1 = Q([S('and'), [S('F'), S(':a1')],
#         [S('F'), S(':a2')], [S('F'), S(':a3')]])
# a2 = Q([['a1', 'a2', 2], ['a2', 'a3', 4],
#         ['a1', 'a3', 3], ['0', 'a1', 1],
#         ['0', 'a2', 2], ['0', 'a3', 1]])

# print(me_call_emacsltl(a1, a2))

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
                         xytext=(-3, 5), ha='center')

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

        for i in range(x):
            obs.add((i, 0))
        for i in range(x):
            obs.add((i, y - 1))

        for i in range(y):
            obs.add((0, i))
        for i in range(y):
            obs.add((x - 1, i))

        use_what = 'old'
        if (use_what == 'old'):
            for i in range(10, 21):
                obs.add((i, 15))
            for i in range(15):
                obs.add((20, i))

            for i in range(15, 20):
                obs.add((30, i))
            for i in range(16):
                obs.add((40, i))
        else:
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
    s_start = (5, 5)
    s_goal = (45, 25)

    test_env = yy_env(s_start,
                      [['a1', (10, 20)],
                       ['a2', (20, 27)],
                       ['a3', (30, 10)],
                       ['a4', (40, 25)],
                       ['a5', (45, 5)]])
    # test_env.add_task('a1', (10, 20))
    # test_env.add_task('a2', (20, 27))
    # test_env.add_task('a3', (30, 10))
    # test_env.add_task('a4', (40, 25))
    # test_env.add_task('a5', (45, 5))

    # astar = yy_AStar(s_start, s_goal, test_env, "euclidean")

    # my_list = ['a1', 'a2', 'a3', 'a4', 'a5']
    # my_point = [s_start] + list(map(lambda x: test_env.task_point(x), my_list))
    # pairs = list(zip(my_point, my_point[1:]))

    a1 = Q([S('and'),
            [S('F'), S(':a1')],
            [S('F'), S(':a2')], [S('F'), S(':a3')],
            [S('F'), S(':a4')], [S('F'), S(':a5')]])
    # a1 = Q([S('and'),
    #         [S('F'), S(':a3')],
    #         [S('X'), [S('and'),
    #          [S('F'), S(':a1')], [S('F'), S(':a2')],
    #          [S('F'), S(':a4')], [S('F'), S(':a5')]]]])
    # a1 = Q([S('F'),
    #         [S('and'), S(':a5'),
    #          [S('X'), [S('F'),
    #                    [S('and'), S(':a4'),
    #                     [S('X'), [S('F'),
    #                               [S('and'), S(':a3'),
    #                                [S('X'), [S('F'),
    #                                          [S('and'), S(':a2'),
    #                                           [S('X'), [S('F'), S(':a1')]]]]]]]]]]]]])
    # a1 = Q([S('and'), [S('F'), S(':a5')], [S('X'), [S('and'), [S('F'), S(':a4')], [S('X'), [S('and'), [S('F'), S(':a3')], [S('X'), [S('and'), [S('F'), S(':a2')], [S('X'), [S('F'), S(':a1')]]]]]]]]])

    # a2 = Q([['a1', 'a2', 2], ['a2', 'a3', 4],
    #         ['a1', 'a3', 3], ['0', 'a1', 1],
    #         ['0', 'a2', 2], ['0', 'a3', 1]])
    a2 = Q(test_env.simple_distance(s_start))
    # print(a2)
    st1 = time.time()
    res = me_call_emacsltl(a1, a2)
    # print(time.time() - st1)
    my_list = ['a1', 'a2', 'a3', 'a4', 'a5']
    # my_list = res[0]
    my_point = [s_start] + list(map(lambda x: test_env.task_point(x), my_list))
    pairs = list(zip(my_point, my_point[1:]))

    # print the test result
    # JUST ONCE
    for p in pairs:
        l_start = p[0]
        l_target = p[1]
        astar = yy_AStar(l_start, l_target, test_env, "euclidean")
        l_plot = yy_Plotting(l_start, l_target, test_env)
        path, visited = astar.searching()
        l_plot.anime(path)

    plt.annotate('start', my_point[0],
                 textcoords="offset points",
                 xytext=(5, -12), ha='center')
    plt.annotate('end', my_point[-1],
                 textcoords="offset points",
                 xytext=(5, -12), ha='center')
    plt.show()

    # repeat test time
    N = 100
    total_time = 0.0
    for i in range(0, N):
        me_time = 0.0
        for p in pairs:
            l_start = p[0]
            l_target = p[1]
            astar = yy_AStar(l_start, l_target, test_env, "euclidean")
            # astar.s_start = l_start
            # astar.s_goal = l_target
            # if (i == 0):
            #     l_plot = yy_Plotting(l_start, l_target, test_env)
            st = time.time()
            path, visited = astar.searching()
            ed = time.time()
            # if (i == 0):
            #     l_plot.anime(path)
            me_time = me_time + ed - st
            # print(ed - st)
        #print(me_time)
        #print('---------------------------')
        total_time = total_time + me_time
    plt.annotate('start', my_point[0],
                 textcoords="offset points",
                 xytext=(5, -12), ha='center')
    plt.annotate('end', my_point[-1],
                 textcoords="offset points",
                 xytext=(5, -12), ha='center')

    print(total_time)
    print(total_time / N)

    # astar = yy_AStar(s_start, s_goal, test_env, "euclidean")
    # plot = yy_Plotting(s_start, s_goal, test_env)
    # st = time.time()
    # path, visited = astar.searching()
    # end = time.time()
    # print(end - st)

    # plot.anime(path)
    # plot.animation(path, visited, "A*")  # animation
    # s_start = (45, 25)
    # s_goal = (45, 5)
    # astar.s_start = (45, 25)
    # astar.s_goal = (45, 5)
    # plot = yy_Plotting(s_start, s_goal, test_env)
    # st = time.time()
    # path, visited = astar.searching()
    # end = time.time()
    # print(end - st)
    # # plot.animation(path, visited, "A*")  # animation
    # plot.anime(path)
    # astar.Env.simple_distance((1, 2))
    # print(astar.Env.task_point('a1'))
    # plt.show()

if __name__ == '__main__':
    main()
