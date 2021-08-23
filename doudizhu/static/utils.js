function get(object, key, default_value) {
  //https://stackoverflow.com/questions/44184794/what-is-the-javascript-equivalent-of-pythons-get-method-for-dictionaries/44185289
  var result = object[key];
  return typeof result !== "undefined" ? result : default_value;
}

let card_to_string = {
  11: "jack",
  12: "queen",
  13: "king",
  14: "1",
  15: "2",
  16: "joker_black",
  17: "joker_red",
  0: "back-black",
};

function cardToImage(card) {
  // Takes a card (int) and gets the card picture
  if ((card == 16) | (card == 17) | (card == 0)) {
    return card_to_string[card] + ".png";
  } else if (card in card_to_string) {
    return card_to_string[card] + ".png";
  } else {
    return card.toString() + ".png";
  }
}

function getOtherCards(data) {
  let cardArr = new Array();
  for (let x = 0; x < data["n_cards"]; x++) {
    if (x < data["visible_cards"].length)
      cardArr.push(data["visible_cards"][x]);
    else cardArr.push(0); // hidden card
  }
  return cardArr;
}

function addImages(arr, jquery, chunk = 7, classname = "playing-card") {
  // Adds images to the jquery, displays every chunk, adds classname to the image
  let temp;
  for (let i = 0; i < arr.length; i += chunk) {
    let temporary = arr.slice(i, i + chunk);
    temp = $('<div class="card-container"></div>');
    temporary.forEach((card, x) => {
      let img = $("<img />");
      img.attr("id", card);
      img.attr("class", classname);
      img.attr("src", "/static/card-images/" + cardToImage(card));
      temp.append(img);
      // if (x % 5 == 0) $(jquery).append('<br>');
    });
    $(jquery).append(temp);
  }
}

function addMove(move, discard, jquery) {
  addImages(move, jquery, (chunk = move.length));
  addImages(discard, jquery, (chunk = move.length));
}
