var gamename = "";
var token = "";
var username= "";
var game_history_messages_missing = false;
var craft_rule_choice = "minecraft";
var craft_rule_prefix = "minecraft:";
var craft_rule_length = 10;

class Entry{
    // Deal with Entry-Hall-Game selection activities
    constructor(root){
        this.hall_bg = root;

        this.hall_region = $(`<div></div>`);
        this.hall_bg.append($("<h1>TradeCraft Halls</h1>"))
            .append($(`<button class="btn btn-primary" id="refresh-main-entry">Refresh Halls</button>`))
            .append(this.hall_region);
    }
    _add_button_callbacks(){
        // The procedure should be different when Hall is fully functioning.
        $("#login-btn").click((e)=>{
            socket.emit("login", {username: $("#username-input").val()});
            // [TODO] Add some "loading" page.
            // game.show_game();
        });
        $("#refresh-main-entry").click((e)=>{
            socket.emit("get_entry_info", {_token:token});
        });
    }
    _add_event_callbacks(){
        socket.on("server__login_success", (msg)=>{
            token = msg.token;
            username = msg.username;
            $("#login-container").hide();
            $("#navbar-bg").show();
            if (msg.status_code == 1){
                game_history_messages_missing = true;
                // [TODO] request for game status. and expect
                // "update_all_hands", "private_start_info"
                // and last state-transition message individually, say
                // "start_proposal", "proposal", "start_crafting".
                // server: goto find them in history.
            }
            else{
                this.show_hall();
            }
        });
        socket.on("server__game_restored", (msg)=>{
            if (!game_history_messages_missing){
                return;
            }
            if (msg.gametype == "Game"){
                game.show_game();
            }
            else if (msg.gametype == "MainEntry"){
                this.show_hall();
            }
        });


        socket.on("server__restored_proof_invalid",
                  (msg)=>{});  // what kind of actions should be undertaken?

        socket.on("server__restored_proof_requested", (msg)=>{
            socket.emit("restored_proof", {_username: username, _token: token});
        });
        socket.on("server__username_conflict", (msg)=>{
            $("#login-info-display").text(msg.message);
        });
        socket.on("server__session_conflict", (msg)=>{
            $("#login-info-display").text(msg.message);
        });

        socket.on("server__player_enter_room",(msg)=>{
            if (msg.type != "Hall"){
                return;
            }
        });
        socket.on("server__entry_info", (msg)=>{
            this.hall_region.empty();
            for (let i=0;i<msg.halls.length; i++){
                let info = msg.halls[i];
                var hallbase = $(`<div id="hall-base-${info[0]}"></div>`)
                    .append(this.generate_hall(info));
                this.hall_region.append(hallbase);
                $(`#hall-refresh-${info[0]}`).click((e)=>{
                    socket.emit("get_hall_info",
                                {_token:token, _hallname:info[0]});
                });
                $(`#hall-enter-${info[0]}`).click((e)=>{
                    socket.emit("enter_hall",
                                {_token:token, _hallname:info[0]});
                });
            }
        });
        socket.on("server__hall_info",(msg)=>{
            let info=msg.general_info;
            $(`#general-${msg.hallname}`).html(`${info[1]}<div>Status:</div>
            <div>${info[2].ongoing_games} ongoing games,<div>
            <div>${info[2].ingame_players} players playing,<div>
            <div>${info[2].available_players} players waiting.<div>`);
        });
        socket.on("disconnect", (msg)=>{
            console.log(msg);
            // socket.io.reconnect();
        });
    }

    generate_hall(info){
        // [TODO] Maybe use Bootstrap v5.3 Accordions.
        var base = $(`<div></div>`);
        var abstract = $(`<div class="card text-bg-secondary" style="width:80%;"></div>`);
        var top = $(`<div class="card-header"><h5>Hall: ${info[0]}</h5></div>`);
        var mid = $(`<div class="card-body" id="general-${info[0]}">${info[1]}<div>Status:</div>
            <div>${info[2].ongoing_games} ongoing games,<div>
            <div>${info[2].ingame_players} players playing,<div>
            <div>${info[2].available_players} players waiting.<div></div>`);
        var bot = $(`<div class="card-footer">
            <button class="btn btn-primary" type="button" data-bs-toggle="collapse" data-bs-target="#hall-${info[0]}" aria-expanded="false" aria-controls="hall-${info[0]}">
                 Details
            </button>
        </div>`);

        var detail = $(`<div class="collapse" id="hall-${info[0]}" style="width:80%;">
                            <div class="card card-body" id="hall-detail-${info[0]}">
                            </div>
                            <div class="card card-footer">
                            <button class="btn btn-primary" id="hall-refresh-${info[0]}" type="button">Refresh Info</button>
                                Enter Hall and Start Matching Opponent(s):
                            <button class="btn btn-primary" id="hall-enter-${info[0]}" type="button">Enter</button>
                            </div>
                        </div>`);
        abstract.append(top).append(mid).append(bot);
        base.append(abstract).append(detail);


        return base;
    }


    show_hall(){
        game.root.hide();
        this.hall_bg.show();

    }
    ready(){
        this._add_event_callbacks();
        this._add_button_callbacks();
    }
}

var entry = {};
var is_test = true;

$(window).ready((e)=>{
    entry = new Entry($("#hall-container"));
    game = new Game($("#game-container"));
    entry.ready();
    game.ready();



    // [DELETE]
    socket.on("server__test_status",(msg)=>{console.log(msg);});

    if(is_test){
    socket.prependAny((eventname, ...args)=>{
        console.log("===>>> INCOMING", eventname, args);
    });
    socket.onAnyOutgoing((eventname, ...args)=>{
        console.log("<<<=== OUTGOING", eventname, args);
    });}
});
