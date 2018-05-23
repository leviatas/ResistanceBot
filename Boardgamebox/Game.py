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
			if (self.playerlist[uid].afiliacion == "Espia" and not self.playerlist[uid].rol == "Espia Ciego") or self.playerlist[uid].rol == "Pretendiente":
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
			if self.playerlist[uid].afiliacion == "Espia" and not self.playerlist[uid].rol == "Encubierto": 
				espias.append(self.playerlist[uid])
		return espias
	
	def get_comandantes(self):
		espias = []
		for uid in self.playerlist:
			if self.playerlist[uid].rol in ("Comandante", "Comandante Falso"): 
				espias.append(self.playerlist[uid])
		return espias
	
	def jugador_con_carta(self, nombre_carta):
		result = False
		for uid in self.playerlist:
			if nombre_carta in self.playerlist[uid].cartas_trama:
				return True
		return result
	
	def get_creadores_de_opinion(self):
		creador_de_opinion = []
		for uid in self.playerlist:
			if self.playerlist[uid].creador_de_opinion:
				creador_de_opinion.append(self.playerlist[uid])
		return creador_de_opinion
	
	def get_jefes_resistencia(self):
		jefes = []
		for uid in self.playerlist:
			if self.playerlist[uid].rol in ("Jefe Resistencia", "Jefe Resistencia 2"): 
				jefes.append(self.playerlist[uid])
		return jefes
	
	def get_coordinador(self):
		coordinador = []
		for uid in self.playerlist:
			if self.playerlist[uid].rol == "Coordinador": 
				coordinador.append(self.playerlist[uid])
		return coordinador
	
	def get_cazador_resistencia(self):
		for uid in self.playerlist:
			if self.playerlist[uid].rol == "Cazador Resistencia":
				return self.playerlist[uid]
			
	def get_cazador_espia(self):
		for uid in self.playerlist:
			if self.playerlist[uid].rol == "Cazador Espia":
				return self.playerlist[uid]
