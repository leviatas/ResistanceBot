import json
from datetime import datetime
from random import shuffle

from Boardgamebox.Player import Player
from Boardgamebox.Board import Board
from Boardgamebox.State import State

class Game(object):
	def __init__(self, cid, initiator):
		self.playerlist = {}
		self.player_sequence = []
		self.cid = cid
		self.board = None
		self.initiator = initiator
		self.dateinitvote = None
		self.history = []
		self.hiddenhistory = []
		self.modulos = []
		self.is_debugging = False
    
    
	def add_player(self, uid, player):
		self.playerlist[uid] = player

	def get_asesino(self):
		for uid in self.playerlist:
			if self.playerlist[uid].rol == "Asesino":
				return self.playerlist[uid]
	def get_goodguys(self):
		resistencia = []
		for uid in self.playerlist:
			if self.playerlist[uid].afiliacion == "Resistencia":
				resistencia.append(self.playerlist[uid])
		return resistencia

	def get_badguys(self):
		espias = []
		for uid in self.playerlist:
			if self.playerlist[uid].afiliacion == "Espia":
				espias.append(self.playerlist[uid])
		return espias

	def shuffle_player_sequence(self):
		for uid in self.playerlist:
			self.player_sequence.append(self.playerlist[uid])
		shuffle(self.player_sequence)

	def remove_from_player_sequence(self, Player):
		for p in self.player_sequence:
			if p.uid == Player.uid:
				p.remove(Player)

	def print_roles(self):
		rtext = ""
		if self.board is None:
			#game was not started yet
			return rtext
		else:
			for p in self.playerlist:
				rtext += "El rol secreto de %s" % (self.playerlist[p].name)
				if self.playerlist[p].esta_muerto:
					rtext += "(muerto) "
				rtext += " era %s (%s)\n" % (self.playerlist[p].rol, self.playerlist[p].afiliacion)
			return rtext

	def encode_all(obj):
		if isinstance(obj, Player):
			return obj.__dict__
		if isinstance(obj, Board):
			return obj.__dict__            
		return obj
    
	def jsonify(self):
		return json.dumps(self.__dict__, default= encode_all)
    
	def get_equipo_actual(self, con_markup):
		miembros_elegidos = ""
		if con_markup:
			for player in self.board.state.equipo:
				miembros_elegidos += "[%s](tg://user?id=%d)\n" % (player.name, player.uid)
		else:
			for player in self.board.state.equipo:
				miembros_elegidos += "%s\n" % (player.name)
		return miembros_elegidos
	
	def get_equipo_actual_flat(self, con_markup):
		miembros_elegidos = ""
		if con_markup:
			for player in self.board.state.equipo:
				miembros_elegidos += "[%s](tg://user?id=%d) " % (player.name, player.uid)
		else:
			for player in self.board.state.equipo:
				miembros_elegidos += "%s - " % (player.name)
		miembros_elegidos = miembros_elegidos[:-3]
		return miembros_elegidos
	
	def get_badguys2(self):
		espias = []
		for uid in self.playerlist:
			if self.playerlist[uid].afiliacion == "Espia" and self.playerlist[uid].rol not "Encubierto": 
				espias.append(self.playerlist[uid])
		return espias
	
	def get_comandante(self):
		espias = []
		for uid in self.playerlist:
			if self.playerlist[uid].rol in ("Comandante", "Comandante Falso"): 
				espias.append(self.playerlist[uid])
		return espias
	
