#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function


def utool_main():
    ignore_prefix = []
    ignore_suffix = []
    import utool as ut
    try:
        import utool as vt  # NOQA
    except ImportError:
        raise
    # allows for --tf
    ut.main_function_tester('utool', ignore_prefix, ignore_suffix)

if __name__ == '__main__':
    """
    python -m utool --tf infer_function_info:0
    """
    print('Checking utool main')
    utool_main()
