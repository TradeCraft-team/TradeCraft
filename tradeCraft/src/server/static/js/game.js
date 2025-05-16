/*
 * Game
 */

class GameStatusBar {
    /*
        使用说明：
        - 创建 GameStatusBar 实例。
        - 调用 create(root) 方法将状态栏添加到页面的指定容器中。
        - 改变状态请直接改变phase(0-statusList.length)
        - 其他显示变量分别为gameName, playerId, playerOrder, currentPlayerName, currentStateDescription
        - 使用 set_status_list(newStatusList) 方法来更新状态列表。
        - 在游戏状态变化时，更新类的属性，并调用 updateGameInfo() 和 updatePhase() 方法来刷新显示。
      */
    constructor(
        gameName,
        playerId,
        playerOrder,
        currentPlayerName,
        currentStateDescription,
    ) {
        this.gameName = gameName;
        this.playerId = playerId;
        this.playerOrder = playerOrder;
        this.currentPlayerName = currentPlayerName;
        this.currentStateDescription = currentStateDescription;
        this.actionGuide = "Assistant action guide.";
        this.phase = 0;
        this.statusList = [
            "Waiting",
            "Started",
            "Propose",
            "Respond",
            "Crafting",
            "Check",
            "Apply",
            "Craft-done",
        ];
        this.div_object = {};
    }

    _add_callbacks() {
        socket.on("server__game_start", (msg) => {
            this.updatePhase(1);
        });
        socket.on("server__start_proposal", (msg) => {
            this.updatePhase(2);
        });
        socket.on("server__proposal_sent", (msg) => {
            this.updatePhase(3);
        });
        socket.on("server__proposal_accepted", (msg) => {
            this.updatePhase(4);
        });
        socket.on("server__proposal_rejected", (msg) => {
            this.updatePhase(4);
        });
        socket.on("server__possible_recipes_from_hand", (msg) => {
            this.updatePhase(4);
        });
        socket.on("server__craft_recipe_validity", (msg) => {
            this.updatePhase(5);
        });
        socket.on("server__private_hand_change", (msg) => {
            this.updatePhase(6);
        });

    }
    display(root) {
        $(root).empty();
        $(root).append(this.create());
        this.updatePhase(0);
        this._add_callbacks();
    }
    create() {
        if (Object.keys(this.div_object).length > 0) {
            return this.div_object;
        }
        this.div_object = $(`
            <div id="gameStatusBar">
                <div id="gameInfo" class="mb-2">
                    <span id="gameName">Game: ${this.gameName}</span> |
                    <span id="playerId">Player ID: ${this.playerId}</span> |
                    <span id="playerOrder">Order: ${this.playerOrder}</span> |
                    <span id="currentPlayerName">Current Player: ${this.currentPlayerName}</span> |
                    <span id="currentStateDescription">State: ${this.currentStateDescription}</span>
                </div>
                <div id="gameStatus" class="progress-stacked" style="height:30px">
                    ${this.statusList
                      .map(
                        (status, index) => `
                       <div class="progress" role="progressbar" aria-label="Segment ${index}" aria-valuenow="15" aria-valuemin="0" aria-valuemax="100" style="width: ${100 / this.statusList.length}%;height:30px">
                       <div id="game-status-progress-bar-${index}" class="progress-bar">${status}</div>
                       </div>
                    `,
                      )
                      .join("")}
                </div>
                <div id="actionGuide" class="mb-2">
                   Action Guide: ${this.actionGuide}
                </div>
            </div>
        `);
        return this.div_object;
    }

    updateGameInfo() {
        $("#gameName").text(`Game: ${this.gameName}`);
        $("#playerId").text(`I am <strong>${this.playerId}</strong>`);
        $("#playerOrder").text(`Index: ${this.playerOrder}`);
        $("#currentPlayerName").text(`Proposer: ${this.currentPlayerName}`);
        $("#currentStateDescription").text(
            `State: ${this.currentStateDescription}`,
        );
        $("#actionGuide").text(`Action Guide: ${this.actionGuide}`);
    }

