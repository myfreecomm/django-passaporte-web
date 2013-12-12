#
# gravatars.py -- Decorational template tags
#
# Copyright (c) 2008-2009  Christian Hammond
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from hashlib import md5

from django import template
from django.conf import settings


register = template.Library()


@register.simple_tag
def gravatar(user, size=24, default="mm", secure=True):
    """
    Outputs the HTML for displaying a user's gravatar.

    This can take an optional size of the image (defaults to 80 if not
    specified).

    This is also influenced by the following settings:

        GRAVATAR_SIZE    - Default size for gravatars
        GRAVATAR_RATING  - Maximum allowed rating (g, pg, r, x)
        GRAVATAR_DEFAULT - Default image set to show if the user hasn't
                           specified a gravatar (identicon, monsterid, wavatar)

    See http://www.gravatar.com/ for more information.
    """
    if not user.email:
        return ""

    email_hash = md5(user.email.lower()).hexdigest()

    if secure:
        url = "https://secure.gravatar.com/avatar/{0}.png".format(email_hash)
    else:
        url = "http://www.gravatar.com/avatar/{0}.png".format(email_hash)

    params = []

    params.append("s={0}".format(size))
    params.append("d={0}".format(default))

    if hasattr(settings, "GRAVATAR_RATING"):
        params.append("r={0}".format(settings.GRAVATAR_RATING))

    url += "?" + "&".join(params)

    username = user.get_full_name() or user.username
    if not isinstance(username, unicode):
        # Grant username is unicode
        username = username.decode('utf-8')

    return u'<img src="{url}" width="{size}" height="{size}" alt="{username}" style="vertical-align: middle;"/>'.format(
            url=url, size=size, username=username)
