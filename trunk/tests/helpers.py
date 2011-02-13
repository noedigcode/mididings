# -*- coding: utf-8 -*-
#
# mididings
#
# Copyright (C) 2008-2011  Dominic Sacré  <dominic.sacre@gmx.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

import unittest
import random
import itertools

from mididings import *
from mididings import setup, engine, misc, constants
from mididings.event import *


class MididingsTestCase(unittest.TestCase):
    def setUp(self):
        setup.reset()
        setup.config(data_offset = 0)

    def check_patch(self, patch, d):
        """
        Test the given patch. d must be a mapping from events to the expected
        list of resulting events.
        """
        self.check_scenes({ setup.get_config('data_offset'): patch }, d)

    def check_scenes(self, scenes, d):
        """
        Test the given scenes. d must be a mapping from events to the expected
        list of resulting events.
        """
        for ev, expected in d.items():
            r = self.run_scenes(scenes, ev)
            for x in r:
                x.__class__ = MidiEvent
            if isinstance(expected, bool):
                # boolean value: ensure that at most one event was returned
                self.assertLessEqual(len(r), 1)
                # ensure that event is unchanged
                if len(r):
                    self.assertEqual(r[0], ev)
                # check if the result is as expected
                self.assertEqual(bool(len(r)), expected,
                        "\nscenes=%s\nev=%s\nexpected=%s" % (repr(scenes), repr(ev), repr(expected)))
            else:
                # list: check if the result is exactly as expected
                self.assertEqual(r, expected,
                        "\nscenes=%s\nev=%s\nr=%s\nexpected=%s" % (repr(scenes), repr(ev), repr(r), repr(expected)))

    def check_filter(self, filt, d):
        """
        Test if the filter filt works as expected.
        d must be a mapping from events to a tuple of two booleans, where the
        first value specifies if the event should match the filter as is, and
        the second value specifies if the event should match the inverted
        filter.
        """
        for ev, expected in d.items():
            for f, p in zip((filt, ~filt, -filt), [expected[0], expected[1], not expected[0]]):
                self.check_patch(f, {ev: p})

    def run_patch(self, patch, events):
        """
        Run the given events through the given patch, return the list of
        resulting events.
        """
        return self.run_scenes({ setup.get_config('data_offset'): patch }, events)

    def run_scenes(self, scenes, events):
        """
        Run the given events through the given scenes, return the list of
        resulting events.
        """
        setup.config(check=False,
            backend='dummy'
        )
        e = engine.Engine(scenes, None, None, None)
        r = []
        if not misc.issequence(events):
            events = [events]
        for ev in events:
            r += e.process(ev)[:]
        return r

    def make_event(self, *args, **kwargs):
        """
        Create a new MIDI event. Attributes can be specified in args or
        kwargs, unspecified attributes are filled with random values.
        """
        type, port, channel, data1, data2 = itertools.islice(itertools.chain(args, itertools.repeat(None)), 5)

        for k, v in kwargs.items():
            if k == 'type': type = v
            if k == 'port': port = v
            elif k == 'channel': channel = v
            elif k in ('data1', 'note', 'ctrl'): data1 = v
            elif k in ('data2', 'velocity', 'value', 'program'): data2 = v

        if type == None:
            type = random.choice(list(set(constants._EVENT_TYPE_NAMES.keys()) - set([SYSEX, DUMMY])))
        if port == None:
            port = random.randrange(0, 42)
        if channel == None:
            channel = random.randrange(0, 16)
        if data1 == None:
            data1 = random.randrange(0, 128)
        if data2 == None:
            data2 = (random.randrange(1, 128) if type == NOTEON
                     else 0 if type == NOTEOFF
                     else random.randrange(0, 128))

        return MidiEvent(type, port, channel, data1, data2)

    def modify_event(self, ev, **kwargs):
        """
        Make a copy of the event ev, replacing arbitrary attributes with the
        values given in kwargs.
        """
        r = MidiEvent(ev.type, ev.port, ev.channel, ev.data1, ev.data2)
        for k, v in kwargs.items():
            setattr(r, k, v)
        return r