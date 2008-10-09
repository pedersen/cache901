#!/usr/bin/env python

try:
    import psyco
    psyco.full()
except ImportError:
    pass

import cache901.app

def main():
    app = cache901.app.Cache901App()
    app.MainLoop()

if __name__ == '__main__':
    main()
