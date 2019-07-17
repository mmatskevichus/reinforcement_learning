import gym
import numpy as np
from gym import spaces
import os

from src.envs import wh_map as wm
from src.envs import wh_objects as wo
from src.models.ConvDQN import create_wh_sreen
from src.utils import config as co

import os


class WarehouseEnv(gym.Env):
    metadata = {
        'render.modes': ['human', 'ansi']
    }

    def __init__(self, map_sketch=wm.wh_vis_map, num_turns=None, max_order_line=25, frequency=0.2,
                 simplified_state=False, silent=True):
        self.map_sketch = map_sketch
        self.silent = silent
        self.frequency = frequency
        self.load_map = wm.init_wh_map
        self.simplified_state = simplified_state
        self.map, self.product_scheme = self.load_map(
            self.map_sketch,
            max_weight=200,
            max_volume=100,
            path_to_catalog=co.PATH_TO_CATALOG,
            silent=self.silent
        )
        self.agent = wo.Agent(
            coordinates=(18, 9),
            silent=self.silent,
            max_weight=200,
            max_volume=100,
            frequency=self.frequency,
            product_scheme=self.product_scheme
        )

        self.actions = {
            'w': lambda x, y: x.move(to='u', map_obj=y),
            'a': lambda x, y: x.move(to='l', map_obj=y),
            's': lambda x, y: x.move(to='d', map_obj=y),
            'd': lambda x, y: x.move(to='r', map_obj=y),
            't': lambda x, y: x.take_product(map_obj=y),
            'g': lambda x, y: x.deliver_products(map_obj=y),
            'i': lambda x, y: x.inspect_shelf(map_obj=y),
            'r': lambda x, _: x.wait(),
            # 'q': 'break_loop',
        }

        self.action_space = spaces.Discrete(len(self.actions))
        if self.simplified_state:
            self.observation_space = spaces.Box(
                low=np.array([1, 1, 0, 0]),
                high=np.array([
                    len(self.map[0])-2,
                    len(self.map)-2,
                    self.agent.max_weight,
                    self.agent.max_volume
                ]),
                dtype=np.uint32
            )
        else:
            pass  # TODO: finish observation space for product scheme

        self.reward_policy = {
            2: 50,
            1: 0,
            0: -10,
            10: 500, #done
            -1: -1000 #drop
        }

        if num_turns is None:
            self.num_turns = np.inf
        else:
            self.num_turns = num_turns

        if max_order_line is None:
            self.max_order_line = np.inf
        else:
            self.max_order_line = max_order_line

        self.turns_left = self.num_turns
        self.score = 0
        self.encode = self._get_action_code()

    @staticmethod
    def map2feats(map, agent):
        feats = list()
        encoder = dict()
        for i, row in enumerate(map):
            for j, obj in enumerate(row):
                if (i, j) == agent.coordinates:
                    sprite = agent.sprite
                else:
                    sprite = obj.sprite
                if sprite not in encoder:
                    encoder[sprite] = len(encoder)
                code = encoder[sprite]
                feats.append(code)
        return feats

    def _get_action_code(self):
        acts = dict()
        for i, act in enumerate(self.actions.keys()):
            acts[i] = act
        return acts

    def step(self, action_code):


        # TODO: 1) step needs to return next_observ (state), reward, done 2) observation - map (0 - floor, 1 - objects)
        self.agent.order_list()
        action = self.encode[action_code]
        responce = self.actions[action](self.agent, self.map)

        if not isinstance(responce, int):
            reward = 0
            if not self.silent: print(responce)
        elif responce in self.reward_policy:
            reward = self.reward_policy[responce]
        elif responce > 0 and responce % 10 == 0:
            reward = 0
            for _ in range(responce // 10):
                reward += self.reward_policy[10]
        else:
            reward = responce
        reward -= 10
        self.score += reward
        self.turns_left -= 1
        observation = []  # self.map2feats(self.map, self.agent)
        observation += [*self.agent.coordinates, self.agent.free_volume, self.agent.available_load]

        if self.turns_left <= 0 or len(self.agent.order_list) > self.max_order_line:
            done = True
        else:
            done = False

        # info = self.agent.order_list.__str__()

        screen = self.render()
        return create_wh_sreen(screen), action_code, reward, done  # , {'order_list': info}

    def reset(self):
        self.map, self.product_scheme = self.load_map(
            self.map_sketch,
            max_weight=200,
            max_volume=100,
            path_to_catalog=co.PATH_TO_CATALOG,
            silent=self.silent
        )
        self.agent = wo.Agent(
            coordinates=(18, 9),
            silent=self.silent,
            max_weight=200,
            max_volume=100,
            product_scheme=self.product_scheme
        )
        self.turns_left = self.num_turns

        #observation = [*self.agent.coordinates, self.agent.free_volume, self.agent.available_load]
        #return observation


    def render(self, mode='human'):  # TODO: finish respriting for shelves with products on product list
        picture = []
        for i, row in enumerate(self.map):
            to_print = list()
            for j, obj in enumerate(row):
                if (i, j) == self.agent.coordinates:
                    to_print.append(self.agent.sprite)
                else:
                    to_print.append(obj.sprite)
            picture.append(''.join(to_print))
        print('\n'.join(picture))
        return picture

    def close(self):
        os.system('clear')
