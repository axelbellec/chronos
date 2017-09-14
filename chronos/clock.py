# coding: utf-8

from apscheduler.schedulers.blocking import BlockingScheduler

from chronos.cli import cli
from chronos.tracing import log_factory

log = log_factory(__name__)
sched = BlockingScheduler()


@sched.scheduled_job('interval', minutes=5)
def timed_job():
    log.info('this job is run every five minutes')
    cli()
    

if __name__ == '__main__':
    sched.start()