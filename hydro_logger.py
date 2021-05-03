# -*- coding: utf-8 -*-
"""
Created on Fri Jul  1 21:50:14 2016

@author: bernd
"""

import logging
import logging.handlers

__all__ = ['my_logger']

my_logger = logging.getLogger('MyLogger')
#my_logger.setLevel(logging.INFO)
my_logger.setLevel(logging.DEBUG)

#handler = logging.handlers.WatchedFileHandler('/var/log/syslog')
try:
    handler = logging.handlers.RotatingFileHandler('/home/pi/work/hydroponic/hydro.log', mode='a', maxBytes=300000, backupCount=2, encoding=None, delay=0)
    my_logger.addHandler(handler)
except Exception:
    #in case we run unit tests whíle the application is running
    handler = logging.StreamHandler()
    my_logger.addHandler(handler)

