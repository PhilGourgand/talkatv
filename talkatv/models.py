# talkatv - Commenting backend for static pages
# Copyright (C) 2012  talkatv contributors, see AUTHORS
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import bcrypt

from datetime import datetime

from migrate import changeset
assert changeset  # silence code analysers

from talkatv import db
from talkatv.comment import parse_comment


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), unique=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(60))

    def __init__(self, username, email, password=None, openid=None):
        self.username = username
        self.email = email

        if password:
            self.set_password(password)

        if openid:
            self.openid = openid

    def __repr__(self):
        return '<User {0}>'.format(self.username)

    def set_password(self, password):
        self.password = bcrypt.hashpw(password, bcrypt.gensalt())

    def check_password(self, password):
        return bcrypt.hashpw(password, self.password) == self.password


class OpenID(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String())
    created = db.Column(db.DateTime)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User',
            backref=db.backref('openids', lazy='dynamic'))

    def __init__(self, user, url):
        self.created = datetime.utcnow()
        self.user = user
        self.url = url


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String())
    url = db.Column(db.String(), unique=True)
    created = db.Column(db.DateTime)

    site_id = db.Column(db.Integer, db.ForeignKey('site.id'))
    site = db.relationship('Site',
            backref=db.backref('items', lazy='dynamic'))

    def __init__(self, url, title, site=None):
        if site:
            self.site = site

        self.title = title
        self.url = url

        self.created = datetime.utcnow()

    def __repr__(self):
        return '<Item {0} ({1})>'.format(
                self.url,
                self.site.owner.username if self.site else None)

    def as_dict(self):
        me = {
                'id': self.id,
                'title': self.title,
                'url': self.url,
                'created': self.created.isoformat()}
        if self.site:
            me.update({'owner': self.site.owner.id})

        return me


class Site(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime)
    domain = db.Column(db.String)

    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    owner = db.relationship('User',
            backref=db.backref('sites', lazy='dynamic'))

    def __init__(self, owner, domain):
        self.owner = owner
        self.domain = domain

        self.created = datetime.utcnow()

    def __repr__(self):
        return '<Site {0} ({1})>'.format(
                self.domain,
                self.owner.username)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime)
    text = db.Column(db.String())

    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    item = db.relationship('Item',
            backref=db.backref('comments', lazy='dynamic'))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User',
            backref=db.backref('comments', lazy='dynamic'))

    reply_to_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    reply_to = db.relationship('Comment', remote_side=[id],
            backref=db.backref('replies', lazy='dynamic'))

    def __init__(self, item, user, text, reply_to=None):
        self.item = item
        self.user = user
        self.text = text

        if reply_to:
            if reply_to is int:
                self.reply_to_id = reply_to
            else:
                self.reply_to = reply_to

        self.created = datetime.utcnow()

    def __repr__(self):
        return '<Comment {0} ({1})>'.format(
                self.text[:25] + ('...' if len(self.text) > 25 else ''),
                self.user.username)

    def as_dict(self):
        me = {
                'id': self.id,
                'item': self.item.id,
                'user_id': self.user.id,
                'username': self.user.username,
                'text': self.text,
                'html': parse_comment(self.text),
                'reply_to': self.reply_to_id,
                'created': self.created.isoformat()}
        return me

MODELS = [
        User,
        Comment,
        Item,
        OpenID,
        Site]
