import json
import logging as log
import datetime
#import ast
import jsonpickle
import os
import psycopg2
import urllib.parse

	
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import (CallbackContext)

import MainController
import GamesController
from Constants.Config import STATS
from Constants.Cards import modules
from Boardgamebox.Board import Board
from Boardgamebox.Game import Game
from Boardgamebox.Player import Player
from Boardgamebox.State import State
from Constants.Config import ADMIN
from collections import namedtuple
from datetime import datetime
from datetime import timedelta
# Enable logging

log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log.INFO)
logger = log.getLogger(__name__)

#DB Connection I made a Haroku Postgres database first
urllib.parse.uses_netloc.append("postgres")
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])

conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

commands = [  # command description used in the "help" command
    '/help - Te da informacion de los comandos disponibles',
    '/start - Da un poco de información sobre La Resistencia',
    '/symbols - Te muestra todos los símbolos posibles en el tablero',
    '/rules - Te da un link al sitio oficial con las reglas de Secret Hitler',
    '/newgame - Crea un nuevo juego o carga un juego previo',
    '/join - Te une a un juego existente',
    '/startgame - Comienza un juego existente cuantodo todos los jugadores se han unido',
    '/cancelgame - Cancela un juego existente, todos los datos son borrados.',
    '/board - Imprime el tablero actual con la pista liberal y la pista fascista, orden presidencial y contador de elección',
    '/history - Imprime el historial del juego actual',
    '/votes - Imprime quien ha votado',
    '/calltovote - Avisa a los jugadores que se tiene que votar'    
]

symbols = [
	u"\u2714\uFE0F" + ' Mision exitosa',
	u"\u2716\uFE0F" + ' Mision fallida',
]

cards = ["*Creador De Opinión Permanente* - El jugador a quién el Líder pase esta carta, debe seleccionar y revelar su token de Voto antes de que cualquier jugador seleccione su Voto. El efecto de esta carta permanece hasta el fin de la partida. Si dos 'Creadores de opinión' están en juego, los 2 jugadores mostrarán sus votos simultámente.",
	 "*Lider Fuerte 1-Uso* - El jugador a quién el Líder pase esta carta, puede convertirse en Líder. El uso de esta carta debe ser anunciado antes de que el Líder realice alguna acción (robar las cartas de Complot o distribuir las cartas de Equipo). Cuando se juegue un 'Líder Fuerte', otro 'Líder Fuerte' no puede ser jugado hasta realizar una Votación.",
	 "*Vigilancia Estrecha 1-Uso* - El jugador a quién el Líder pase esta carta, puede usarla para examinar una carta de Misión jugada. Usar esta carta no requiere que un jugador anuncie su uso antes de que las cartas de Misión se jueguen, y no afecta a la carta de Misión jugada. Multiples cartas de Misión pueden ser comprobadas en una sóla ronda, pero no más de un jugador puede comprobar la misma carta en una ronda.",
	 "*Asumir Responsabilidad 1-Uso* - El jugador a quién el Líder pase esta carta, debe coger una carta de Complot de otro jugador.",
	 "*En El Punto De Mira 1-Uso* - El jugador a quién el Líder pase esta carta, puede usarla para forzar a un jugador a jugar su carta de Misión boca arriba. El jugador que juegue esta carta debe anunciar su uso y el jugador objetivo antes de que cualquier jugador en el equipo de Misión seleccione su carta de Misión.",
	 "*Sin confianza 1-Uso* - El jugador a quién el Líder pase esta carta, debe usar esta carta para rechazar un equipo de Misión aprobado (Votación aprobada). Usar esta carta cuenta como un Votación fallida.",
	 "*Comunicación Intervenida Inmediata* - El jugador a quién el Líder pase esta carta, debe mirar la carta de Personaje de un jugador adyacente.",
	 "*Compartir Opinión Inmediata* - El jugador a quién el Líder pase esta carta, debe pasar su carta de Personaje a otro jugador (incluido el Líder) para examinarla.",
	 "*Establecer Confianza Inmediata* - El lider debe pasar su carta de Personaje al jugador que reciba esta carta."
]

