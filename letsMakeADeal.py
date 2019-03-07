# Robert Gaffney 3/2/2019
#
# Simple script to calculate if there is a strategic advantage to choosing to switch doors in the Monty Hall problem:
# https://en.wikipedia.org/wiki/Monty_Hall_problem
#
# Rather than attempting to solve via logical deduction, solves empirically by testing a large number of cases. This
# is also a useful statistical exercise to see how sample sizes affect the accuracy of the prediction
#
# While coding the logic of the game, it became clear it could be simplified as
# 1) Choose switch door strategy
#   a) Initially choose correct door = lose
#   b) Initially choose either wrong door = win
# 2) Choose keep door strategy
#   a) Initially choose correct door = win
#   b) Initially choose either wrong door = lose
#
# Since the initial odds of initially choosing the correct door are 1/3, the better strategy is clearly to switch.

import datetime
import rx # Using RxPY 3 pre-release
from rx import operators as ops
from rx.concurrency import newthreadscheduler
import random
import array
import logging
import time

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def get_eliminated_door(correct_door, first_choice_door):
    elim_door_possibilities = array.array('i')
    for j in range(1, 4):
        if j != correct_door and j != first_choice_door:
            elim_door_possibilities.append(j)
    return random.choice(elim_door_possibilities)


logger.debug('Starting using simple imperative style')

switchWins = 0
switchLoss = 0
keepWins = 0
keepLoss = 0
i = 0

start = datetime.datetime.now()
for i in range(1, 20001):
    correctDoor = random.randrange(1, 4)
    firstChoiceDoor = random.randrange(1, 4)
    secondChoiceDoor = 0

    # For even tests, we will use the switch doors strategy
    mod = i % 2
    if mod == 0:
        eliminatedDoor = get_eliminated_door(correctDoor, firstChoiceDoor)
        for k in range(1, 4):
            if k != eliminatedDoor and k != firstChoiceDoor:
                secondChoiceDoor = k
        if secondChoiceDoor == correctDoor:
            switchWins = switchWins + 1
        else:
            switchLoss = switchLoss + 1
    else:
        # otherwise we will keep our door
        if firstChoiceDoor == correctDoor:
            keepWins = keepWins + 1
        else:
            keepLoss = keepLoss + 1

logger.debug('Finished in : {}'.format(datetime.datetime.now() - start))

logger.debug('Switch Wins: {}'.format(switchWins))
logger.debug('Switch Losses: {}'.format(switchLoss))
logger.debug('Keep Wins: {}'.format(keepWins))
logger.debug('Keep Losses: {}'.format(keepLoss))

logger.debug('Switch Win %: {}'.format(switchWins / (switchWins + switchLoss) * 100))
logger.debug('Keep Win %: {}'.format(keepWins / (keepWins + keepLoss) * 100))


def doors_helper(doors):
    doors['eliminated'] = get_eliminated_door(doors['correct'], doors['first'])
    return doors


def doors_helper2a(doors, x):
    doors['final_choice'] = x
    return doors


def doors_helper2(doors):
    obs = rx.from_iterable(range(1, 4)).pipe(
        ops.filter(lambda x: x != doors['eliminated']),
        ops.filter(lambda x: x != doors['first']),
        ops.first(),
        ops.map(lambda x: doors_helper2a(doors, x))
    )

    return obs
    
    
def increment_wins(wins_and_total, won):
    if won:
        return wins_and_total[0] + 1, wins_and_total[1] + 1
    return wins_and_total[0], wins_and_total[1] + 1


logger.debug('-------------------------------------------------')
logger.debug('Trying again using declarative ops on rxpy stream')
logger.debug('Using Switch Doors strat')

# scheduler = newthreadscheduler.NewThreadScheduler()

start = datetime.datetime.now()
rx.from_iterable(range(1, 10001)).pipe(
    # ops.observe_on(scheduler=scheduler),
    ops.filter(lambda x: x % 2 == 0),
    ops.map(lambda y: {'first': random.randrange(1, 4), 'correct': random.randrange(1, 4)}),
    ops.map(lambda doors: doors_helper(doors)),
    ops.flat_map(lambda doors: doors_helper2(doors)),
    ops.map(lambda doors: doors['correct'] == doors['final_choice']),
    ops.reduce(lambda wins_and_total, won: increment_wins(wins_and_total, won), (0, 0)),
).subscribe(
    on_next=lambda tots_wins: logger.debug('wins/total: {}/{}, {}%'.format(tots_wins[0], tots_wins[1],
                                                                           tots_wins[0]/tots_wins[1]*100)),
    on_completed=lambda: logger.debug(
        'finished at: {}; duration: {}'.format(datetime.datetime.now(), datetime.datetime.now() - start)),
    on_error=lambda err: logger.debug('error: {}'.format(err))
)

time.sleep(4)

logger.debug('Using Keep Doors strat')
start = datetime.datetime.now()
rx.from_iterable(range(1, 10001)).pipe(
    # ops.observe_on(scheduler=scheduler),
    ops.filter(lambda x: x % 2 == 0),
    ops.map(lambda y: {'first': random.randrange(1, 4), 'correct': random.randrange(1, 4)}),
    ops.map(lambda doors: doors['correct'] == doors['first']),
    ops.reduce(lambda wins_and_total, won: increment_wins(wins_and_total, won), (0, 0)),
).subscribe(
    on_next=lambda tots_wins: logger.debug('wins/total: {}/{}, {}%'.format(tots_wins[0], tots_wins[1],
                                                                           tots_wins[0]/tots_wins[1]*100)),
    on_completed=lambda: logger.debug(
        'finished at: {}; duration: {}'.format(datetime.datetime.now(), datetime.datetime.now() - start)),
    on_error=lambda err: logger.debug('error: {}'.format(err))
)

# rxpy 3 doesn't support blocking yet, afaik - need to sleep main thread to keep application from terminating
time.sleep(4)