    updatePhase(phase = -1) {
        if (phase >= 0) this.phase = phase;
        this.statusList.forEach((status, index) => {
            $(`#game-status-progress-bar-${index}`).attr(
                "class",
                "progress-bar " + this.getBarClass(index),
            );
        });
    }

    set_status_list(statusList) {
        this.statusList = statusList;
        this.updatePhase(this.phase); // Redraw the status bar with new statuses
    }

    getBarClass(index) {
        if (index < this.phase) {
            return "bg-secondary"; // Gray for completed phases
        } else if (index === this.phase) {
            return "bg-success"; // Green for current phase
        } else {
            return "bg-primary"; // Blue for future phases
        }
    }
}

class PlayerTab {
    constructor(
        playername,
        player_role,
        detailed_status,
        hand = {},
        target = {},
    ) {
        this.playername = playername;
        this.player_role = player_role;
        this.detailed_status = detailed_status;
        this.is_self = playername == username;
        this.hand = hand;
        this.target = target;
        this.headerClass = this.is_self ? "border-success" : "border-warning";
        this.div_object = {};
        this.is_trade_target = false;
        this.is_active = false;
        this.is_shown = false;
    }
    display(root) {
        if (
            Object.keys(this.div_object).length === 0 &&
            this.div_object.constructor === Object
        ) {
            // this.is_shown = true;
            return root.append(this.create());
        }
        return root.append(this.div_object);
    }

    show_win(is_win, target) {
        this.div_object.addClass(is_win ? "bg-success" : "bg-danger");
        this.div_object.detailed_status.text(is_win ? "WIN" : "LOSE");
        this.update_target(target);
    }
    create() {
        // should be called only once.
        this.div_object = $(`<div class="card mb3 border-4" ></div>`)
            .addClass(this.headerClass)
            .addClass("bg-light");

        // [TODO] clean the initialization logic
        var tradeButtonClass =
            typeof game_status !== "undefined" && game_status === 2 && !this.is_self ?
            "btn-primary" :
            "btn-primary";

        var headerHtml = `
            <div class="card-header container ${this.headerClass}" style="width:100%">
                <span>${this.playername} - </span>
                <span id="player-tab-info-${this.playername}">
                    ${this.player_role} - ${this.detailed_status}
                </span>
                <button class="btn ${tradeButtonClass} player-tab-trade-button float-right" disabled="" id="player-tab-trade-button-${this.playername}">trade with</button>
            </div>
        `;

        this.div_object.append(headerHtml);
        this.$handSection = $(`<div class="card-body"></div>`);
        this.$targetSection = $('<div class="card-footer">Your Target:</div>');

        this.update_hand(this.hand);
        this.update_target(this.target);

        this.div_object //.append($('<div class="row"></div>')
            .append(this.$handSection)
            .append(this.$targetSection);
        // this._add_callbacks();
        return this.div_object;
    }
    _add_callbacks() {
        console.log("ADDING CALLBACKS");

        $(`#player-tab-trade-button-${this.playername}`).click((e) => {
            console.log(`#player-tab-trade-button-${this.playername}`);
            game.status["trading_partner"] = this.playername;
            this.show_trading_input();
            for (let name in game.players) {
                if (name != this.playername && name != username) {
                    game.players[name].hide_trading_input();
                }
            }
        });
    }

    show_trading_input() {
        $(`.trading-input-${this.playername}`).css("display", "inline");
        $(`.trading-input-group-${this.playername}`).show();
    }
    hide_trading_input() {
        $(`.trading-input-group-${this.playername}`).hide();
    }

