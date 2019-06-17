import sched
import time

s = sched.scheduler(time.time, time.sleep)


def print_time(a="default"):
    print("From print_time", time.time(), a)


def print_some_times():
    s.enter(1, 1, print_time)
    s.enter(5, 2, print_some_times)
    print(s.queue)
    s.run(blocking=False)


print_some_times()
print("Looks like the queue is good")
