"""Managers of Zinnia"""
from datetime import datetime

from django.db import models
from django.contrib.sites.models import Site
from django.utils.translation import get_language
from django.conf import settings


DRAFT = 0
HIDDEN = 1
PUBLISHED = 2
FILTER_ON_LANGUAGE = getattr(settings, "ZINNIA_FILTER_ON_LANGUAGE")


def tags_published():
    """Return the published tags"""
    from tagging.models import Tag
    from zinnia.models import Entry
    tags_entry_published = Tag.objects.usage_for_queryset(
        Entry.published.all())
    # Need to do that until the issue #44 of django-tagging is fixed
    return Tag.objects.filter(name__in=[t.name for t in tags_entry_published])


class AuthorPublishedManager(models.Manager):
    """Manager to retrieve published authors"""

    def get_query_set(self):
        """Return published authors"""
        now = datetime.now()
        return super(AuthorPublishedManager, self).get_query_set().filter(
            entries__status=PUBLISHED,
            entries__start_publication__lte=now,
            entries__end_publication__gt=now,
            entries__sites=Site.objects.get_current()
            ).distinct()


def entries_published(queryset):
    """Return only the entries published"""
    now = datetime.now()
    filters = {
        'status': PUBLISHED,
        'start_publication__lte': now,
        'end_publication__gt': now,
        'sites': Site.objects.get_current()
    }
    if FILTER_ON_LANGUAGE:
        language = get_language()
        title = 'title_%s' % language
        slug = 'slug_%s' % language
        filters['%s__isnull' % title] = False
        filters['%s__isnull' % slug] = False
    result = queryset.filter(**filters)
    if FILTER_ON_LANGUAGE:
        title_arg = {
            '%s__exact' % title: '',
        }
        slug_arg = {
            '%s__exact' % slug: '',
        }
        result = result.filter(~models.Q(**title_arg), ~models.Q(**slug_arg))
    return result


class EntryPublishedManager(models.Manager):
    """Manager to retrieve published entries"""

    def get_query_set(self):
        """Return published entries"""
        return entries_published(
            super(EntryPublishedManager, self).get_query_set())

    def on_site(self):
        """Return entries published on current site"""
        return super(EntryPublishedManager, self).get_query_set(
            ).filter(sites=Site.objects.get_current())

    def search(self, pattern):
        """Top level search method on entries"""
        try:
            return self.advanced_search(pattern)
        except:
            return self.basic_search(pattern)

    def advanced_search(self, pattern):
        """Advanced search on entries"""
        from zinnia.search import advanced_search
        return advanced_search(pattern)

    def basic_search(self, pattern):
        """Basic search on entries"""
        lookup = None
        for pattern in pattern.split():
            query_part = models.Q(content__icontains=pattern) | \
                         models.Q(excerpt__icontains=pattern) | \
                         models.Q(title__icontains=pattern)
            if lookup is None:
                lookup = query_part
            else:
                lookup |= query_part

        return self.get_query_set().filter(lookup)