    generate_item_set(item_set) {
        var root = $("<div></div>");
        Object.keys(item_set).forEach((item) => {
            var input_group = $(
                `<span class="container" style="display:inline;"></span>`,
            );
            root.append(input_group);
            const item_display = crafting_panel.generate_item_div(
                item,
                item_set[item],
                24,
            );
            input_group.append(
                $(`<span class="" style="display:inline;"></span>`).append(
                    item_display,
                ),
            );
            var trading_input =
                $(`<input type="text" class="form-control trading-input-${this.playername} trading-input-group-${this.playername}"
                                        placeholder="0" aria-label="0"
                                        style="height=100%;width:10%;display:none;">
                                   </input>`);
            input_group.append(trading_input);
        });
        if (username != this.playername) {
            root.append(`<div class="input-group trading-input-group-${this.playername}"  style="display:none;">
                             <span class="input-group-text">Message to ${this.playername}:</span>
                             <textarea class="form-control trading-input-${this.playername}"
                                       aria-label="With textarea" style="width:100%;"></textarea>
                         </div>`);
        }

        return root;
    }
    update_info(info) {
        if (info.player_role !== undefined) this.player_role = info.player_role;
        if (info.detailed_status !== undefined)
            this.detailed_status = info.detailed_status;
        $(`#player-tab-info-${this.playername}`).text(
            `${this.player_role} - ${this.detailed_status} `,
        );
    }

    update_hand(hand) {
        this.hand = hand;
        this.$handSection.empty();
        this.$handSection.append($(`<div>Hand:</div>`));
        this.$handSection.append(this.generate_item_set(hand));
    }

    update_target(target) {
        this.target = target;
        this.$targetSection.empty();
        this.$targetSection.append($(`<span>Target: </span>`));
        Object.keys(target).forEach((item) => {
            const item_display = crafting_panel.generate_item_div(
                item,
                target[item],
                24,
            );
            this.$targetSection.append(item_display);
        });
        if (target.length == 0) {
            this.$targetSection.append($(`<span>UNKNOWN:</span>`));
        }
    }
}
class MessageTranslator {
    constructor() {}

    proposal(msg) {
        var p = msg.proposal;
        return `<div>Proposer: ${p["self"]}, Partner: ${p.partner}</div>
                <div>Proposer Give: ${mcu.stringify_item_set(p.offer)}</div>
                <div>Partner Give: ${mcu.stringify_item_set(p.request)}</div>
                <div>Message: ${msg.message}</div>`;
    }
    rejected(msg) {
        return `A proposal from ${msg.proposer} was rejected.`;
    }
    reason(r){
        if (r=="win"){
            return "someone wins";
        }
        return r;
    }
    game_over(msg) {
        var ret = `Game is over because of <b>${msg.reason}</b>. The winners are: `;
        for (let p in msg["win-status"]) {
            if (msg["win-status"][p]) {
                ret += `<span class="text-bg-danger"> ${p} </span>`;
            }
        }
        return ret;
    }
    crafting_history(history) {
        // Move stringification of recipe into MineCraftUtils module
        var ret = "You Crafted:";
        for (let i = 0; i < history.length; i++) {
            var input = this._stringify_item_set(history[i].input);
            var output = this._stringify_item_set(history[i].output);
            ret += `<div>${input.substr(0, input.length)} => ${output}</div>`;
        }
        return ret;
    }
    _stringify_item_set(item_set) {
        var ret = "";
        for (let item in item_set) {
            ret += `${mcu.process_name(item)[0]} * ${display_number(item_set[item])} + `;
        }
        return ret.substr(0, ret.length - 2);
    }
    player_enter_room(msg) {
        return `Player ${msg.playername} entered the room`;
    }
    player_leave_room(msg) {
        return `Player ${msg.playername} left the room`;
    }
    hands_updated(msg) {
        return `Players' hand status has been changed`;
    }
    private_start_info(msg) {
        return `Your private target is ${Object.keys(msg.target)[0]}.`;
    }
    game_start(msg) {
        return `The game begins.`;
    }
    start_proposal(msg) {
        return `Player <b>${msg.proposer}</b>'s turn to propose.`;
    }
    /* proposal(msg) {
        var offer = this._stringify_item_set(msg.proposal.offer);
        var request = this._stringify_item_set(msg.proposal.request);
        return `Proposer ${msg.proposal.self} gives (${offer}). Need (${request}) from ${msg.proposal.partner}`;
    } */

}

