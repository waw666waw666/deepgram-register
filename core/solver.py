"""
Lightweight Slider & Track Simulator.
Generates human-like bezier mouse movements and simple gap calculations.
"""
import random
import time
from typing import List, Tuple
from playwright.sync_api import Page


def generate_bezier_track(distance: int) -> List[int]:
    """
    Generate non-linear incremental movement steps imitating human hand inertia:
    fast acceleration initially, slow deceleration near the destination.
    """
    steps: List[int] = []
    current = 0
    mid = distance * 0.7
    v = 0
    t = 0.2

    while current < distance:
        if current < mid:
            a = random.uniform(2.5, 4.0)
        else:
            a = -random.uniform(1.8, 3.2)
        v0 = v
        v = v0 + a * t
        move = int(v0 * t + 0.5 * a * (t ** 2))
        if move <= 0:
            move = 1
        if current + move > distance:
            move = distance - current
        current += move
        steps.append(move)

    # Add slight random micro-tremors around the endpoint
    for _ in range(random.randint(2, 4)):
        steps.append(random.choice([-1, 0, 1]))

    return steps


def simulate_drag(page: Page, slider_selector: str, distance: int):
    """Perform smooth human-like mouse dragging on a slider element."""
    box = page.locator(slider_selector).bounding_box()
    if not box:
        return

    start_x = box["x"] + box["width"] / 2
    start_y = box["y"] + box["height"] / 2

    page.mouse.move(start_x, start_y)
    page.mouse.down()
    time.sleep(random.uniform(0.1, 0.2))

    track = generate_bezier_track(distance)
    cur_x = start_x
    for move_x in track:
        cur_x += move_x
        # minor vertical jitter
        cur_y = start_y + random.uniform(-1.0, 1.0)
        page.mouse.move(cur_x, cur_y)
        time.sleep(random.uniform(0.01, 0.025))

    time.sleep(random.uniform(0.15, 0.3))
    page.mouse.up()
