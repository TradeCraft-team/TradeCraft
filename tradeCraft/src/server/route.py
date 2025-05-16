"""
Route
"""
import os
from flask import (render_template, request, session, jsonify, send_file,
                   send_from_directory, redirect)
from .app import (app, logger, HALLS, socketio, GAMES, PLAYERS, pr_args,
                  lint_to_simplename)


def check_session_info():
    if 'token' in session:
        pass


@app.route("/")
def root():
    return render_template("index.html")


@app.route("/new/")
def new():
    return render_template("index.html")


@app.route("/test/")
def test():
    session["username"] = "test"
    return render_template("test.html")


@app.route('/login', methods=['POST'])
def login():
    """
    On Client side, io() should be called after recieving
    "success" from login.

    Feature: If accidentally disconnected (status written in 'PLAYERS'), and login to the same
    username anywhere, redirect to the status before disconnection.
    [NOTE] NOT IN USE
    """

    data = request.get_json()

    if not data or 'username' not in data:
        return jsonify({'status': 'error', 'message': 'Invalid request'}), 400

    username = request.json['username']
    session['username'] = username

    hall_list = []
    for rule, hall in HALLS.items():
        hall_list += hall.info()

    return jsonify({
        "status": "success",
        "username": username,
        "hall_list": hall_list
    })


@app.route("/game_tools/", methods=["POST"])
def game_tools():
    """
    Game tools
    """
    error = jsonify({'status': 'error', 'message': 'Invalid request'}), 400
    data = request.get_json()
    gamename = data.get("gamename", "")
    token = data.get("token", "")
    username = data.get("username", "")

    if gamename not in GAMES:
        return error
    game = GAMES.get(gamename)
    if (game.token_to_username.get(token, "~") != username
            or username not in game.players):
        return error

    player = game.players[username]
    match data.get("tool_name"):
        case "craft_wiki":
            return app.json.dumps({})
        case "possible_recipes_from_hand":
            return app.json.dumps(player.on_possible_recipes_from_hand(data))
        case "craft_recipe_check":
            return app.json.dumps(player.on_craft_recipe_check(data))
        case _:
            return error


PATH_ITEM_ICONS = os.path.join("src", pr_args["craft_rule_base_path"],
                               pr_args["craft_rule_choice"], "item_icons/")
ICON_EXT = pr_args["icon_format"]


@app.route("/item_icons/<path:filename>")
def return_static_item_icons(filename):
    """
    Get Icon file by filename without prefix. 
    Note: Do NOT use relative path in `send_from_directory`
    """
    return send_from_directory(os.path.realpath(PATH_ITEM_ICONS),
                               f"{filename}.{ICON_EXT}")


@app.route("/icons/<icon_name>")
def icon_display(icon_name):
    """
    This is supposed not in use.
    """
    if icon_name[0] == "~":  # tags
        png_name = "tag.png"
    elif icon_name[0] == "$":  # recipes
        png_name = "recipe.png"
    else:
        png_name = lint_to_simplename(icon_name) + ".png"
    path = os.path.join(PATH_ITEM_ICONS, png_name)

    return send_file(os.path.realpath(path), as_attachment=False)