def command_symbols(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	symbol_text = "Los siguientes símbolos aparecen en el tablero: \n"
	for i in symbols:
		symbol_text += i + "\n"
	bot.send_message(cid, symbol_text)

def command_cartas(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	card_text = "Las siguientes cartas pueden aparecer al lider: \n"
	for i in cards:
		card_text += i + "\n"
	bot.send_message(cid, card_text, ParseMode.MARKDOWN)

def command_board(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	game = get_game(cid)
	if game:
		if game.board:			
			bot.send_message(cid, game.board.print_board(game.player_sequence), ParseMode.MARKDOWN)
		else:
			bot.send_message(cid, "No hay juego comenzado en este chat.  Por favor comience el juego con /startgame")
	else:
		bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")

def command_start(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	bot.send_message(cid,"Bot del juego de mesa La Resistencia.")
	command_help(update, context)


def command_rules(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	btn = [[InlineKeyboardButton("Rules", url="https://en.wikipedia.org/wiki/The_Resistance_(game)")]]
	rulesMarkup = InlineKeyboardMarkup(btn)
	bot.send_message(cid, "Lee las reglas oficiales de Resistencia:", reply_markup=rulesMarkup)


# pings the bot
def command_ping(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	bot.send_message(cid, 'pong - v0.3')


# prints statistics, only ADMIN
def command_stats(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	if cid == ADMIN:
		with open(STATS, 'r') as f:
			stats = json.load(f)
		stattext = "+++ Statistics +++\n" + \
					"Liberal Wins (policies): " + str(stats.get("libwin_policies")) + "\n" + \
					"Liberal Wins (killed Hitler): " + str(stats.get("libwin_kill")) + "\n" + \
					"Fascist Wins (policies): " + str(stats.get("fascwin_policies")) + "\n" + \
					"Fascist Wins (Hitler chancellor): " + str(stats.get("fascwin_hitler")) + "\n" + \
					"Games cancelled: " + str(stats.get("cancelled")) + "\n\n" + \
					"Total amount of groups: " + str(len(stats.get("groups"))) + "\n" + \
					"Games running right now: "
		bot.send_message(cid, stattext)       


# help page
def command_help(update: Update, context: CallbackContext):
	bot = context.bot
	cid = update.message.chat_id
	help_text = "Los siguientes comandos están disponibles:\n"
	for i in commands:
		help_text += i + "\n"
	bot.send_message(cid, help_text)

def reload_game(bot, game, cid):
	GamesController.games[cid] = game
	bot.send_message(cid, "Hay un juego comenzado en este chat. Si quieres terminarlo escribe /cancelgame!")				
	
	# Si el juego no ha comenzado todavia...
	if not game.board:
		return	
	
	# Ask the president to choose a chancellor	
	if game.board.state.fase_actual == "votacion_del_equipo_de_mision":
		bot.send_message(cid, game.board.print_board(game.player_sequence), ParseMode.MARKDOWN)		
		if len(game.board.state.last_votes) == len(game.player_sequence):
			MainController.count_votes(bot, game)
		else:
			MainController.vote(bot, game)
			bot.send_message(cid, "Hay una votación en progreso utiliza /calltovote para decirles a los otros jugadores. ")
	else:
		if game.board.state.fase_actual == "conducir_la_mision":
			bot.send_message(cid, game.board.print_board(game.player_sequence), ParseMode.MARKDOWN)	
			MainController.voting_aftermath(bot, game, True)
		elif game.board.state.fase_actual == "asignar_equipo":			
			bot.send_message(cid, game.board.print_board(game.player_sequence), ParseMode.MARKDOWN)	
			MainController.asignar_equipo(bot, game)
		elif game.board.state.fase_actual == "vote_creadores_opinion":
			bot.send_message(cid, game.board.print_board(game.player_sequence), ParseMode.MARKDOWN)
			MainController.vote_creadores_opinion(bot, game)
		else:
			MainController.start_round(bot, game)

def command_newgame(update: Update, context: CallbackContext):  
	bot = context.bot
	cid = update.message.chat_id
		
	try:
		game = GamesController.games.get(cid, None)
		groupType = update.message.chat.type
		if groupType not in ['group', 'supergroup']:
			bot.send_message(cid, "Tienes que agregarme a un grupo primero y escribir /newgame allá!")
		elif game:
			bot.send_message(cid, "Hay un juego comenzado en este chat. Si quieres terminarlo escribe /cancelgame!")
		else:
			
			#Search game in DB
			game = load_game(cid)			
			if game:
				reload_game(bot, game, cid)
			else:				
				GamesController.games[cid] = Game(cid, update.message.from_user.id)
				bot.send_message(cid, "Nuevo juego creado! Cada jugador debe unirse al juego con el comando /join.\nEl iniciador del juego (o el administrador) pueden unirse tambien y escribir /startgame cuando todos se hayan unido al juego!")
				bot.send_message(cid, "Comenzamos eligiendo los modulos a incluir")
				MainController.configurar_partida(bot, GamesController.games[cid])
			
			
	except Exception as e:
		bot.send_message(cid, str(e))


def command_join(update: Update, context: CallbackContext):
	# I use args for testing. // Remove after?
	groupName = update.message.chat.title
	bot = context.bot
	args = context.args
	cid = update.message.chat_id
	groupType = update.message.chat.type
	game = GamesController.games.get(cid, None)
	if len(args) <= 0:
		# if not args, use normal behaviour
		fname = update.message.from_user.first_name
		uid = update.message.from_user.id
	else:
		uid = update.message.from_user.id
		if uid == ADMIN:
			for i,k in zip(args[0::2], args[1::2]):
				fname = i
				uid = int(k)
				player = Player(fname, uid)
				game.add_player(uid, player)
				log.info("%s (%d) joined a game in %d" % (fname, uid, game.cid))
	
	if groupType not in ['group', 'supergroup']:
		bot.send_message(cid, "Tienes que agregarme a un grupo primero y escribir /newgame allá!")
	elif not game:
		bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")
	elif game.board:
		bot.send_message(cid, "El juego ha comenzado. Por favor espera el proximo juego!")
	elif uid in game.playerlist:
		bot.send_message(game.cid, "Ya te has unido al juego, %s!" % fname)
	elif len(game.playerlist) >= 10:
		bot.send_message(game.cid, "Han llegado al maximo de jugadores. Por favor comiencen el juego con /startgame!")
	else:
		#uid = update.message.from_user.id
		player = Player(fname, uid)
		try:
			#Commented to dont disturb player during testing uncomment in production
			bot.send_message(uid, "Te has unido a un juego en %s. Pronto te dire cual es tu rol secreto." % groupName)			 
			game.add_player(uid, player)
			log.info("%s (%d) joined a game in %d" % (fname, uid, game.cid))
			if len(game.playerlist) > 4:
				bot.send_message(game.cid, fname + " se ha unido al juego. Escribe /startgame si este es el último jugador y quieren comenzar con %d jugadores!" % len(game.playerlist))
			elif len(game.playerlist) == 1:
				bot.send_message(game.cid, "%s se ha unido al juego. Hay %d jugador en el juego y se necesita 5-10 jugadores." % (fname, len(game.playerlist)))
			else:
				bot.send_message(game.cid, "%s se ha unido al juego. Hay %d jugadores en el juego y se necesita 5-10 jugadores" % (fname, len(game.playerlist)))
			# Luego dicto los jugadores que se han unido
			jugadoresActuales = "Los jugadores que se han unido al momento son:\n"
			for uid in game.playerlist:
				jugadoresActuales += "%s\n" % game.playerlist[uid].name
			bot.send_message(game.cid, jugadoresActuales)
			save_game(cid, "Game in join state", game)
		except Exception:
			bot.send_message(game.cid,
				fname + ", No te puedo enviar un mensaje privado. Por favor, ve a @LaResistenciaByLevibot y has pincha \"Start\".\nLuego necesitas escribir /join de nuevo.")


def command_startgame(update: Update, context: CallbackContext):
	log.info('command_startgame called')
	groupName = update.message.chat.title
	bot = context.bot
	cid = update.message.chat_id
	game = GamesController.games.get(cid, None)
	if not game:
		bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")
	elif game.board:
		bot.send_message(cid, "El juego ya ha comenzado!")
	elif update.message.from_user.id != game.initiator and bot.getChatMember(cid, update.message.from_user.id).status not in ("administrator", "creator"):
		bot.send_message(game.cid, "Solo el creador del juego or el admisnitrador del grupo pueden comenzar el juego con /startgame")
	elif len(game.playerlist) < 5:
		bot.send_message(game.cid, "No hay suficientes jugadores (min. 5, max. 10). Uneté al juego con /join")
	else:
		player_number = len(game.playerlist)
		MainController.inform_players(bot, game, game.cid, player_number)
		MainController.inform_badguys(bot, game, player_number)
		game.board = Board(player_number, game)
		log.info(game.board)
		log.info("len(games) Command_startgame: " + str(len(GamesController.games)))
		game.shuffle_player_sequence()
		game.board.state.player_counter = 0		
		#group_name = update.message.chat.title
		#bot.send_message(ADMIN, "Game of Secret Hitler started in group %s (%d)" % (group_name, cid))		
		MainController.start_round(bot, game)
		#save_game(cid, groupName, game)

def command_cancelgame(update: Update, context: CallbackContext):
	log.info('command_cancelgame called')
	bot = context.bot
	cid = update.message.chat_id	
	#Always try to delete in DB
	delete_game(cid)
	game = get_game(cid)
	if game:
		status = bot.getChatMember(cid, update.message.from_user.id).status
		if update.message.from_user.id == game.initiator or status in ("administrator", "creator"):
			MainController.end_game(bot, game, 99)
		else:
			bot.send_message(cid, "Solo el creador del juego o el adminsitrador del grupo pueden cancelar el juego con /cancelgame")
	else:
		bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")

def command_votes(update: Update, context: CallbackContext):
	try:
		#Send message of executing command   
		bot = context.bot
		cid = update.message.chat_id
		#bot.send_message(cid, "Looking for history...")
		#Check if there is a current game 
		game = get_game(cid)
		if game:
			if not game.dateinitvote:
				# If date of init vote is null, then the voting didnt start          
				bot.send_message(cid, "La votación no ha comenzado todavia!")
			else:
				#If there is a time, compare it and send history of votes.
				start = game.dateinitvote
				stop = datetime.now()
				elapsed = stop - start
				if elapsed > timedelta(minutes=5):
					history_text = "Historial de votacion para el Presidente %s y Canciller %s:\n\n" % (game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name)
					for player in game.player_sequence:
						# If the player is in the last_votes (He voted), mark him as he registered a vote
						if player.uid in game.board.state.last_votes:
							history_text += "%s ha votado.\n" % (game.playerlist[player.uid].name)
						else:
							history_text += "%s no ha votado.\n" % (game.playerlist[player.uid].name)
					bot.send_message(cid, history_text)
				else:
					bot.send_message(cid, "Cinco minutos deben pasar para ver los votos") 
		else:
			bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")
	except Exception as e:
		bot.send_message(cid, str(e))

def command_calltovote(update: Update, context: CallbackContext):
	try:
		#Send message of executing command   
		bot = context.bot
		cid = update.message.chat_id
		#bot.send_message(cid, "Looking for history...")
		#Check if there is a current game
		game = get_game(cid)
		if game:
			if not game.dateinitvote:
				# If date of init vote is null, then the voting didnt start          
				bot.send_message(cid, "La votación no ha comenzado todavia!")
			else:
				#If there is a time, compare it and send history of votes.
				# start = game.dateinitvote
				# stop = datetime.now()          
				# elapsed = stop - start
				# if elapsed > timedelta(minutes=1):
					# Only remember to vote to players that are still in the game
				history_text = ""
				if game.board.state.fase_actual == "votacion_del_equipo_de_mision":
					for player in game.player_sequence:
						# If the player is not in last_votes send him reminder
						if player.uid not in game.board.state.last_votes:
							history_text += "Es hora de votar [%s](tg://user?id=%d)!\n" % (game.playerlist[player.uid].name, player.uid)
				else:
					for player in game.board.state.equipo:
						# If the player is not in last_votes send him reminder
						if player.uid not in game.board.state.votos_mision:
							history_text += "Debe votar la misión [%s](tg://user?id=%d)!\n" % (game.playerlist[player.uid].name, player.uid)
					
				bot.send_message(cid, text=history_text, parse_mode=ParseMode.MARKDOWN)
				# else:
				# 	bot.send_message(cid, "Cinco minutos deben pasar para pedir que se vote!") 
		else:
			bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")
	except Exception as e:
		bot.send_message(cid, str(e))
        
def command_showhistory(update: Update, context: CallbackContext):
	#game.pedrote = 3
	try:
		#Send message of executing command   
		bot = context.bot
		cid = update.message.chat_id
		#Check if there is a current game
		game = get_game(cid)
		if game:		
			#bot.send_message(cid, "Current round: " + str(game.board.state.currentround + 1))
			uid = update.message.from_user.id
			history_text = "Historial:\n\n" 
			history_textContinue = "" 
			for x in game.history:
				if len(history_text) < 3500:
					history_text += x + "\n\n"
				else:
					history_textContinue += x + "\n\n"

			bot.send_message(uid, history_text, ParseMode.MARKDOWN)
			if len(history_textContinue) > 0:
				bot.send_message(uid, history_textContinue, ParseMode.MARKDOWN)
			#bot.send_message(cid, "I sent you the history to our private chat")			
		else:
			bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")
	except Exception as e:
		bot.send_message(cid, str(e))
		log.error("Unknown error: " + str(e))  

def command_showmodulos(update: Update, context: CallbackContext):
	#game.pedrote = 3
	try:
		#Send message of executing command   
		bot = context.bot
		cid = update.message.chat_id
		#Check if there is a current game
		game = get_game(cid)
		if game:
			modulos_incluidos = ""
			for modulo in game.modulos:
				modulos_incluidos += f"*{modulo}*: {modules[modulo]['descripcion']}\n"
			bot.send_message(cid, f"Los modulos incluidos en este juego son:\n{modulos_incluidos}", ParseMode.MARKDOWN)	
		else:
			bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")
	except Exception as e:
		bot.send_message(cid, str(e))
		log.error("Unknown error: " + str(e)) 

def command_claim(update: Update, context: CallbackContext):
	#game.pedrote = 3
	try:
		#Send message of executing command   
		bot = context.bot
		cid = update.message.chat_id
		args = context.args
		#Check if there is a current game
		game = get_game(cid)
		if game:
			uid = update.message.from_user.id		
			if uid in game.playerlist:				
				if game.board.state.currentround != 0:
					if len(args) > 0:
						#Data is being claimed
						claimtext = ' '.join(args)
						claimtexttohistory = "El jugador %s declara: %s" % (game.playerlist[uid].name, claimtext)
						bot.send_message(cid, "Tu declaración: %s fue agregada al historial." % (claimtext))
						game.history.append("*%s*" % (claimtexttohistory))
					else:					
						bot.send_message(cid, "Debes mandar un mensaje para hacer una declaración.")

				else:
					bot.send_message(cid, "No puedes hacer declaraciones en la primera ronda.")
			else:
				bot.send_message(cid, "Debes ser un jugador del partido para declarar algo.")
				
		else:
			bot.send_message(cid, "No hay juego en este chat. Crea un nuevo juego con /newgame")
	except Exception as e:
		bot.send_message(cid, str(e))
		log.error("Unknown error: " + str(e))    
		
def save_game(cid, groupName, game):
	#Check if game is in DB first
	cur = conn.cursor()			
	log.info("Searching Game in DB")
	query = "select * from games where id = %s;"
	cur.execute(query, [cid])
	dbdata = cur.fetchone()
	if cur.rowcount > 0:
		log.info('Updating Game')
		gamejson = jsonpickle.encode(game)
		#query = "UPDATE games SET groupName = %s, data = %s WHERE id = %s RETURNING data;"
		query = "UPDATE games SET groupName = %s, data = %s WHERE id = %s;"
		cur.execute(query, (groupName, gamejson, cid))
		#log.info(cur.fetchone()[0])
		conn.commit()		
	else:
		log.info('Saving Game in DB')
		gamejson = jsonpickle.encode(game)
		query = "INSERT INTO games(id , groupName  , data) VALUES (%s, %s, %s);"
		#query = "INSERT INTO games(id , groupName  , data) VALUES (%s, %s, %s) RETURNING data;"
		cur.execute(query, (cid, groupName, gamejson))
		#log.info(cur.fetchone()[0])
		conn.commit()

def get_game(cid):
	# Busco el juego actual
	game = GamesController.games.get(cid, None)	
	if game:
		# Si esta lo devuelvo.
		return game
	else:
		# Si no esta lo busco en BD y lo pongo en GamesController.games
		game = load_game(cid)
		if game:
			GamesController.games[cid] = game
			return game
		else:
			None

def load_game(cid):
	cur = conn.cursor()			
	log.info("Searching Game in DB")
	query = "SELECT * FROM games WHERE id = %s;"
	cur.execute(query, [cid])
	dbdata = cur.fetchone()

	if cur.rowcount > 0:
		log.info("Game Found")
		jsdata = dbdata[2]
		#log.info("jsdata = %s" % (jsdata))				
		game = jsonpickle.decode(jsdata)
		
		# For some reason the decoding fails when bringing the dict playerlist and it changes it id from int to string.
		# So I have to change it back the ID to int.				
		temp_player_list = {}		
		for uid in game.playerlist:
			temp_player_list[int(uid)] = game.playerlist[uid]
		game.playerlist = temp_player_list
		temp_last_votes = {}	
		temp_votos_mision = {}
		if game.board is not None and game.board.state is not None:
			for uid in game.board.state.last_votes:
				temp_last_votes[int(uid)] = game.board.state.last_votes[uid]
			game.board.state.last_votes = temp_last_votes
			
			temp_espera_accion = {}	
			for uid in game.board.state.enesperadeaccion:
				temp_espera_accion[int(uid)] = game.board.state.enesperadeaccion[uid]
			game.board.state.enesperadeaccion = temp_espera_accion

			for uid in game.board.state.votos_mision:
				temp_votos_mision[int(uid)] = game.board.state.votos_mision[uid]
			game.board.state.votos_mision = temp_votos_mision
		#bot.send_message(cid, game.print_roles())
		return game
	else:
		log.info("Game Not Found")
		return None

def delete_game(cid):
	cur = conn.cursor()
	log.info("Deleting Game in DB")
	query = "DELETE FROM games WHERE id = %s;"
	cur.execute(query, [cid])
	conn.commit()
	
	
#Testing commands
def command_ja(update: Update, context: CallbackContext):
	uid = update.message.from_user.id
	if uid == ADMIN:
		bot = context.bot
		cid = update.message.chat_id
		game = GamesController.games.get(cid, None)
		answer = "Si"
		for uid in game.playerlist:
			game.board.state.last_votes[uid] = answer
		MainController.count_votes(bot, game)
	

def command_nein(update: Update, context: CallbackContext):	
	uid = update.message.from_user.id
	if uid == ADMIN:
		bot = context.bot
		cid = update.message.chat_id
		game = GamesController.games.get(cid, None)
		answer = "No"
		for uid in game.playerlist:
			game.board.state.last_votes[uid] = answer
		MainController.count_votes(bot, game)
		
def command_reloadgame(update: Update, context: CallbackContext):  
	bot = context.bot
	cid = update.message.chat_id
		
	try:
		game = GamesController.games.get(cid, None)
		groupType = update.message.chat.type
		if groupType not in ['group', 'supergroup']:
			bot.send_message(cid, "Tienes que agregarme a un grupo primero y escribir /reloadgame allá!")		
		else:			
			#Search game in DB
			game = load_game(cid)			
			if game:
				reload_game(bot, game, cid)
			else:
				bot.send_message(cid, "No hay juego que recargar, crea un nuevo juego con /newgame")
			
			
	except Exception as e:
		bot.send_message(cid, str(e))
		
def command_toggle_debugging(update: Update, context: CallbackContext):
	uid = update.message.from_user.id
	if uid == ADMIN:
		bot = context.bot
		cid = update.message.chat_id
		game = GamesController.games.get(cid, None)
		# Informo que el modo de debugging ha cambiado
		game.is_debugging = True if not game.is_debugging else False
		bot.send_message(cid, "Debug Mode: ON" if game.is_debugging else "Debug Mode: OFF")
		
def command_prueba(update: Update, context: CallbackContext):
	uid = update.message.from_user.id
	if uid == ADMIN:
		bot = context.bot
		cid = update.message.chat_id
		game = GamesController.games.get(cid, None)
		game.board.state.resultado_misiones.append("Fracaso")
		MainController.start_round(bot, game)
		
		'''sdate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		log.info("Paso la conversion " + sdate)
		surl = "https://www.dropbox.com/s/sy4473ohowipxke/BSGP%20Esperando%20la%20Carroza%20-%20CURRENT.jpg?raw=1&cache=" + sdate
		log.info("URL: " + surl)
		bot.send_photo(cid, photo=surl)
		'''
		#bot.send_photo(cid, photo='https://www.dropbox.com/s/sy4473ohowipxke/BSGP%20Esperando%20la%20Carroza%20-%20CURRENT.jpg?raw=1&cache=%d' % (datetime.now()))
		#bot.send_photo(cid, photo='https://www.dropbox.com/s/sy4473ohowipxke/BSGP%20Esperando%20la%20Carroza%20-%20CURRENT.jpg?raw=1')
		'''game = GamesController.games.get(cid, None)
		
		#game.board.state.failed_votes -= 1
		
		for uid in game.board.state.last_votes:
			bot.send_message(ADMIN, "%s voto, en last votes" % game.playerlist[uid].name)
		
		bot.send_message(ADMIN, "Fase actual: %s" % game.board.state.fase_actual)
		'''
		
		'''
		callback = update.callback_query
		log.info(' '.join(args))
		'''
		'''
		bot = context.bot
		cid = update.message.chat_id
		game = Commands.get_game(cid)
		MainController.final_asesino(bot, game)
		'''

def command_jugadores(update: Update, context: CallbackContext):	
	uid = update.message.from_user.id
	bot = context.bot
	cid = update.message.chat_id
	game = GamesController.games.get(cid, None)
	jugadoresActuales = "Los jugadores que se han unido al momento son:\n"
	for uid in game.playerlist:
		jugadoresActuales += "[%s](tg://user?id=%d)\n" % (game.playerlist[uid].name, uid)
	bot.send_message(game.cid, jugadoresActuales, ParseMode.MARKDOWN)
