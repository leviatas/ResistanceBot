from Constants.Cards import playerSets
from Constants.Cards import modules
import random
from Boardgamebox.State import State

class Board(object):
    def __init__(self, playercount, game):
        self.state = State()
        self.num_players = playercount
        self.misiones = playerSets[self.num_players]["misiones"]
        
        # Si hay cartas de trama las incluyo
        if "Trama" in game.modulos:
            tempdeck = modules["Trama"]["plot"]["5"]
            if self.num_players > 6:
                tempdeck += modules["Trama"]["plot"]["7"]            
            self.cartastrama = random.sample(tempdeck, len(tempdeck))
            
        self.discards = []
        self.previous = []
    def print_board(self, player_sequence):
        board = "--- Misiones ---\n"
        
        for i in range(5):
            # Pongo la cantidad de miembros por mision como primera fila
            # pongo un espacio extra luego de 4 porque esta el * de mision en casod e mas de 6 jugadores
            if i == 3 and self.num_players > 6:
                board += " " + str(i+1) + "    "
            else:        
                board += " " + str(i+1) + "   "            
            
        board += "\n"
        
        for i in range(5):
            # Pongo la cantidad de miembros por mision como primera fila
            board += " " + self.misiones[i].replace('*', '\*') + "   " #X
        board += "\n"
        
        # Seguimiento de misiones
        
        for resultado in self.state.resultado_misiones :
            if resultado == "Exito":
                board += u"\u2714\uFE0F" + " " #dove
            else:
                board += u"\u2716\uFE0F" + "  " #X          
             
        board += "\n--- Contador de elección ---\n"
        
        for i in range(5):
            if i < self.state.failed_votes:
                board += u"\u2716\uFE0F" + " " #X
            else:
                board += u"\u25FB\uFE0F" + " " #empty
        
        
        board += "\n--- Orden de turno  ---\n"
        
        for index, player in enumerate(player_sequence):
            if self.state.player_counter == index:
                board += "*" + player.name + "*" + " " + u"\u27A1\uFE0F" + " "
            else:
                board += player.name + " " + u"\u27A1\uFE0F" + " "
        board = board[:-3]
        board += u"\U0001F501"
               
        return board
