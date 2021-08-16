import {cardToImage, getOtherCards, addImages, get} from "./utils.js";

$(document).ready(function(){

    let info = {game_id: '{{game.game_id}}',
                username: '{{current_user.username}}'};

    let socket = io();
    
    socket.on('connect', () => socket.emit('add to database', info));

    socket.on('update gameboard', (gameboard) => drawGame(gameboard));
    
    socket.on('bid', function(max_bid){
        //startTimer(15, 'pass-bid');
        let radios = [0];
        if (max_bid < 1 ) radios.push(1)
        if (max_bid < 2) radios.push(2)
        radios.push(3)

        radios.forEach(value => {
          $('#bidding')
          .append(`<input type="radio" id="${value}" name="bid" value="${value}">`)
          .append(`<label for="${value}">${value}</label></div>`)
          .append(`<br>`);
        });

        $('#bidding').append('<input id="submit_bid" type="submit" name="submit bid" value="Submit Bid">')

        $('#bidding').show()
        $('#submit_bid').click(function() {
          let bid = $('input[name="bid"]:checked').val();
          socket.emit('submit bid', {info, bid: bid});
          $('#bidding').hide()
        });
    });

    socket.on('make move', function(){
        $("#move_flash").text("It's your move!").css('color', 'red');
        lockCards = false;
        //startTimer(15, 'pass-move'); 
        hand = [];
        discard = [];
        $('#move_stuff').show();
    });

    socket.on('hand over', function(winner){
        setTimeout(() => socket.emit("next hand", info), 300);
    });

    socket.on('flash', (m) => $("#flash").text(m).css('color', 'red'));

    socket.on('flash append', 
        (m) => $("#flash").text($("#flash").text() + ' , ' + m).css('color', 'red'));

    $("#submit_move").click(submitMove);

    $("#pass_move").click(function(){
        hand = [];
        discard = [];
        submitMove();
    });

    function drawGame(gameboard) {
        // GAMEID  section
        $('.gameid').empty()
            .append(
                $('<h3></h3>').text("Game ID: " + gameboard.game_id),
                $('<h3></h3>').text("Current Bid: " + gameboard.bid)
            );
    
        // TITLE section
        $('.title').empty()
            .append($('<h1></h1>').text("Dou Dizhu"))
            .css('font-size', '3rem');
    
        // SCOREBOARD section 
        $('.scoreboard').empty()
            .append('<h2>Scoreboard</h2>', '<ol></ol>');
    
        $('.scoreboard ol').append(
            gameboard.usernames.map(user => 
                "<li>" + user + " : " + get(gameboard.scoreboard, user, 0) + '</li>'
            )
        )
        
        // PLAYER 1 section
        $(".player1").empty().append('<h2>' + gameboard.other_players[0].username + '</h2>');
        let visibleCards = getOtherCards(gameboard.other_players[0]);
        addImages(visibleCards, ".player1");
        
    
        // PLAYER 2 section
        $(".player2").empty().append('<h2>' + gameboard.other_players[1].username + '</h2>');
        visibleCards = getOtherCards(gameboard.other_players[1]);
        addImages(visibleCards, ".player2");
        
        // This player section
        let discard = [], hand = [];
        $(".current-player #cards").empty()
            // .append('<h2>' + "My Hand" + '</h2>')
            // .css('text-align', 'center');
        addImages(gameboard.hand, ".current-player #cards", 20, "my-playing-card");
        $('#bidding').hide();
        $('#move_stuff').hide();
    
    
        $(".my-playing-card").click( function() {
            console.log('clicked')
            if($(this).hasBorder()) {
                $(this).css("border", "");
                hand.pop($(this).attr("id"))
            } else {
                $(this).css("border", "5px solid red");
                hand.push($(this).attr("id")); //something like this 
            }
        });
    
        $(".my-playing-card").dblclick( function() {
            if($(this).hasBorder()) {
                $(this).css("border", "");
                discard.pop($(this).attr("id"))
                }
            else {
                $(this).css("border", "5px solid blue");
                discard.push($(this).attr("id")); //something like this 
            }
        });
    
        $.fn.hasBorder = function() {   
            if ((this.outerWidth() - this.innerWidth() > 0) ||  (this.outerHeight() - this.innerHeight() > 0)){
                    return true;
            } else { return false; }
        };
});


