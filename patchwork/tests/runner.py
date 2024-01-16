# Patchwork - automated patch tracking system
# Copyright (C) 2023 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from unittest import TestResult
from unittest import TextTestRunner

from django.test.runner import DiscoverRunner
from termcolor import colored


# Based on upstream source
# https://github.com/python/cpython/blob/v3.11.4/Lib/unittest/runner.py
class ColourTextTestResult(TestResult):
    def __init__(self, stream, descriptions, verbosity, *, durations=None):
        super().__init__(stream, descriptions, verbosity)

        self.stream = stream
        self.descriptions = descriptions
        self.verbosity = verbosity

    def startTest(self, test):
        super().startTest(test)
        if self.verbosity > 1:
            self.stream.write(colored(str(test), 'white'))
            self.stream.write(colored(' ... ', 'white'))
            self.stream.flush()

    def _reportResult(self, short, long, color):
        if self.verbosity == 1:
            self.stream.write(short)
        else:  # > 1
            self.stream.writeln(colored(long, color, attrs=['bold']))
        self.stream.flush()

    def addSuccess(self, test):
        super().addSuccess(test)
        self._reportResult('.', 'ok', 'green')

    def addError(self, test, err):
        super().addError(test, err)
        self._reportResult('E', 'ERROR', 'red')

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._reportResult('F', 'FAIL', 'yellow')

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._reportResult('s', f'skipped {reason!r}', 'white')

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self._reportResult('s', 'expected failure', 'blue')

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self._reportResult('s', 'unexpected success', 'red')

    def printErrors(self):
        self.stream.writeln()
        self.stream.flush()

        self.printErrorList('ERROR', self.errors)
        self.printErrorList('FAIL', self.failures)

        unexpectedSuccesses = getattr(self, 'unexpectedSuccesses', ())
        if unexpectedSuccesses:
            self.stream.writeln('=' * 70)
            for test in unexpectedSuccesses:
                self.stream.writeln(f'UNEXPECTED SUCCESS: {str(test)}')
            self.stream.flush()

    def printErrorList(self, flavour, errors):
        for test, err in errors:
            self.stream.writeln('=' * 70)
            self.stream.writeln(f'{flavour}: {str(test)}')
            self.stream.writeln('-' * 70)
            self.stream.writeln(str(err))
            self.stream.flush()


class ColourTextTestRunner(TextTestRunner):
    resultclass = ColourTextTestResult


class PatchworkTestRunner(DiscoverRunner):
    test_runner = ColourTextTestRunner
