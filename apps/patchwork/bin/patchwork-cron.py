#!/usr/bin/env python

import sys
from patchwork.utils import send_notifications, do_expiry

def main(args):
    errors = send_notifications()
    for (recipient, error) in errors:
        print "Failed sending to %s: %s" % (recipient.email, ex)

    do_expiry()

if __name__ == '__main__':
    sys.exit(main(sys.argv))

