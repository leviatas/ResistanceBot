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
            board += " " + self.misiones[i] + "   " #X
        board += "\n"
        # Seguimiento de misiones
        for resultado in self.state.resultado_misiones :
            if resultado == "Exito":
                board += "😀" + " " #dove
            else:
                board += "😀" + "  " #X          
        
        board += "\n--- Contador de elección ---\n"
        for i in range(5):
            if i < self.state.failed_votes:
                board += "😀" + " " #X
            else:
                board += "😀" + " " #empty

        board += "\n--- Orden de turno  ---\n"
        for index, player in enumerate(player_sequence):
            if self.state.player_counter == index:
                board += "<b>" + player.name + "</b>" + " " + "😀" + " "
            else:
                board += player.name + " " + "😀" + " "
        board = board[:-3]
        board += "😀"
        
        '''
        if self.state.fascist_track >= 3:
            board += "\n\n" + u"\u203C\uFE0F" + " Cuidado: Si Hitler es elegido como Canciller los fascistas ganan el juego! " + u"\u203C\uFE0F"
        if len(self.state.not_hitlers) > 0:
            board += "\n\nSabemos que los siguientes jugadores no son Hitler porque fueron elegidos Canciller despues de 3 politicas fascistas:\n"
            for nh in self.state.not_hitlers:
                board += nh.name + ", "
            board = board[:-2]
        '''
        return board
