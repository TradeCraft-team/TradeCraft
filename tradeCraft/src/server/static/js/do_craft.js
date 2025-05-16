/*
 * Server needs to handle messages:
 * inward to server:
 *     "request__craft_cache_hands"
 *     "request__craft_recipe_check"
 *     "request__craft_recipe_apply"
 *     "request__craft_done"
 * outward from server:
 *     "respond__craft_recipe_check"
 *     "respond__craft_recipe_apply"
 *     "respond__craft_done"
 *     "server__update_hand"
 */
/*
 * Need external variables: const token, const username, var gamename, var game
 */


class CraftingTable {
    constructor(root) {
        // this.parent = parent;
        this.root = root;
        this.create_crafting_table();
        this.add_button_behaviors();
        this._crafting_history = [];
    }
    create_crafting_table() {
        this.recipe_gui = $('<div id="recipe-gui" class="recipe-gui"></div>');
        this.info_msg = $('<div id="info-msg" class="info-msg"></div>');
        this.input = $('<input type="text" id="crafting-input" placeholder="Type your proposal...">');
        this.help_btn = $("<button class=\"btn btn-success\">Possible Crafts</button>")
            .attr("id", "crafting-help-btn");
        this.check_btn = $("<button class=\"btn btn-primary\">Check</button>")
            .attr("id", "crafting-check-btn");
        this.apply_btn = $("<button class=\"btn btn-primary\" disabled>Apply</button>")
            .attr("id", "crafting-apply-btn");

        // Leave undo not implemented.
        this.undo_btn = $("<button class=\"btn btn-info\">Undo</button>");
        this.undo_btn.attr("id", "crafting-undo-btn");
        this.undo_btn.hide();

        this.done_btn = $(`<button class="btn btn-warning">Done</button>`)
            .attr("id", "crafting-done-btn");
        this.root.append(this.recipe_gui);
        this.root.append(this.info_msg);
        // this.root.append(this.input);


        var btns = $("<div id=\"btns position-relative\"></div>");
        this.root.append(btns);
        btns.append(this.help_btn);
        btns.append(this.check_btn);
        btns.append(this.apply_btn);
        btns.append(this.undo_btn);
        btns.append(this.done_btn);
        // console.log(this.recipe_gui);
        this.add_callbacks();
    }

    request_possible_recipes() {
        socket.emit("player__possible_recipes_from_hand", {
            token: token,
            gamename: gamename,
            is_browser: true
        });
    }

    add_callbacks() {
        socket.on("server__possible_recipes_from_hand", (msg) => {
            if (msg.username != username) return;
            console.log(msg);
            this.recipe_gui.append($("<h4>There are " + msg.recipes.length + " possible crafting recipes:</h4>"));
            for (let i = 0; i < msg.recipes.length; i++) {
                let name = msg.recipes[i];
                var div = $("<div></div>");
                var span = $("<span></span>");
                var span_btn = $("<span></span>");
                var btn = $("<button></button>");
                btn.addClass("btn").addClass("btn-primary")
                    .addClass("select-recipe-btn").text("Craft")
                    .attr("id", name);
                btn.click((e) => {
                    this._select_recipe(e);
                });
                span.append(crafting_panel.generate_recipe_div_before_loading(name, math.fraction(1)));
                span_btn.append(btn);
                div.append(span);
                div.append(span_btn);
                this.recipe_gui.append(div);
            }
        });
        socket.on("server__load_items_from_tag", (msg) => {
            CACHED_CRAFTING_NODES[msg.tag_name] = msg.node;
            this.__generate_tag_input_after_loaded(msg.tag_name, "input");
        });
    }