const default_msg_translator = new MessageTranslator();

class Game {
    constructor(root, mt = default_msg_translator) {
        this.root = root;
        this.action_queue = [];
        this.players = {};
        this.player_div = {};
        this.status = {};
        this.chat_messages = [];
        this._mt = mt;
        this.modals = {};
        this.modal_divs = {};
        this._create_modals();
    }
    ready() {
        this.game_status_bar = new GameStatusBar(
            gamename,
            username,
            "",
            "",
            "Game not loaded.",
        );
        this._create_main_board();
        this._create_crafting_wiki();
        this._create_status_panel();
        this._create_ctrl_panel();
        crafting_panel = new CraftingPanel(this.craft_region_body);
        // crafting_panel.show_self();
        crafting_panel.ready();
        crafting_table = new CraftingTable(this.craft_table_root);

        this._add_callbacks();
    }

    _generate_modal_contents(info,extra_foot="") {
        return `<div class="modal fade" id="modal-${info.id}" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="exampleModalLabel">${info.title}</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body">
        ${info.text}
      </div>
      <div class="modal-footer">
        ${extra_foot}
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
      </div>
    </div>
  </div>
</div>`;
    }
    _create_modals() {
        this.modal_divs["game_over"] = $(
            this._generate_modal_contents({
                id: "game_over",
                title: "Game Over!",
                text: "The game is over! Please check further info in game before you exit.",
            }),
        );
        this.modal_divs["void"] = $(
            this._generate_modal_contents({
                id: "void",
                title: "Test",
                text: "Test."
            }),
        );

        this.modal_divs["proposal_invalid"] = $(
            this._generate_modal_contents({
                id: "proposal_invalid",
                title: "Proposal Invalid",
                text: "Your proposal is invalid, please check and re-propose.",
            }),
        );

        this.modal_divs["quit_game"] = $(
            this._generate_modal_contents({
                id: "quit_game",
                title: "Quit Game",
                text: `Click "Quit" to end and quit game.`,
            }, `<button type="button" class="btn btn-danger" id="real-quit">Quit!</button>`),
        );
        this.modal_divs["void_trading_partner"] = $(
            this._generate_modal_contents({
                id: "void_trading_partner",
                title: "Trading Partner Unassigned",
                text: `Please click the "trade with" button of the player you want to trade with.`
            })
        );
        for (let key in this.modal_divs) {
            $("body").append(this.modal_divs[key]);
            this.modals[key] = new bootstrap.Modal(this.modal_divs[key]);
        }
    }
    _create_main_board() {
        // main board structure
        this.root.empty();
        this.game_bg = $("<div></div>")
            .addClass("row")
            .addClass("no-gutters")
            .addClass("align-items-start")
            .css("height", "100%");
        this.status_panel = $("<div></div>")
            .attr("id", "status-panel")
            .css("height", "80vh")
            .css("overflow-y", "auto")
            .addClass("col-md-6");
        this.ctrl_panel = $("<div></div>")
            .attr("id", "ctrl-panel")
            .css("height", "80vh")
            .css("overflow-y", "auto")
            .addClass("col-md-6");
        this.root.append(this.game_bg);
        this.game_bg.append(this.status_panel);
        this.game_bg.append(this.ctrl_panel);
        // this.status_panel.append($("<h1>Please wait for other players...</h1>"));
        // this.ctrl_panel.append($("<h1>Please wait for other players...</h1>"));
    }

    _create_status_panel() {
        this.game_status_bar.display(this.status_panel);
        this.player_div = $(`<div></div>`);
        this.status_panel.append(this.player_div);
    }

