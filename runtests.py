#!/usr/bin/env python
"""
Running tests for djangosaml2_spid application.
"""
import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.test_settings'
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2 if '-v' in sys.argv else 1,
                             failfast='-f' in sys.argv)
    test_labels = [arg for arg in sys.argv[1:]
                   if arg.startswith('tests') or arg.startswith('djangosaml2_spid')]
    failures = test_runner.run_tests(test_labels or ['tests', 'src'])
    sys.exit(bool(failures))
