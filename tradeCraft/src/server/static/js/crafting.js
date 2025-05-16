// TODO Please change this in chatting part!
var is_craft_phase = true;
var CACHED_CRAFTING_NODES = {};
var CACHED_RECIPE_DIVS = {};
var CACHED_ITEM_IMGS = {};
var algebra_dummy = false;
function input2num(a){
    switch (a.d){
    case undefined:
        return math.fraction(a[0]) / math.fraction(a[1]);
    default:
        return math.fraction(a);
    }
}
function multiply(a, b){
    if (algebra_dummy){
        console.log(a, b);
        return Number(a)*Number(b);
    }
    return math.multiply(a,b);
}
function display_number(a){
    switch(a.d){
    case 1:
        return a.n;
    case undefined:
        if (a.length == 2){
            return display_number(math.fraction(a[0]) / math.fraction(a[1]));
        }else{
            return a;
        }
    default:
        return `(${a.n} / ${a.d})`;
    }

}


class MineCraftUtils{
    constructor(){}

    cut_mc(s){
        if (s.substr(0,craft_rule_length) === craft_rule_prefix){
            return s.substr(craft_rule_length);
        }
        return s;
    }
    process_name(name){
        var node_type, node_name;
        if (name[0] === "#"){
            node_type = "tag";
            node_name = name.substr(1);
        }
        else if (name[0] === "$"){
            node_type = "recipe";
            node_name = name.substr(1);
        }
        else{
            node_type = "item";
            node_name = name;
        }
        return {name:this.cut_mc(node_name), type:node_type};
    }

    reconstruct_name(node_name, node_type){
        // let's reconstruct only the items and recipes??

        var middle = craft_rule_prefix;
        if (node_name.search(/[0-9]/) >= 0 && node_name.length == 32 && node_type==="tag"){
            middle = "";
            // TODO: change this to a better method to identify self-defined tags (no "minecraft:" as prefix).
        }else if (node_type == "recipe"){
            middle = "";
        }
        var prefix = "";
        if (node_type == "tag") prefix = "#";
        else if (node_type == "recipe") prefix = "$";

        return prefix + middle + node_name;
    }
    icon_name(node_name, node_type){
        // let's reconstruct only the items and recipes??


        if (node_type == "tag") return node_type;
        else if (node_type == "recipe") return node_type;
        return node_name;
    }
    stringify_item_set(item_set){
        var ret = "| ";
        for(let key in item_set){
            if (item_set[key] == 0) continue;
            ret += this.process_name(key).name + " * ";
            ret += display_number(item_set[key]);
            ret += " | ";
        }
        return ret;
    }
}
var mcu = new MineCraftUtils();

function levenshtein(a, b) {
    const matrix = [];
    let i, j;

    if (a.length === 0) return b.length;
    if (b.length === 0) return a.length;

    for (i = 0; i <= b.length; i++) {
        matrix[i] = [i];
    }

    for (j = 0; j <= a.length; j++) {
        matrix[0][j] = j;
    }

    for (i = 1; i <= b.length; i++) {
        for (j = 1; j <= a.length; j++) {
            if (b.charAt(i - 1) === a.charAt(j - 1)) {
                matrix[i][j] = matrix[i - 1][j - 1];
            } else {
                matrix[i][j] = Math.min(
                    matrix[i - 1][j - 1] + 1, // replace
                    Math.min(matrix[i][j - 1] + 1, // insert
                             matrix[i - 1][j] + 1) // delete
                );
            }
        }
    }
    return matrix[b.length][a.length];
}


class CraftingPanel{

    constructor(parent){
        this.parent = parent;
        this.crafting_item_list = [];
        this.icon_size = 48;
        this.loaded_tags = {};
    }
    // [START] structural part of the display region.
    show_self(){
        console.log(this.parent);
        this.bg = this.create_crafting_tag(); // the background
        this.create_search_bar();
        this.create_display_region();
    }

    create_crafting_tag(){
        var crafting_tag = $("<div id='crafting-tag' class='ref-tag'></div>");
        this.parent.empty();
        this.parent.append(crafting_tag);
        return crafting_tag;
    }
    ready(){
        socket.on("server__crafting_item_list", (msg)=>{
            console.log(msg);
            this.crafting_item_list = msg.crafting_item_list.map((t)=>{
                return mcu.process_name(t).name;
            });
            console.log(msg);

            this.show_self();
        });

        socket.on("server__crafting_node", (msg)=>{
            console.log("crafting_node", msg);
            if (msg.username !== username) return 1;
            if (!msg.is_valid) return 2;
            var node = msg.node; // msg.node should be a JSON containing (node_type, node_name, parents, children)
            this.display_node(node);
            CACHED_CRAFTING_NODES[msg.node.node_name] = msg.node;
            return 0;
        });
        socket.on("server__crafting_node_nonredirect", (msg)=>{
            console.log("NONREDIRECT", msg);
            if (msg.username !== username) return 1;
            if (!msg.is_valid) return 2;
            var node = msg.node; // msg.node should be a JSON containing (node_type, node_name, parents, children)

            let raw_amount = input2num(msg.amount);
            if (node.node_type == "tag"){
                this.replace_tag_div_after_loaded(node, raw_amount);
            }else if (node.node_type == "recipe"){
                this.replace_recipe_div_after_loaded(node, raw_amount);
            }else {}
            CACHED_CRAFTING_NODES[msg.node.node_name] = msg.node;
            return 0;
        });
        socket.emit("player__crafting_item_list",
                    {token:token, gamename:gamename});
    }

