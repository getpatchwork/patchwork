#!/usr/bin/env python

import sys
from patchwork.utils import send_notifications

def main(args):
    errors = send_notifications()
    for (recipient, error) in errors:
        print "Failed sending to %s: %s" % (recipient.email, ex)

if __name__ == '__main__':
    sys.exit(main(sys.argv))

