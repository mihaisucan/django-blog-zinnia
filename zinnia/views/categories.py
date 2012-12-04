"""Views for Zinnia categories"""
from django.shortcuts import get_object_or_404
from django.views.generic.list_detail import object_list

from zinnia.models import Category
from zinnia.settings import PAGINATION
from zinnia.views.decorators import template_name_for_entry_queryset_filtered
from menus.utils import set_language_changer
from django.utils.translation import get_language
from django.http import Http404


def get_category_or_404(path):
    """Retrieve a Category by a path"""
    path_bits = [p for p in path.split('/') if p]
    slug = path_bits[-1]

    # Try current language
    slug_field = "slug_%s" % get_language()
    get_kwargs = {
        slug_field: slug,
    }

    try:
        cat = get_object_or_404(Category, **get_kwargs)
    except Http404:
        # Use the default language
        del get_kwargs[slug_field]
        get_kwargs['slug'] = slug
        cat = get_object_or_404(Category, **get_kwargs)

    return cat


def category_detail(request, path, page=None, **kwargs):
    """Display the entries of a category"""
    extra_context = kwargs.pop('extra_context', {})

    category = get_category_or_404(path)
    if not kwargs.get('template_name'):
        kwargs['template_name'] = template_name_for_entry_queryset_filtered(
            'category', category.slug)

    extra_context.update({'category': category})
    kwargs['extra_context'] = extra_context
    set_language_changer(request, category.get_absolute_url)
    return object_list(request, queryset=category.entries_published(),
                       paginate_by=PAGINATION, page=page,
                       **kwargs)