    create_search_bar(){
        this.input = $('<input type="text" id="autocomplete-input" placeholder="Please input...">');
        this.suggestion = $('<ul id="suggestions-list" class="suggestions-list"></ul>');
        this.bg.append(this.input);
        this.bg.append(this.suggestion);
        this.input.on("input", ()=>{
            const query = this.input.val().toLowerCase();
            this.suggestion.empty();
            if (query) {
                const filteredData = this.get_crafting_item_list().filter((item) => item.toLowerCase().includes(query))
                      .sort((a, b) => levenshtein(a.toLowerCase(), query) - levenshtein(b.toLowerCase(), query))
                      .slice(0, 5);
                filteredData.forEach(item => {
                    this.suggestion.append(`<li>${item}</li>`);
                });
                this.suggestion.show();
            } else {
                this.suggestion.hide();
            }
        });
        this.suggestion.on('click', 'li', (e)=> {

            this.input.val(e.target.outerText);
            this.suggestion.empty().hide();
        });
        this.search_button = $("<button id=\"craft-search-button\" class=\" btn btn-primary\">Search</button>");
        this.bg.append(this.search_button);
        this.search_button.click((e)=>{
            var node_name = this.input.val();
            if (this.crafting_item_list.includes(node_name)){
                this.request_crafting_node(node_name);
            }
        });
    }
    create_display_region(){
        this.display_region = $("<div id=\"display-region\", class=\"region\"></div>");
        this.bg.append(this.display_region);
        console.log(":::: :smile:", "THIS.DISPLAY_REGION");
    }
    // [END] structural part of the display region.

    // [START] data request and process(?)
    request_crafting_node(node_name, node_type="item"){
        console.log(mcu.reconstruct_name(node_name, node_type));
        if (node_name in CACHED_CRAFTING_NODES){
            this.display_node(CACHED_CRAFTING_NODES[node_name]);
        }
        else{
            console.log(mcu.reconstruct_name(node_name, node_type));
            socket.emit("player__crafting_node",
                        {token:token, gamename:gamename,
                         node_name: mcu.reconstruct_name(node_name, node_type)});
        }
    }

    get_crafting_item_list(){
        return this.crafting_item_list;
    }

    // [START] deal with data, like sorting according to current hands.
    sorting_items_dummy(item_list){
        // dummy, sorting the list as is.
        return item_list;
    }


    // [START] displays of recipe / tag / item
    display_node(node){
        this.current_item = node.node_name;
        this.display_region.empty();

        var self = $("<div><h4>The ITEM:</h4></div>");
        this.display_region.append(self);
        this.add_node_tag(node.node_name, [1,1], self, node, true);

        var children = $("<div><h4>The Item Can be Obtained via:</h4></div>");
        this.display_region.append(children);
        for (i=0; i<node.children.length; i++){
            this.add_node_tag(node.children[i][0], node.children[i][1], children, node);
        }

        var parents = $("<div><h4>The Item can be Ingredients for</h4></div>");
        this.display_region.append(parents);
        console.log( "PARENTS", node.parents);
        for (var i=0; i<node.parents.length; i++){
            this.add_node_tag(node.parents[i][0], node.parents[i][1], parents, node);
        }

    }

    replace_recipe_div_after_loaded(recipe_node, amount){
        // after loaded a tag, replace the place-holder by the full-function tag div.
        // amount should be in format of math.fraction
        var recipe = $("#temp-recipe-" + mcu.process_name(recipe_node.node_name).name);
        console.log("REPLACE:", recipe);
        recipe.empty();
        recipe.append(this.generate_recipe_div_from_node(recipe_node, amount));
    }

