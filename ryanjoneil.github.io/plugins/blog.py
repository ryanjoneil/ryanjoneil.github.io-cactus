from collections import OrderedDict
import os
import datetime
import logging

ORDER = 999
POSTS_PATH = 'posts/'
POSTS = []
CATS = OrderedDict({'Modeling': [], 'Programming': []})
LANGS = OrderedDict({'Python': [], 'R': []})

from django.template import Context
from django.template.loader import get_template
from django.template.loader_tags import BlockNode, ExtendsNode

def getNode(template, context=Context(), name='subject'):
    """
    Get django block contents from a template.
    http://stackoverflow.com/questions/2687173/
    django-how-can-i-get-a-block-from-a-template
    """
    for node in template:
        if isinstance(node, BlockNode) and node.name == name:
            return node.render(context)
        elif isinstance(node, ExtendsNode):
            return getNode(node.nodelist, context, name)
    raise Exception("Node '%s' could not be found in template." % name)


def preBuild(site):

    global POSTS

    # Build all the posts
    for page in site.pages():
        if page.path.startswith(POSTS_PATH):

            # Skip non html posts for obious reasons
            if not page.path.endswith('.html'):
                continue

            # Find a specific defined variable in the page context,
            # and throw a warning if we're missing it.
            def find(name):
                c = page.context()
                if not name in c:
                    logging.info("Missing info '%s' for post %s" % (name, page.path))
                    return ''
                return c.get(name, '')

            # Build a context for each post
            postContext = {}
            postContext['title'] = find('title')
            postContext['author'] = find('author')
            postContext['date'] = find('date')
            postContext['category'] = find('category')
            postContext['lang'] = find('lang')
            postContext['path'] = page.path
            postContext['post'] = getNode(get_template(page.path), name="post")
            postContext['description'] = find('description')

            # Parse the date into a date object
            try:
                postContext['date'] = datetime.datetime.strptime(postContext['date'], '%d-%m-%Y')
            except Exception as e:
                logging.warning("Date format not correct for page %s, should be dd-mm-yy\n%s" % (page.path, e))
                continue

            POSTS.append(postContext)

    # Sort the posts by date
    POSTS = sorted(POSTS, key=lambda x: x['date'])
    POSTS.reverse()

    indexes = xrange(0, len(POSTS))

    for i in indexes:
        if i+1 in indexes: POSTS[i]['prevPost'] = POSTS[i+1]
        if i-1 in indexes: POSTS[i]['nextPost'] = POSTS[i-1]

    # Add them to the category and language dicts
    for post in POSTS:
        if post['category']:
            CATS[post['category']].append(post)
        if post['lang'] in LANGS:
            LANGS[post['lang']].append(post)

def preBuildPage(site, page, context, data):
    """
    Add the list of posts to every page context so we can
    access them from wherever on the site.
    """
    context['posts'] = POSTS
    context['cats'] = CATS
    context['lang_r'] = LANGS['R']
    context['lang_py'] = LANGS['Python']

    for post in POSTS:
        if post['path'] == page.path:
            context.update(post)

    return context, data
