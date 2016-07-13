#!/usr/bin/env python
import os
import sys


os.environ['DJANGO_SETTINGS_MODULE'] = 'testproject.settings'

def run_tests():
    """Run the test suite."""
    import django
    from django.test.runner import DiscoverRunner
    django.setup()
    test_runner = DiscoverRunner(verbosity=2, interactive=False)
    failures = test_runner.run_tests(['.'])
    sys.exit(bool(failures))

if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