    generate_recipe_div_before_loading(recipe_name, amount){
        // if the tag is not loaded, then load it.
        // before successfully loaded, leave a place-holder.
        // amount should be in format of math.fraction
        // var tempn_ame = mcu.reconstruct_name(recipe_name, "recipe");
        var temp_name = mcu.process_name(recipe_name).name;
        var div = $("<div></div>").attr("id", "temp-recipe-"+temp_name);

        if (recipe_name in CACHED_CRAFTING_NODES){
            return this.generate_recipe_div_from_node(CACHED_CRAFTING_NODES[recipe_name],
                                                      math.fraction(1));
        }
        console.log("REQUEST_NONDIRECT", recipe_name);
        socket.emit("player__crafting_node_nonredirect",
                    {token:token,
                     gamename:gamename,
                     node_name: recipe_name,
                     amount: amount});
        div.append(this.generate_item_div("recipe", math.fraction(1), this.icon_size,
                                      "loading "+recipe_name+"...", "danger"));
        return div;
    }
    generate_recipe_div_from_node(recipe_node, amount){
        if (false && recipe_node.node_name in CACHED_RECIPE_DIVS)
            return CACHED_RECIPE_DIVS[recipe_node.node_name];
        var div = $("<div></div>");
        div.attr("id", "recipe-" + recipe_node.node_name);
        div.addClass("recipe");

        var c = recipe_node.children;
        for (let i=0; i< c.length; i++){
            if(i){div.append("<span class='operator'> + </span>");}
            let raw_amount = input2num(c[i][1]);
            div.append(this.generate_item_or_tag(c[i][0], multiply(raw_amount, amount)));
            //div.append($("<span>*"+math.format(c[i][1][0])/Number(c[i][1][1])+"</span>"));
        }
        div.append($("<span class='operator'> => </span>"));

        c = recipe_node.parents;
        for (let i=0; i< c.length; i++){
            if(i){div.append("<span class='operator'> + </span>");}
            let raw_amount = input2num(c[i][1]);
            div.append(this.generate_item_or_tag(c[i][0], multiply(raw_amount, amount)));
            // div.append(this.generate_item_img(c[i][0]));
            // div.append($("<span>*"+Number(c[i][1][0])/Number(c[i][1][1])+"</span>"));
        }
        CACHED_RECIPE_DIVS[recipe_node.node_name] = div;
        return div;

    }
    generate_item_or_tag(name, amount){
        // amount should be in format of math.fraction
        if (name[0] == "#"){
            // if it is a tag:
            return this.generate_tag_div_before_loading(name, amount);
        }
        return this.generate_item_div(name, amount, this.icon_size, "");
    }

    replace_tag_div_after_loaded(tag_node, amount){
        // after loaded a tag, replace the place-holder by the full-function tag div.
        // amount should be in format of math.fraction
        var tags = $(".temp-tag-" + mcu.process_name(tag_node.node_name).name);
        console.log(tags);
        for (let i=0; i<tags.length; i++){
            let tag = $(tags[i]);
            tag.empty();
            tag.append(this.generate_tag_div_from_node(tag_node, amount));
        }
    }

    generate_tag_div_before_loading(tag_name, amount){
        // if the tag is not loaded, then load it.
        // before successfully loaded, leave a place-holder.
        // amount should be in format of math.fraction
        var temp_name = mcu.process_name(tag_name).name;
        var div = $("<span></span>").attr("class", "temp-tag-"+temp_name);

        if (tag_name in CACHED_CRAFTING_NODES){
            return this.generate_tag_div_from_node(CACHED_CRAFTING_NODES[tag_name], amount);
        }
        var tag_btn = this.generate_item_div("tag", amount, this.icon_size,
                                             "loading "+tag_name+"...", "danger");
        console.log("NONREDIRECT_BEFORELOADIN", tag_name);
        tag_btn.click((e)=>{
            console.log("[^_^]NONREDIRECT", tag_name);
            socket.emit("player__crafting_node_nonredirect",
                        {token:token,
                         gamename:gamename,
                         node_name: tag_name,
                         amount: amount});
        });
        if (!(tag_name in this.loaded_tags)){
            this.loaded_tags[tag_name] = 1;
            socket.emit("player__crafting_node_nonredirect",
                        {token:token,
                         gamename:gamename,
                         node_name: tag_name,
                         amount: amount});                
        }
        div.append(tag_btn);
        return div;

    }
    generate_tag_div_from_node(tag_node, amount){
        // tag effect: display the first (in some order?)
        // amount should be in format of math.fraction
        var root = $("<span></span>");
        const id=(Math.random() + 1).toString(36).substring(4)+"_";

        const tag_name = mcu.process_name(tag_node.node_name).name;
        root.addClass("dropdown");
        root.addClass("tag_"+tag_name);
        var a = $("<a class='btn btn-success dropdown-toggle dropdown-toggle-split' data-bs-toggle='dropdown' aria-expanded='false'></a>");
        a.attr("id", "tag-a-" + id + tag_name);
        // visualize the tag itself.
        a.append(this.generate_item_div("tag", amount, this.icon_size, tag_name, ""));
        root.append(a);
        var ul = $('<ul class="dropdown-menu"></ul>');
        root.append(ul);
        console.log("<><><>", id);
        for(let i=0; i< tag_node.children.length; i++){
            let child = tag_node.children[i];
            let item_name = mcu.process_name(child[0]).name;
            let inner_li = $('<li></li>');
            let inner_a = $('<a class="dropdown-item" href="#"></a>');
            // console.log(amount, child[1]);
            const new_amount = multiply(amount, input2num(child[1]));
            inner_a.append(this.generate_item_div(item_name, new_amount, this.icon_size, item_name, ""));
            inner_li.append(inner_a);
            ul.append(inner_li);
            inner_a.click((e)=>{
                var base = $("#tag-a-"+id+tag_name);
                base.empty();
                console.log(base);
                base.append(this.generate_item_div(item_name, new_amount, this.icon_size, "", ""));
            });
        }
        root.append(ul);
        return root;
    }