    _create_ctrl_panel() {
        this.ctrl_panel.empty();
        this.chat_box = $(`<div id="chat-box" class="chat-box border-3"></div>`);

        this.ctrl_panel.append($(`<h4 class="position-relative">Game Messages</h4>`)
                               .append($(`<button id="quit" class="btn btn-danger position-absolute top-0 end-0">Quit Game</button>`)));
        this.ctrl_panel.append(this.chat_box);
        this.trading_table = $(`<div></div>`);
        this.ctrl_panel.append(this.trading_table);
        // proposal region base
        this.proposal_region = $(`<div class="container proposal-table"></div>`);
        this.trading_table.append(this.proposal_region);

        // proposal display items.
        this.proposal_proposer = $(`<span id="proposal-proposer"></span>`);
        this.proposal_partner = $(`<span id="proposal-partner"></span>`).addClass(
            "proposal-info",
        );
        this.proposal_offer = $(`<span id="proposal-offer"></span>`).addClass(
            "proposal-info",
        );
        this.proposal_request = $(`<span id="proposal-request"></span>`).addClass(
            "proposal-info",
        );
        this.proposal_message = $(`<span id="proposal-message"></span>`).addClass(
            "proposal-info",
        );
        this.proposal_reply_msg = $(
                `<textarea id="proposal-reply" aria-label="With textarea" ></textarea>`,
            )
            .addClass("proposal-info")
            .addClass("form-control")
            .css("width", "100%;");

        // buttons
        this.preview_proposal_btn = $(
            `<button class="btn btn-primary proposal-table">Preview Proposal</button>`,
        );
        this.submit_proposal_btn = $(
            `<button class="btn btn-primary proposal-table">Submit Proposal</button>`,
        );

        this.proposal_approve_btn = $(
            `<button class="btn btn-success proposal-table proposal-response">Approve Proposal</button>`,
        );
        this.proposal_reject_btn = $(
            `<button class="btn btn-danger proposal-table proposal-response">Reject Proposal</button>`,
        );

        // Organize them
        this.proposal_region.append(
            $(`<div>`)
            .append(`<span>Proposer: </span>`)
            .append(this.proposal_proposer),
        );
        this.proposal_region.append(
            $(`<div>`).append(`<span>Partner: </span>`).append(this.proposal_partner),
        );
        this.proposal_region.append(
            $(`<div>`)
            .append(`<span>Proposer Gives: </span>`)
            .append(this.proposal_offer),
        );
        this.proposal_region.append(
            $(`<div>`)
            .append(`<span>Proposer Wants: </span>`)
            .append(this.proposal_request),
        );
        this.proposal_region.append(
            $(`<div>`)
            .append(`<span>Proposer's Message: </span>`)
            .append(this.proposal_message),
        );

        this.proposal_region.append(
            $(`<div  class="proposal-table proposal-response">`)
            .append(`<span>Reply to Proposer: </span>`)
            .append(this.proposal_reply_msg),
        );
        this.proposal_region.append(this.preview_proposal_btn);
        this.proposal_region.append(this.submit_proposal_btn);
        this.proposal_region.append(this.proposal_approve_btn);
        this.proposal_region.append(this.proposal_reject_btn);

        this.craft_table_root = $("<div>", {
            id: "craft_table_root"
        }).hide();
        this.ctrl_panel.append(this.craft_table_root);

        $(".proposal-table").hide();
    }

