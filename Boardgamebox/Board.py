from Constants.Cards import playerSets
import random
from Boardgamebox.State import State

class Board(object):
    def __init__(self, playercount, game):
        self.state = State()
        self.num_players = playercount
        self.misiones = playerSets[self.num_players]["misiones"]
        
        #self.plotcards = random.sample(playerSets[self.num_players]["plot"], len(playerSets[self.num_players]["plot"]))
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
        for player in player_sequence:
            board += player.name + " " + u"\u27A1\uFE0F" + " "
        board = board[:-3]
        board += u"\U0001F501"
        
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
