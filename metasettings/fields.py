from __future__ import unicode_literals

from django.db import models
from django.db.models.fields import BLANK_CHOICE_DASH
from django.utils.encoding import force_text
from django.utils.functional import lazy

from .models import Currency, currencies


class CurrencyDescriptor(object):
    def __init__(self, field):
        self.field = field

    def __get__(self, instance=None, owner=None):
        if instance is None:
            raise AttributeError(
                "The '%s' attribute can only be accessed from %s instances."
                % (self.field.name, owner.__name__))
        return Currency(
            code=instance.__dict__[self.field.name],
        )

    def __set__(self, instance, value):
        if value is not None:
            value = force_text(value)
        instance.__dict__[self.field.name] = value


class CurrencyField(models.CharField):
    descriptor_class = CurrencyDescriptor

    def __init__(self, *args, **kwargs):
        currencies_class = kwargs.pop('currencies', None)
        self.currencies = currencies_class() if currencies_class else currencies
        self.blank_label = kwargs.pop('blank_label', None)

        kwargs.update({
            'choices': self.currencies,
            'max_length': 3
        })

        return super(CurrencyField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return "CharField"

    def contribute_to_class(self, cls, name):
        super(CurrencyField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, self.descriptor_class(self))

    def get_prep_value(self, value):
        "Returns field's value prepared for saving into a database."
        # Convert the Currency to unicode for database insertion.
        if value is None or getattr(value, 'code', '') is None:
            return None
        return force_text(value)

    def get_prep_lookup(self, lookup_type, value):
        if hasattr(value, 'code'):
            value = value.code

        return super(CurrencyField, self).get_prep_lookup(lookup_type, value)

    def get_choices(
            self, include_blank=True, blank_choice=None, *args, **kwargs):
        if blank_choice is None:
            if self.blank_label is None:
                blank_choice = BLANK_CHOICE_DASH
            else:
                blank_choice = [('', self.blank_label)]
        return super(CurrencyField, self).get_choices(
            include_blank=include_blank, blank_choice=blank_choice, *args,
            **kwargs)

    get_choices = lazy(get_choices, list)

    def deconstruct(self):
        name, path, args, kwargs = super(CurrencyField, self).deconstruct()
        kwargs.pop('choices')
        if self.currencies is not currencies:
            # Include the countries class if it's not the default countries
            # instance.
            kwargs['currencies'] = self.currencies.__class__
        return name, path, args, kwargs


try:  # pragma: no cover
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ['^metasettings\.fields\.CurrencyField'])
except ImportError:
    pass