    _create_crafting_wiki() {
        this.craft_wiki_a = $("<a></a>")
            .attr("id", "craft-wiki-btn")
            .attr("data-bs-toggle", "offcanvas")
            .attr("data-bs-target", "#offcanvas-craft-wiki")
            .attr("aria-controls", "offcanvasWithBothOptions")
            .addClass("nav-link")
            .text("Craft Help");
        this.craft_region = $("<div>", {
                "data-bs-scroll": "true",
                tabindex: "-1",
                id: "offcanvas-craft-wiki",
                "aria-labelledby": "offcanvasWithBothOptionsLabel",
            })
            .addClass("offcanvas")
            .addClass("offcanvas-end")
            .css("width", "45%");
        this.root.append(this.craft_region);
        this.craft_region_header = $("<div>", {
                class: "offcanvas-header"
            })
            .append(
                $("<h5>", {
                    class: "offcanvas-title",
                    id: "offcanvas-craft-wiki-title",
                }).text("TradeCraft WIKI Page"),
            )
            .append(
                $("<button>", {
                    type: "button",
                    class: "btn-close",
                    "data-bs-dismiss": "offcanvas",
                    "aria-label": "Close",
                }),
            );
        this.craft_region_body = $("<div>", {
            class: "offcanvas-body",
            id: "craft-wiki",
        });
        this.craft_region.append(this.craft_region_header);
        this.craft_region.append(this.craft_region_body);

        var $li = $("<li>", {
            class: "nav-item"
        });
        $li.append(this.craft_wiki_a);
        $("#navbar-btns").append($li);
    }

