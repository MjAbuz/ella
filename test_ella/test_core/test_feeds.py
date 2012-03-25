# -*- coding: utf-8 -*-
from PIL import Image

from django.test import TestCase

from nose import tools, SkipTest

from django.core.urlresolvers import reverse
from django.http import HttpRequest

from ella.core.models import Listing
from ella.core.feeds import RSSTopCategoryListings
from ella.photos.models import Photo, Format

from test_ella.test_core import create_basic_categories, \
        create_and_place_more_publishables, list_all_publishables_in_category_by_hour

class TestFeeds(TestCase):

    def setUp(self):
        try:
            import feedparser
        except ImportError:
            raise SkipTest()

        super(TestFeeds, self).setUp()
        create_basic_categories(self)
        create_and_place_more_publishables(self)
        list_all_publishables_in_category_by_hour(self)


        self._feeder = RSSTopCategoryListings()

    def _set_photo(self):
        from test_ella.test_photos.fixtures import create_photo

        photo = create_photo(self)

        self.publishables[0].photo = photo
        self.publishables[0].save()
        # update the cache on the Listing object
        self.listings[0].publishable = self.publishables[0]

    def test_rss(self):
        import feedparser
        Listing.objects.all().update(category=self.category)
        url = reverse('home_rss_feed')
        c = self.client

        response = c.get(url)
        tools.assert_equals(200, response.status_code)
        d = feedparser.parse(response.content)

        tools.assert_equals(len(self.publishables), len(d['items']))

    def test_atom(self):
        import feedparser
        Listing.objects.all().update(category=self.category)
        url = reverse('home_atom_feed')
        c = self.client

        response = c.get(url)
        tools.assert_equals(200, response.status_code)
        d = feedparser.parse(response.content)

        tools.assert_equals(len(self.publishables), len(d['items']))

    def test_title_defaults_to_category_title(self):
        tools.assert_true(self._feeder.title(self.category), self.category.title)

    def test_title_uses_app_data_when_set(self):
        self.category.app_data = {'syndication': {'title': 'SYNDICATION_TITLE'}}
        tools.assert_true(self._feeder.title(self.category), 'SYNDICATION_TITLE')

    def test_description_defaults_to_category_title(self):
        tools.assert_true(self._feeder.title(self.category), self.category.title)

    def test_description_uses_app_data_when_set(self):
        self.category.app_data = {'syndication': {'description': 'SYNDICATION_DESCRIPTION'}}
        tools.assert_true(self._feeder.description(self.category), 'SYNDICATION_DESCRIPTION')

    def test_get_enclosure_uses_original_when_format_not_set(self):
        feeder = RSSTopCategoryListings()
        feeder.format = None
        self._set_photo()
        tools.assert_true(self.publishables[0].photo is not None)
        original = self.publishables[0].photo.image.url
        tools.assert_equals(original, feeder.item_enclosure_url(self.listings[0]))

    def test_get_enclosure_uses_formated_photo_when_format_available(self):
        f = Format.objects.create(name='enc_format', max_width=10, max_height=10,
            flexible_height=False, stretch=False, nocrop=False)

        feeder = RSSTopCategoryListings()
        feeder.format = f

        self._set_photo()
        tools.assert_true(self.publishables[0].photo is not None)
        original = self.publishables[0].photo.image
        new = self._feeder.item_enclosure_url(self.listings[0])
        tools.assert_not_equals(unicode(original), unicode(new))

    def test_get_enclosure_returns_none_when_no_image_set(self):
        tools.assert_equals(self._feeder.item_enclosure_url(self.listings[0]), None)