    generate_item_img(name, size=48){
        var img = $(`<img src="/item_icons/${name}"></img>`);
        img.addClass("item-" + name);
        img.attr("height", size);
        return img;
    }
    generate_item_div(name, amount, size=48, display_name="", btn_cls="dark"){
        let midfix = "outline-";
        if (this.current_item == name){
            midfix = "";
        }
        // console.log("GEN_ITEM_DIV:", name, amount);
        name = mcu.process_name(name).name;
        var is_true_item = false;
        if (!display_name){
            display_name = name;
            is_true_item = true;
        }
        var div = $("<div></div>");
        div.addClass("item-" + name);
        div.attr("id", "item-" + name);
        div.append(this.generate_item_img(name, size));
        div.append(" * "+display_number(amount));
        div.append($("<div></div>").text(display_name));
        if (is_true_item){
            div.click((e)=>{this.request_crafting_node(name);});
        }
        if (btn_cls){
            div.addClass('btn');  // test
            div.addClass('btn-' + midfix + btn_cls); // test
        }
        return div;
    }

    add_node_tag(name, amount_frac, base, node, is_self=false){
        var bg = $("<div></div>");
        base.append(bg);
        console.log(name);
        if (name[0] == "$"){
            console.log("RECIPE", name, base, node);
            bg.append(this.generate_recipe_div_before_loading(name, math.fraction(1)));
        }
        else if (name[0] == "#"){
            console.log("TAG", name, base, node);
            return;
            // bg.append(this.generate_tag_div_before_loading(name, math.fraction(1)));
        }else{
            bg.append(this.generate_item_div(name, math.fraction(1), this.icon_size, ""));
        }
        name = mcu.process_name(name);
        /*
        var test = $("<img src=\"/item_icons/"+ mcu.icon_name(name.name, name.type) +".png\" width=\"48\" height=\"48\"></img>");
        bg.append(test);
        var ntype = $("<div></div>");
        ntype.text("Type: "+name.type);
        // bg.append(ntype);
        var nname = $("<button></button>");
        nname.html(name.name);
        // nname.addClass(name.type);
        bg.append(nname);
        */

        bg.attr("id", "bg-"+name.name);
        // bg.addClass("bg-"+name.type);
        /* if (!is_self){
            // load tag when clicked~
            bg.click((e)=>{
                console.log(mcu.reconstruct_name(name.name, name.type));

                socket.emit("request__crafting_node",
                            {username: username,
                             node_name: mcu.reconstruct_name(name.name, name.type)});
            });
        }else */
            if (name.type == "recipe"){
            var tmp = $("<button>Craft!</button>");
            // bg.append(tmp);
            function calc(x){
                var obj = {};
                obj[x[0]]= Number(x[1][0])/Number(x[1][1]);
                return obj;
            }
            tmp.click((e)=>{
                if (is_craft_phase){
                    var recipe = {output:Object.assign({}, ...node.parents.map(calc)),
                                  input: Object.assign({}, ...node.children.map(calc))};

                    try{
                        var original = JSON.parse($("#proposal-input").val());
                    }catch{
                        var original = {input:{}, output:{}};
                    }
                    for (var key in recipe.input){
                        if (key in original.input){
                            original.input[key] += recipe.input[key];
                        }
                        else original.input[key] = recipe.input[key];
                    }
                    for (key in recipe.output){
                        if (key in original.output){
                            original.output[key] += recipe.output[key];
                        }
                        else original.output[key] = recipe.output[key];
                    }
                    console.log(original);
                    $("#crafting-input").val(JSON.stringify(original));
                }
            });
        }

        var amount = $("<div></div>");
        amount.text("Amount: " + (Number(amount_frac[0]) / Number(amount_frac[1])).toString());
        bg.append(amount);
    }


}


// [START] GLOBAL SETTINGS
// $("#login-btn").click((e)=>{$("#game-container").css("display", "grid");});
var crafting_panel = {};