    _add_callbacks() {
        socket.on("server__player_enter_room", (msg) => {
            console.log("server__player_enter_room processed");
            if (msg.playername == username){
                if (msg.type == "Game"){
                    socket.emit("player__ready_to_start",
                                {"username":username, token:token, gamename:msg.gamename});
                    this.show_game();
                    // [GLOBAL]
                    craft_rule_choice = msg.craft_rule_choice;
                    craft_rule_prefix = `${msg.craft_rule_prefix}:`;
                    craft_rule_length = craft_rule_prefix.length;
                }else if (msg.type == "MainEntry"){
                    entry.show_hall();
                }

            }
            if (this.status["is_game_on"]) {
                this.add_chat_message("System",
                    this._mt.player_enter_room(msg) + " The game moves on.");
                return;
            }
            if (msg.type != "Game") {
                return;
            }
            var playername = msg.playername;
            this.player_list = msg.player_list;
            var player_list = msg.player_list;
            this.players[playername] = new PlayerTab(playername, "unknown", "Idle");
            this.display_players(player_list);
            this.add_chat_message("System", this._mt.player_enter_room(msg));
        });
        socket.on("server__player_leave_room", (msg) => {
            console.log("server__player_leave_room processed");
            if (this.status["is_game_on"]) {
                this.add_chat_message("System",
                    this._mt.player_leave_room(msg) + " Waiting for reconnection.");
                return;
            }
            if (msg.type != "Game") {
                return;
            }
            var playername = msg.playername;
            this.player_list = msg.player_list;
            var player_list = msg.player_list;
            this.players[playername] = {};
            this.display_players(player_list);
            this.add_chat_message("System", this._mt.player_leave_room(msg));
        });
        socket.on("server__update_all_hands", (msg) => {
            console.log("server__update_all_hands processed");
            var hands = msg.hands;
            for (let i = 0; i < this.player_list.length; i++) {
                this.players[this.player_list[i]].update_hand(hands[i]);
            }
            this.add_chat_message("System", this._mt.hands_updated(msg));
        });
        socket.on("server__private_start_info", (msg) => {
            console.log("server__private_start_info processed");
            // assert(msg.username == this.player_list[msg.index])
            // unless server__start_game is processed before this.
            this.players[msg.username].update_target(msg.target);
            this.add_chat_message("System", this._mt.private_start_info(msg));
        });
        socket.on("server__game_start", (msg) => {
            console.log("server__game_start processed");
            gamename = msg.gamename;
            this.status["is_game_on"] = true;
            entry.hall_bg.hide();
            game.show_game();
            var player_list = msg.player_list;
            if (JSON.stringify(player_list) != JSON.stringify(this.player_list)) {
                this.player_list = player_list;
            }
            for (let i = 0; i < this.player_list.length; i++) {
                var player = this.players[this.player_list[i]];
                player.player_role = i;
            }
            this.add_chat_message("System", this._mt.game_start(msg));
            this.display_players(player_list);
        });

        socket.on("server__start_proposal", (msg) => {
            // [TODO] some pop-up messagebox. All the detailed status change.
            console.log("server__start_proposal processed");
            this.game_status_bar.currentStateDescription = `Turn ${msg.turn_index} of ${msg.max_turn}`;
            this.game_status_bar.updateGameInfo();
            this.status["proposer"] = msg.proposer;
            this.players[msg.proposer].update_info({
                detailed_status: "Proposing"
            });
            this.add_chat_message("System", this._mt.start_proposal(msg));

            if (msg.proposer == username) {
                // console.log(this.players, this.players[msg.proposer]);
                this.make_proposal();
                this.preview_proposal_btn.show();
                this.proposal_region.show();
            }
        });
        socket.on("server__proposal_sent", (msg) => {
            $(".proposal-table").hide();
            $(".proposal-info").empty();
            $(".player-tab-trade-button").prop("disabled", true);
            if (username == msg.proposer) {
                for (let player in this.players)
                    this.players[player].hide_trading_input();
                this.add_chat_message("You", "My proposal: " + this._mt.proposal(
                    this.current_proposal
                ));
            }
            this.add_chat_message(
                "System",
                "Proposer has sent the proposal, waiting for reply.",
            );
            this.status.trading_partner = undefined;
        });

        socket.on("server__proposal_invalid", (msg) => {
            // pop-up alert box.
            this.modals.proposal_invalid.show();
        });

        socket.on("server__player_craft_done", (msg) => {
            this.players[msg.username].update_info({
                detailed_status: "Finished Crafting."
            });
            this.add_chat_message("System", `Player ${msg.username} has finished crafting.`);
        });


        socket.on("server__proposal", (msg) => {
            this.proposal_region.show();
            this.display_proposal_preview(msg);
            $(".proposal-response").show();
            this.status["proposal_reply"] = true;
            this.add_chat_message(`${msg.proposal.self}`, this._mt.proposal(msg));
        });

        socket.on("server__proposal_accepted", (msg) => {
            this.add_chat_message(
                "System",
                "Proposal Accepted:" + this._mt.proposal(msg),
            );
            this.start_crafting();
        });
        socket.on("server__proposal_rejected", (msg) => {
            this.add_chat_message("System", this._mt.rejected(msg));
            this.start_crafting();
        });

        socket.on("server__proposal_reply_message", (msg) => {
            this.add_chat_message(msg.from, "Replied on Proposal:" + msg.message);
        });

        socket.on("server__game_over", (msg) => {
            this.add_chat_message("System", this._mt.game_over(msg));
            for (let i = 0; i < this.players.length; i++) {
                this.players[i].update_target(msg.targets[i]);
            }
            this.status["is_game_over"] = true;
            this.status["is_game_on"] = false;
            this.modals.game_over.show();
        });

        this.preview_proposal_btn.click((e) => {
            if (this.status.proposer != username || !this.status.is_game_on) {
                return;
            }
            if (this.status.trading_partner == undefined){
                this.modals.void_trading_partner.show();
            }
            var trading_partner = this.status.trading_partner;
            // proposer = username;
            var offer_spec = this.read_item_picking_spec(username);
            var request_spec = this.read_item_picking_spec(trading_partner);
            var message = request_spec.message;
            delete request_spec.message;
            this.status["proposal_previewed"] = true;
            this.current_proposal = {
                token: token,
                gamename: gamename,
                proposal: {
                    self: username,
                    partner: trading_partner,
                    offer: offer_spec,
                    request: request_spec,
                },
                message: message,
            };
            this.display_proposal_preview(this.current_proposal);
            this.submit_proposal_btn.show();
        });
        this.submit_proposal_btn.click((e) => {
            if (!this.status["proposal_previewed"]) return;
            socket.emit("player__submit_proposal", this.current_proposal);
            this.status["proposal_previewed"] = false;
        });
        this.proposal_approve_btn.click((e) => {
            this.send_approval_or_reject("accept");
        });
        this.proposal_reject_btn.click((e) => {
            this.send_approval_or_reject("reject");
        });

        $("#quit").click((e)=>{
            this.modals.quit_game.show();
        });
        $("#real-quit").click((e)=>{
            socket.emit("player__quit_game", {token:token,gamename:gamename});
            this.modals.quit_game.hide();
            this.hide_game();
        });

    }

