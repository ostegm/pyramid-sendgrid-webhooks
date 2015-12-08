#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_pyramid_sendgrid_webhooks
----------------------------------

Tests for `pyramid_sendgrid_webhooks` module.
"""

from __future__ import unicode_literals

import json
import unittest
from pyramid import testing

import pyramid_sendgrid_webhooks as psw
from pyramid_sendgrid_webhooks import events, errors


class EventGrabber(object):
    """ Grabs events as they're dispatched """
    def __init__(self):
        self.events = []
        self.last = None

    def __call__(self, event):
        self.events.append(event)
        self.last = event


class WebhookTestBase(unittest.TestCase):
    _PATH = '/webhook'

    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request)
        self.config.include('pyramid_sendgrid_webhooks', self._PATH)

    def tearDown(self):
        testing.tearDown()

    def _createGrabber(self, event_cls):
        grabber = EventGrabber()
        self.config.add_subscriber(grabber, event_cls)
        return grabber

    def _createRequest(self, event_body):
        if not isinstance(event_body, list):
            event_body = [event_body]
        self.request.json_body = event_body
        return self.request


class TestBaseEvents(WebhookTestBase):

    def _makeOne(self, event_type='bounce', category='category'):
        return {
            'asm_group_id': 1,
            'category': category,
            'cert_error': '0',
            'email': 'email@example.com',
            'event': event_type,
            'ip': '127.0.0.1',
            'reason': '500 No Such User',
            'smtp-id': '<original-smtp-id@domain.com>',
            'status': '5.0.0',
            'timestamp': 1249948800,
            'tls': '1',
            'type': 'bounce',
            'unique_arg_key': 'unique_arg_value',
        }

    def _create_dt(self):
        import datetime
        return datetime.datetime(2009, 8, 11, 0, 0)

    def test_event_parsed(self):
        grabber = self._createGrabber(events.BaseWebhookEvent)
        request = self._createRequest(self._makeOne())
        psw.receive_events(request)

        self.assertEqual(len(grabber.events), 1)

    def test_specific_event_caught(self):
        grabber = self._createGrabber(events.BounceEvent)
        request = self._createRequest(self._makeOne())
        psw.receive_events(request)

        self.assertEqual(len(grabber.events), 1)

    def test_unspecified_event_ignored(self):
        grabber = self._createGrabber(events.DeferredEvent)
        request = self._createRequest(self._makeOne())
        psw.receive_events(request)

        self.assertEqual(len(grabber.events), 0)

    def test_timestamp_parsed(self):
        grabber = self._createGrabber(events.BaseWebhookEvent)
        request = self._createRequest(self._makeOne())
        psw.receive_events(request)

        self.assertEqual(grabber.last.dt, self._create_dt())

    def test_unique_arguments_extracted(self):
        grabber = self._createGrabber(events.BaseWebhookEvent)
        request = self._createRequest(self._makeOne())
        psw.receive_events(request)

        self.assertDictEqual(grabber.last.unique_arguments, {
            'unique_arg_key': 'unique_arg_value',
        })

    def test_correct_subclass(self):
        grabber = self._createGrabber(events.BaseWebhookEvent)
        request = self._createRequest(self._makeOne())
        psw.receive_events(request)

        self.assertIsInstance(grabber.last, events.BounceEvent)

    def test_unknown_event_raises_exception(self):
        request = self._createRequest(self._makeOne(event_type='UNKNOWN'))
        self.assertRaises(
            errors.UnknownEventError, psw.receive_events, request)

    def test_single_category_is_list_wrapped(self):
        grabber = self._createGrabber(events.BaseWebhookEvent)
        request = self._createRequest(self._makeOne())
        psw.receive_events(request)

        self.assertEqual([grabber.last.category], grabber.last.categories)

    def test_multiple_categories_are_unchanged(self):
        grabber = self._createGrabber(events.BaseWebhookEvent)
        request = self._createRequest(self._makeOne(category=['c1', 'c2']))
        psw.receive_events(request)

        self.assertEqual(grabber.last.category, grabber.last.categories)

    def test_empty_categories_is_empty_list(self):
        grabber = self._createGrabber(events.BaseWebhookEvent)
        request = self._createRequest(self._makeOne(category=None))
        psw.receive_events(request)

        self.assertEqual(grabber.last.categories, [])


class TestDeliveryEvents(WebhookTestBase):
    def _makeOne(self):
        return {
            'asm_group_id': 1,
            'category': ['category1', 'category2'],
            'cert_error': '0',
            'email': 'email@example.com',
            'event': 'bounce',
            'ip': '127.0.0.1',
            'reason': '500 No Such User',
            'smtp-id': '<original-smtp-id@domain.com>',
            'status': '5.0.0',
            'timestamp': 1249948800,
            'tls': '1',
            'type': 'bounce',
            'unique_arg_key': 'unique_arg_value',
        }


class TestEngagementEvents(WebhookTestBase):
    def _makeOne(self):
        return {
            'asm_group_id': 1,
            'category': ['category1', 'category2'],
            'email': 'email@example.com',
            'event': 'click',
            'ip': '255.255.255.255',
            'timestamp': 1249948800,
            'unique_arg_key': 'unique_arg_value',
            'url': 'http://yourdomain.com/blog/news.html',
            'useragent': 'Example Useragent',
        }


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
