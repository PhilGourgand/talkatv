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

from flask import request, json, abort, g

from talkatv import app, db
from talkatv.decorators import require_active_login
from talkatv.models import Item, Comment, User
from talkatv.tools.cors import jsonify, allow_all_origins


@app.route('/api/comments', methods=['GET', 'POST', 'OPTIONS'])
@require_active_login(['POST'])
def api_comments():
    if request.method == 'POST':
        post_data = json.loads(request.data)

        item = Item.query.filter_by(id=post_data['item']).first()

        if not item:
            return abort(404)

        user = User.query.filter_by(id=g.user.id).first()

        if not user:
            return abort(400)

        comment = Comment(item, user, post_data['comment'])
        db.session.add(comment)
        db.session.commit()

        app.logger.debug(request.data)

        return jsonify(status='OK', _allow_origin_cb=allow_all_origins)

    item = Item.query.filter_by(url=request.args.get('item_url')).first()

    if not item:
        title = request.args.get('item_title')
        url = request.args.get('item_url')

        item = Item(url, title)
        db.session.add(item)
        db.session.commit()

    return_data = {
            'item': item.as_dict(),
            'comments': [
                i.as_dict() for i in \
                        item.comments.order_by(
                            Comment.created.desc()).all()],
            'comment_count': item.comments.count()}

    if g.user:
        return_data.update({'logged_in_as': g.user.username})

    app.logger.debug(return_data)

    return jsonify(_allow_origin_cb=allow_all_origins,
            **return_data)


@app.route('/api/check-login')
def check_login():
    if g.user:
        return jsonify(status='OK', _allow_origin_cb=allow_all_origins)
    else:
        return jsonify(status=False, _allow_origin_cb=allow_all_origins)