    start_crafting() {
        crafting_table.activate();
    }

    send_approval_or_reject(decision) {
        if (!this.status.proposal_reply) {
            return;
        }
        const msg = this.proposal_reply_msg.val();
        socket.emit("player__approval_or_reject", {
            token: token,
            gamename: gamename,
            decision: decision,
            message: msg,
        });
        this.add_chat_message(username, `Decision:${decision}\nMsg:${msg}`);
        $(".proposal-table").hide();
        this.status.proposal_reply = false;
    }

    read_item_picking_spec(name) {
        var raw = $(`.trading-input-${name}`).map((x, v) => {
            return $(v).val();
        });
        var keys = Object.keys(this.players[name].hand);
        keys.push("message");
        var ret = {};
        for (let ii = 0; ii < raw.length; ii++) {
            if (keys[ii] != "message") {
                console.log(keys[ii], raw[ii]);
                if (raw[ii] && Number(raw[ii]) > 0) {
                    console.log(keys[ii], raw[ii]);
                    ret[keys[ii]] = Number(raw[ii]);
                }
            } else {
                ret[keys[ii]] = raw[ii];
            }
        }
        console.log(ret);
        return ret;
    }

    display_players(player_list = []) {
        this.player_div.empty();
        console.log("TEST DISPLAY PLAYERS", this.players, player_list);
        for (let i = 0; i < player_list.length; i++) {
            if (!(player_list[i] in this.players)) {
                this.players[player_list[i]] = new PlayerTab(player_list[i], i, "Idle");
            }
            this.players[player_list[i]].player_role = i;
            this.players[player_list[i]].display(this.player_div);
            this.players[player_list[i]]._add_callbacks();
        }
    }
    display_proposal_preview(p) {
        this.proposal_message.text(p.message);
        this.proposal_proposer.text(p.proposal.self);
        this.proposal_partner.text(p.proposal.partner);
        this.proposal_request.text(mcu.stringify_item_set(p.proposal.request));
        this.proposal_offer.text(mcu.stringify_item_set(p.proposal.offer));
    }
    make_proposal() {
        for (let playername in this.players) {
            console.log(playername, username);
            let btn = $(`#player-tab-trade-button-${playername}`);
            if (playername != username) {
                btn.prop("disabled", false);
            } else {
                this.players[username].show_trading_input();
            }
        }
    }

    show_game() {
        entry.hall_bg.hide();
        this.root.show();
        this.chat_box.empty();
        $(".proposal-table").hide();
    }
    hide_game() {
        entry.hall_bg.show();
        this.root.hide();
    }
    add_chat_message(playername, msg, prepend=false) {
        var is_self = playername == username;
        var name = is_self ? "You" : playername;
        var bubble_color = is_self ? "#c1ffcd" : "#c1d0cd";
        // var role = (is_self)?"chat-self":"chat-other";
        var align = is_self ? "align-items-end" : "align-items-start";
        this.chat_messages.push([playername, msg]);
        let messageHtml = `
          <div class="chat-message d-flex flex-column ${align}">
            <div class="chat-name d-flex flex-column ${align}">${name}</div>
            <div class="chat-bubble " style="background-color: ${bubble_color};">${msg}</div>
          </div>
        `;
        if (prepend){
            $("#chat-box").prepend(messageHtml);
        }else{
            $("#chat-box").append(messageHtml);
        }
        $("#chat-box").scrollTop($("#chat-box")[0].scrollHeight);
    }
}

var game = {};