    add_button_behaviors() {
        this.input.on("input", (e) => {
            this._input(e);
        });
        this.check_btn.click((e) => {
            this._check(e);
        });
        this.apply_btn.click((e) => {
            this._apply(e);
        });
        this.undo_btn.click((e) => {
            this._undo(e);
        });
        this.done_btn.click((e) => {
            this._done(e);
        });
        this.help_btn.click((e) => {
            this._help(e);
        });


        socket.on("server__craft_recipe_validity", (msg) => {
            console.log("CHECK:  ", msg);
            if (msg.result) {
                this.apply_btn.attr("disabled", false);
                var div = $("<div></div>").addClass("alert").addClass("alert-success");
                div.text("Crafting plan " +
                    JSON.stringify(this.current_recipe) +
                    " is valid, click \"Apply\" button to proceed.");
                this.info_msg.empty();
                this.info_msg.append(div);
            } else {
                var div = $("<div></div>").addClass("alert").addClass("alert-danger");
                div.text("Crafting plan " +
                    JSON.stringify(this.current_recipe) +
                    " is invalid. Please correct it and proceed.");
                this.info_msg.empty();
                this.info_msg.append(div);
            }
        });
        socket.on("server__private_hand_change", (msg) => {
            console.log("APPLIED", msg);
            game.players[username].update_hand(msg.hand);
            this.help_btn.attr("disabled", false);
            this.undo_btn.attr("disabled", false);
            // this.apply_btn.attr("disabled", false);
            this.done_btn.attr("disabled", false);
            this.check_btn.attr("disabled", false);

            var div = $("<div></div>").addClass("alert").addClass("alert-info");
            div.text("Crafting plan is applied.");
            this.info_msg.empty();
            this.info_msg.append(div);
        });
    }


    disable_all_btn() {
        this.check_btn.attr("disabled", true);
        this.undo_btn.attr("disabled", true);
        this.apply_btn.attr("disabled", true);
        // this.done_btn.attr("disabled", true);
        this.check_btn.attr("disabled", true);
    }

    _select_recipe(e) {
        var recipe = $(e.target).parent().parent();
        // console.log("RECIPE", $(e.target).attr("id"));
        const recipe_name = $(e.target).attr("id");

        recipe.siblings().remove();

        const recipe_node = CACHED_CRAFTING_NODES[recipe_name];
        var input = $("<div></div>").append("INPUT:");
        var output = $("<div></div>").append("OUTPUT:");
        var amt_bg = $("<div></div>").hide();
        for (let i = 0; i < recipe_node.children.length; i++) {
            var ingredient = recipe_node.children[i][0];
            var amount = input2num(recipe_node.children[i][1]);
            console.log("AMOUNT", recipe_node.children[i][1], amount);
            if (ingredient.slice(0,craft_rule_length) == craft_rule_prefix)
                input.append(this.__generate_item_input(ingredient,
                    "input",
                    amount));
            else {
                input.append(this.__generate_tag_input_before_loaded(ingredient, "input"));
            }
        }
        for (let i = 0; i < recipe_node.parents.length; i++) {
            var out = recipe_node.parents[i][0];
            var amount = input2num(recipe_node.parents[i][1]);
            output.append(this.__generate_item_input(out, "output",
                amount));
        }
        this.recipe_gui.append(amt_bg);
        amt_bg.append(input).append(output);
        amt_bg.slideDown();
    }
    __generate_tag_input_before_loaded(tag_name, role_in_recipe) {
        var bg = $("<div></div>").addClass("border").addClass("border-3")
            .addClass("border-danger").addClass("rounded")
            .addClass("craft-tag-expansion-" +
                mcu.process_name(tag_name).name);
        bg.append($("<div></div>").text("Assign amount of items to make equivalent amount of <strong>" +
                mcu.process_name(tag_name).name + "</strong> meet requirement of recipe.")
            .addClass("alert").addClass("alert-info"));
        if (!(tag_name in CACHED_CRAFTING_NODES)) {
            var load_btn = $("<button class='btn btn-alert'>Load Tag</button>");
            bg.append(load_btn);
            load_btn.click((e) => {
                console.log(tag_name);
                socket.emit("player__load_items_from_tag", {
                    token: token,
                    gamename: gamename,
                    tag_name: tag_name
                });
            });
        } else {
            this.__generate_tag_input_after_loaded(tag_name, role_in_recipe, bg);
        }
        return bg;
    }

    __generate_tag_input_after_loaded(tag_name, role_in_recipe, bg = "") {
        const hand = game.players[username].hand;
        var node = CACHED_CRAFTING_NODES[tag_name];
        console.log(node, tag_name, tag_name in CACHED_CRAFTING_NODES);
        for (let i = 0; i < node.children.length; i++) {
            if (node.children[i][0] in hand) {
                console.log(node.children[i]);
                var amount = input2num(node.children[i][1]);
                if (bg == "") {
                    $(".craft-tag-expansion-" + mcu.process_name(tag_name).name)
                        .append(this.__generate_item_input(node.children[i][0],
                            role_in_recipe, "", [tag_name, amount]));
                } else {
                    bg.append(this.__generate_item_input(node.children[i][0],
                        role_in_recipe, "", [tag_name, amount]));
                }
            }
        }
    }


