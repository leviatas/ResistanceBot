from Boardgamebox.Game import Game
from Boardgamebox.Player import Player
from Boardgamebox.Board import Board

juego = Game(12, 13)

player = Player("Maximiliano", 1)
juego.add_player(1, player)
player = Player("Maximiliano", 2)
juego.add_player(2, player)

player_number = len(juego.playerlist)
# juego.board = Board(player_number, juego)

print(any([True for k,v in juego.playerlist.items() if v.name.strip() == 'Maximiliano']))

board = ""
for uid in juego.playerlist:
    board += juego.playerlist[uid].name + " " + u"\u27A1\uFE0F" + " "

print(board)
