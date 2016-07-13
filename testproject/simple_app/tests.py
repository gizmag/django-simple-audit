"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from __future__ import absolute_import, unicode_literals

import unittest

from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.test.utils import override_settings
from django.conf import settings

from .models import Topping, Pizza

from simple_audit.models import Audit
from simple_audit import settings as audit_settings
from simple_audit import m2m_audit

class SimpleTest(TestCase):

    def setUp(self):
        super(SimpleTest, self).setUp()
        self.topping_onion = Topping.objects.get_or_create(name="onion")[0]
        self.topping_egg = Topping.objects.get_or_create(name="egg")[0]

        self.content_type_topping = ContentType.objects.get_for_model(Topping)
        self.content_type_pizza = ContentType.objects.get_for_model(Pizza)

    @unittest.expectedFailure
    def test_add_topping_and_search_audit(self):
        """Tests add a topping."""
        topping = Topping.objects.get_or_create(name="potato")[0]

        #topping created
        self.assertTrue(topping.pk)
        #audit recorded?
        self.assertTrue(Audit.objects.get(operation=0, 
                                            content_type=self.content_type_topping,
                                            object_id=topping.pk,
                                            description="Added potato"))

    @unittest.expectedFailure
    def test_add_pizza_without_toppings(self):
        """Test add pizza without topping."""
        pizza = Pizza.objects.get_or_create(name="mussarela")[0]

        #pizza created?
        self.assertTrue(pizza.pk)
        #toppings added?
        self.assertEqual(pizza.toppings.all().count(), 0)
        #audit recorded?
        self.assertTrue(Audit.objects.get(operation=0, 
                                            content_type=self.content_type_pizza,
                                            object_id=pizza.pk,
                                            description="Added mussarela"))


    @unittest.expectedFailure
    def test_add_pizza_with_toppings_with_audit_enabled(self):
        """Test add pizza with topping."""

        self.assertTrue(settings.DJANGO_SIMPLE_AUDIT_M2M_FIELDS)
        audit_settings.DJANGO_SIMPLE_AUDIT_M2M_FIELDS = settings.DJANGO_SIMPLE_AUDIT_M2M_FIELDS

        pizza = Pizza.objects.get_or_create(name="peperoni")[0]

        #pizza created?
        self.assertTrue(pizza.pk)
        #toppings added?
        pizza.toppings.add(self.topping_onion)

        self.assertEqual(pizza.toppings.all().count(), 1)

        #audit recorded?
        self.assertTrue(Audit.objects.get(operation=0, 
                        content_type=self.content_type_pizza,
                        object_id=pizza.pk,
                        description="Added peperoni"))

        #m2m audit recorded?
        desc = 'field toppings.{pk}.id was changed\nfield toppings.{pk}.name was changed'.format(pk=self.topping_onion.pk)

        self.assertTrue(Audit.objects.get(operation=1,
                            content_type=self.content_type_pizza,
                            object_id=pizza.pk,
                            description=desc))


    def test_m2m_dict_diff_with_new_and_old_state_different(self):
        """Test where old state and new state contains different elements."""

        new_state={'toppings': [{'id': 1, 'name': 'ceboloa'},
                                      {'id': 5, 'name': 'cogumelo'},
                                      {'id': 6, 'name': 'abobrinha'},
                                      {'id': 8, 'name': 'codorna'},
                                      {'id': 9, 'name': 'banana'},
                                      {'id': 10, 'name': 'abacaxi'},
                                      ]}

        old_state={'toppings': [{'id': 1, 'name': 'ceboloa'},
                    {'id': 5, 'name': 'cogumelo'},
                    {'id': 6, 'name': 'abobrinha'},
                    {'id': 8, 'name': 'codorna'},
                    {'id': 9, 'name': 'banana'},
                    {'id': 11, 'name': 'abacate'},
                   ]}

        expected_response = [{'toppings.10.id': [None, 10], 'toppings.10.name': [None, 'abacaxi']},
                    {'toppings.11.id': [11, None], 'toppings.11.name': ['abacate', None]}]

        diff = m2m_audit.m2m_dict_diff(old_state, new_state)

        self.assertEqual(diff, expected_response)


    def test_m2m_dict_diff_with_empty_new_state(self):
        """Test where new state is an empty dict."""

        new_state={}

        old_state={'toppings': [{'id': 1, 'name': 'ceboloa'},
                    {'id': 5, 'name': 'cogumelo'},
                    {'id': 6, 'name': 'abobrinha'},
                    {'id': 8, 'name': 'codorna'},
                    {'id': 9, 'name': 'banana'},
                    {'id': 11, 'name': 'abacate'},
                   ]}

        expected_response = [
            {'toppings.1.id': [1, None], 'toppings.1.name': ['ceboloa', None]},
            {'toppings.11.id': [11, None], 'toppings.11.name': ['abacate', None]},
            {'toppings.5.id': [5, None], 'toppings.5.name': ['cogumelo', None]},
            {'toppings.6.id': [6, None], 'toppings.6.name': ['abobrinha', None]},
            {'toppings.8.id': [8, None], 'toppings.8.name': ['codorna', None]},
            {'toppings.9.id': [9, None], 'toppings.9.name': ['banana', None]},
        ]

        diff = m2m_audit.m2m_dict_diff(old_state, new_state)

        self.assertEqual(diff, expected_response)


    def test_m2m_dict_diff_with_empty_old_state(self):
        """Test where old state is an empty dict."""

        new_state={'toppings': [{'id': 1, 'name': 'ceboloa'},
                                      {'id': 5, 'name': 'cogumelo'},
                                      {'id': 6, 'name': 'abobrinha'},
                                      {'id': 8, 'name': 'codorna'},
                                      {'id': 9, 'name': 'banana'},
                                      {'id': 10, 'name': 'abacaxi'},
                                      ]}

        old_state={}

        expected_response = [
            {'toppings.1.id': [None, 1], 'toppings.1.name': [None, 'ceboloa']},
            {'toppings.10.id': [None, 10], 'toppings.10.name': [None, 'abacaxi']},
            {'toppings.5.id': [None, 5], 'toppings.5.name': [None, 'cogumelo']},
            {'toppings.6.id': [None, 6], 'toppings.6.name': [None, 'abobrinha']},
            {'toppings.8.id': [None, 8], 'toppings.8.name': [None, 'codorna']},
            {'toppings.9.id': [None, 9], 'toppings.9.name': [None, 'banana']},
        ]

        diff = m2m_audit.m2m_dict_diff(old_state, new_state)

        self.assertEqual(diff, expected_response)


    def test_m2m_dict_diff_with_old_and_new_state_the_same(self):
        """Test where old state and new state are the same. no change detected!"""

        new_state={'toppings': [{'id': 1, 'name': 'ceboloa'},
                                  {'id': 5, 'name': 'cogumelo'},
                                  {'id': 6, 'name': 'abobrinha'},
                                  {'id': 8, 'name': 'codorna'},
                                  {'id': 9, 'name': 'banana'},
                                  {'id': 10, 'name': 'abacaxi'},
                                  ]}

        old_state={'toppings': [{'id': 1, 'name': 'ceboloa'},
                                    {'id': 5, 'name': 'cogumelo'},
                                    {'id': 6, 'name': 'abobrinha'},
                                    {'id': 8, 'name': 'codorna'},
                                    {'id': 9, 'name': 'banana'},
                                    {'id': 10, 'name': 'abacaxi'},
                                    ]}

        expected_response = []

        diff = m2m_audit.m2m_dict_diff(old_state, new_state)

        self.assertEqual(diff, expected_response)