    __generate_item_input(item_name, role_in_recipe, disabled_with_number = "",
        placeholder = ["", math.fraction(1)]) {
        // if disabled_with_number <= 0, not disabled, otherwise, disable inut and fix it to the value
        var div = $("<div></div>").addClass("input-group");
        var span1 = $("<span></span>").addClass("input-group-text");
        var span2 = $("<span></span>");
        div.append(span1);
        // console.log("ITEM_INPUT", item_name);
        span1.append(crafting_panel.generate_item_div(item_name, math.fraction(1)));
        // span2.
        var ph = "1 * " + item_name + " = " +
            display_number(placeholder[1]) + " * " +
            ((placeholder[0]) ? placeholder[0] : item_name);

        var input = $("<input></input>")
            .attr("id", "craft-amount-" + item_name)
            .attr("role-in-recipe", role_in_recipe)
            .addClass("form-control").addClass("crafting-plan-amount")
            .attr("placeholder", ph)
            .attr("data-bs-toggle", "tooltip").attr("data-bs-title", ph);
        if (disabled_with_number) {
            input.val(disabled_with_number).attr("disabled", true);
        }
        div.append(input);

        return div;
    }

    _help(e) {
        this.recipe_gui.empty();
        this.request_possible_recipes();
    }
    _input(e) {
        console.log(this.recipe_gui);
        // this.recipe_gui.text("INFO:");
        this.apply_btn.attr("disabled", true);
    }

    _check_old(e) {
        try {
            var query = this.input.val();
            this.current_recipe = JSON.parse(query);
        } catch {
            this.info_msg.text("INFO: Failed parsing as JSON. Please correct it and proceed.");
        }

        socket.emit("player__craft_recipe_validity", {
            token: token,
            gamename: gamename,
            recipe: this.current_recipe
        });
    }
    _check(e) {
        const inputs = $(".crafting-plan-amount");
        this.current_recipe = {
            "input": {},
            "output": {}
        };
        for (let i = 0; i < inputs.length; i++) {
            var name = $(inputs[i]).attr("id").substr(13);
            var role = $(inputs[i]).attr("role-in-recipe");
            try {
                var amount = math.fraction($(inputs[i]).val().trim());
            } catch {
                var amount = math.fraction(0);
            }
            if (amount > 0) {
                if (name in this.current_recipe[role]) {
                    this.current_recipe[role][name] += amount;
                } else {
                    this.current_recipe[role][name] = amount;
                }
            }
        }
        console.log(this.current_recipe);
        this.input.val(JSON.stringify(this.current_recipe));
        socket.emit("player__craft_recipe_check", {
            token: token,
            gamename: gamename,
            recipe: this.current_recipe
        });
    }

    _apply(e) {
        // maybe, update this to "check-and-apply" to avoid some extra user effort
        this.disable_all_btn();

        socket.emit("player__craft_recipe_apply", {
            token: token,
            gamename: gamename,
            recipe: this.current_recipe
        });
        for (let item in this.current_recipe.input) {
            this.current_recipe.input[item] = display_number(
                this.current_recipe.input[item]);
        }
        for (let item in this.current_recipe.output) {
            this.current_recipe.output[item] = display_number(
                this.current_recipe.output[item]);
        }
        this._crafting_history.push(Object.assign({}, this.current_recipe));

        this.current_recipe = {};
    }
    _undo(e) {}


    _done(e) {
        this.root.slideUp();
        this.disable_all_btn();
        socket.emit("player__craft_done", {
            token: token,
            gamename: gamename
        });
        game.game_status_bar.updatePhase(7);
        $("#start-crafting-btn").attr("disabled", false);
        $("#send-proposal-btn").attr("disabled", false);
        this.check_btn.attr("disabled", false);

        game.add_chat_message("You", game._mt.crafting_history(this._crafting_history));
        this._crafting_history = [];
    }
    activate() {
        this.root.slideDown();
    }

}




function script_ready() {
    crafting_table = new CraftingTable($("#crafting-table"));
    socket.on("server__update_all_hands", (msg) => {
        game.update_all_hands(msg.hands, msg.player_names);
    });
    $("#crafting-table").hide();

    $("#start-crafting-btn").click((e) => {
        $("#start-crafting-btn").attr("disabled", true);
        $("#send-proposal-btn").attr("disabled", true);
        crafting_table.activate();
    });
}

var crafting_table = {};
