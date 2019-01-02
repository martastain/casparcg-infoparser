#!/usr/bin/env python3

import time

from nxtools import *
from nxtools.caspar import *

from ccginfo import *


caspar = CasparCG("192.168.4.107")
Parser = get_info_parser(caspar)
if not Parser:
   critical_error()

parser = Parser(caspar, 1)

caspar.query("PLAY 1-10 amb LENGTH 250")
caspar.query("LOADBG 1-10 pal_ffxdcam35 AUTO")# SEEK 500 LENGTH 500 AUTO")

while True:
    try:
        info = parser.get_info()
        print ("{} {} / {} (nxt: {})".format(
                info["current"],
                info["pos"],
                info["dur"],
                info["cued"]
            ))
        time.sleep(.02)
    except KeyboardInterrupt:
        break

