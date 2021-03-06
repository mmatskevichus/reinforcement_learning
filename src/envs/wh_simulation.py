from src.envs import wh_map as wm
from src.envs import wh_objects as wo
from src.utils import config as co

import os


def render_map(map_obj, agent_obj):
    for i, row in enumerate(map_obj):
        to_print = list()
        for j, obj in enumerate(row):
            if (i, j) == agent_obj.coordinates:
                to_print.append(agent_obj.sprite)
            else:
                to_print.append(obj.sprite)
        print(''.join(to_print))


def sim_loop():
    map_obj, product_scheme = wm.init_wh_map(
        wm.wh_vis_map,
        max_weight=200,
        max_volume=100,
        path_to_catalog=co.PATH_TO_CATALOG
    )
    agent_obj = wo.Agent(
        coordinates=(18, 9),
        product_scheme=product_scheme
    )

    actions = {
        'w': lambda x, y: x.move(to='u', map_obj=y),
        'a': lambda x, y: x.move(to='l', map_obj=y),
        's': lambda x, y: x.move(to='d', map_obj=y),
        'd': lambda x, y: x.move(to='r', map_obj=y),
        't': lambda x, y: x.take_product(map_obj=y),
        'g': lambda x, y: x.deliver_products(map_obj=y),
        'i': lambda x, y: x.inspect_shelf(map_obj=y),
        'r': lambda x, _: x.wait(),
        'q': 'break_loop',
    }

    reward_policy = {
        2: 50,
        1: 0,
        0: -10,
        10: 500,
        -1: -1000
    }

    score = 0
    os.system('clear')
    render_map(map_obj, agent_obj)
    print(f'Score: {score}')
    while True:
        agent_obj.order_list()
        while True:
            action = input()
            if action in actions:
                os.system('clear')
                break
            print('Unknown command. Try again.')
        if actions[action] == 'break_loop':
            print('Breaking simulation.')
            break

        responce = actions[action](agent_obj, map_obj)
        if not isinstance(responce, int):
            print(responce)
        elif responce in reward_policy:
            score += reward_policy[responce]
        elif responce > 0 and responce % 10 == 0:
            for _ in range(responce / 10):
                score += reward_policy[responce]
        else:
            score += responce

        score -= 10
        render_map(map_obj, agent_obj)
        print(f'Score: {score}')
        print(agent_obj.order_list)


if __name__ == '__main__':
    sim_loop()
