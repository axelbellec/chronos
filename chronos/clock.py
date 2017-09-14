# coding: utf-8

""" Custom clock script for Heroku. """

from apscheduler.schedulers.blocking import BlockingScheduler

from chronos.cli import cli
from chronos.tracing import log_factory
from chronos.config import CHRONOS_FORCE_UPDATE

log = log_factory(__name__)

def timed_job():
    log.debug('this job is run every five minutes')
    cli(force=CHRONOS_FORCE_UPDATE)
    
if __name__ == '__main__':
    sched = BlockingScheduler()
    sched.add_job(timed_job, 'cron', id='run_every_5_min', minute='*/5')
    sched.start()