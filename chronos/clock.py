# coding: utf-8

from apscheduler.schedulers.blocking import BlockingScheduler

from chronos.cli import cli

sched = BlockingScheduler()

@sched.scheduled_job('interval', minutes=5)
def timed_job():
    print('This job is run every five minutes.')
    cli(force=True)
    
sched.start()