import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
import sys
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)


db_drop_and_create_all()

# ROUTES

@app.route('/drinks')
def get_drinks():
    all_drinks = Drink.query.all()
    
    drinks = [drink.short() for drink in all_drinks]

    res = {
        'success': True,
        'drinks': drinks
    }

    return jsonify(res), 200


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(jwt):
    try:
        all_drinks = Drink.query.all()
        drinks = [drink.long() for drink in all_drinks]
        res = {
            'success': True,
            'drinks': drinks
        }
        return jsonify(res), 200
    except AuthError:
        abort(401)


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(jwt):
    data = request.get_json()
    title = data['title']
    recipe = data['recipe']

    if type(recipe) is dict:
        recipe = [recipe]

    new_drink = Drink(
        title=title,
        recipe=json.dumps(recipe)
    )
    new_drink.insert()
    res = {
        'success': True,
        'drink': [new_drink.long()]
    }
    return jsonify(res), 200


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(jwt, drink_id):
    data = request.get_json()
    new_title = data.get('title', None)
    new_recipe = data.get('recipe', None)

    drink = Drink.query.filter(Drink.id == drink_id).first()

    if drink is None:
        abort(404)
    
    if new_title:
        drink.title = data['title']
    if new_recipe:
        drink.recipe = data['recipe']

    if new_title or new_recipe:
        drink.update()

    res = {
        'success': True,
        'drinks': [drink.long()]
    }

    return jsonify(res), 200


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, drink_id):
    drink = Drink.query.filter(Drink.id == drink_id).first()

    if drink is None:
        abort(404)

    drink.delete()

    res = {
        'success': True,
        'delete': drink_id
    }

    return jsonify(res), 200


# Error Handling

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 404,
        'message': 'resource not found'
    }), 404


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 401,
        'message': 'unauthorized'
    }), 401


@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        'success': False,
        'error': error.status_code,
        'message': error.error['description']
    }), error.status_code
