#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Leviatas"

import json
import logging as log
import random
import re
import math
from random import randrange
from time import sleep

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import (Updater, CommandHandler, CallbackQueryHandler, CallbackContext)
from telegram.utils.helpers import mention_html

import Commands
from Constants.Cards import playerSets
from Constants.Config import STATS, ADMIN
from Constants.Cards import modules
from Boardgamebox.Game import Game
from Boardgamebox.Player import Player
import GamesController
import datetime

import os
import psycopg2
import urllib.parse

import traceback
import sys

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
'''
cur = conn.cursor()
query = "SELECT ...."
cur.execute(query)
'''

##
#
# Beginning of round
#
##

def start_round(bot, game):
	# Comienzo de nuevo turno se resetea el equipo elegido
	game.board.state.fase_actual = "comienzo_de_ronda"
	game.board.state.equipo = []
	game.board.state.equipo_contador = 0
	game.board.state.votos_mision = {}
	
	# Modulo Cazador Reseteo el investigador
	game.board.state.investigador = None
	game.board.state.investigador_nominado = None
	game.board.state.trigger_fin_temprano = False
	
	# Variables de Trama	
	if "Trama" in game.modulos:
		game.board.state.miembroenelpuntodemira = None
		game.board.state.enesperadeaccion = {}
	
	Commands.save_game(game.cid, "Saved Round %d" % (game.board.state.currentround + 1), game)
	log.info('start_round called')
		
	# Starting a new round makes the current round to go up    
	game.board.state.currentround += 1
	# Si el lider fue elegido por un evento o jugador... El chosen presidente no sera nulo
	log.info(game.board.state.lider_elegido)
	if game.board.state.lider_elegido is None:
		game.board.state.lider_actual = game.player_sequence[game.board.state.player_counter]
	else:
		game.board.state.lider_actual = game.board.state.lider_elegido
		game.board.state.lider_elegido = None
	
	bot.send_message(game.cid, game.board.print_board(game.player_sequence), ParseMode.MARKDOWN)
	bot.send_message(game.cid, "El próximo Lider es [%s](tg://user?id=%d)." % (game.board.state.lider_actual.name, game.board.state.lider_actual.uid), ParseMode.MARKDOWN)
	
	turno_actual = len(game.board.state.resultado_misiones)
	game.history.append("Ronda %d.%d" % (turno_actual +1, game.board.state.failed_votes + 1))
	
	# Si esta el modulo de Trama se reparten cartas de Trama 
	if "Trama" in game.modulos:
		# Solo el primer lider de cada ronda (el juego tiene solo 5) reparte cartas.
		if game.board.state.failed_votes == 0:
			repartir_cartas_trama(bot, game)
			return		
	asignar_equipo(bot, game)
	# --> nominate_chosen_chancellor --> vote --> handle_voting --> count_votes --> voting_aftermath --> draw_policies
	# --> choose_policy --> pass_two_policies --> choose_policy --> enact_policy --> start_round


def asignar_equipo(bot, game):
	log.info(game.board.state.equipo_contador)
	if game.board.state.equipo_contador == 0:
		game.board.state.fase_actual = "asignar_equipo"
		msgtext =  "%s, por favor elige a los miembros que irán a la mision en nuestro chat privado!" % (game.board.state.lider_actual.name)
		bot.send_message(game.cid, msgtext, ParseMode.MARKDOWN)
		Commands.save_game(game.cid, "Saved Round %d" % (game.board.state.currentround), game)	
	turno_actual = len(game.board.state.resultado_misiones)
	log.info('asignar_equipo called')
	strcid = str(game.cid)
	pres_uid = 0
	chan_uid = 0
	btns = []
		
	# Inicialmente se puede elegir a cualquiera para formar los equipos
	# Menos los que esten en el equipo elegido
	for uid in game.playerlist:
		if game.playerlist[uid] not in game.board.state.equipo:
			name = game.playerlist[uid].name
			btns.append([InlineKeyboardButton(name, callback_data=strcid + "_equipo_" + str(uid))])
	
	equipoMarkup = InlineKeyboardMarkup(btns)
	
	log.info("Este es la mision: %d" % (turno_actual + 1))
	
	if "*" not in game.board.misiones[turno_actual]: 
		game.board.state.equipo_cantidad_mision = int(game.board.misiones[turno_actual])
	else:
		game.board.state.equipo_cantidad_mision = int((game.board.misiones[turno_actual])[:-1])
	
	# En la mision trampero se agrega siempre un miembro extra al equipo.
	if "Trampero" in game.modulos:
		game.board.state.equipo_cantidad_mision += 1
	
	
	if(game.is_debugging):
		bot.send_message(ADMIN, game.board.print_board(game.player_sequence), ParseMode.MARKDOWN)
		bot.send_message(ADMIN, 'Por favor nomina a un miembro para la misión!', reply_markup=equipoMarkup)
	else:
		bot.send_message(game.board.state.lider_actual.uid, game.board.print_board(game.player_sequence), ParseMode.MARKDOWN)
		bot.send_message(game.board.state.lider_actual.uid, 'Por favor nomina a un miembro para la misión!', reply_markup=equipoMarkup)

	
def asignar_miembro(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('asignar_miembro called')
	log.info(update.callback_query.data)
	callback = update.callback_query
	regex = re.search("(-[0-9]*)_equipo_([0-9]*)", callback.data)
	cid = int(regex.group(1))
	chosen_uid = int(regex.group(2))

	'''if debugging:
		chosen_uid = ADMIN
	'''
	try:
		game = Commands.get_game(cid)
		log.info(chosen_uid)
		
		if game.board.state.equipo_contador == game.board.state.equipo_cantidad_mision:
			bot.edit_message_text("Ya has elegido a todos los miembros del equipo!", 
					      callback.from_user.id, callback.message.message_id)
			return
		
		turno_actual = len(game.board.state.resultado_misiones)		
		#log.info(game.playerlist)
		#log.info(str(chosen_uid) in game.playerlist )
		#log.info(chosen_uid in game.playerlist)        
		
		miembro_asignado = game.playerlist[chosen_uid]			
		
		log.info("El lider %s (%d) eligio a %s (%d)" % (
			game.board.state.lider_actual.name, game.board.state.lider_actual.uid,
			miembro_asignado.name, miembro_asignado.uid))
		bot.edit_message_text("Tú elegiste a %s para ir a la misión!" % miembro_asignado.name,
				callback.from_user.id, callback.message.message_id)
		
		bot.send_message(game.cid,
			"El lider %s eligió a %s para ir a la misión!" % (
			game.board.state.lider_actual.name, miembro_asignado.name))
		
		#Agrego uno al contador de Miembros, minimo hay 2 por misión.
		#Lo agrego al equipo
		game.board.state.equipo.append(miembro_asignado)
		game.board.state.equipo_contador += 1
				
		# Si se suman la cantidad apropiada de miembros para la mision se vota.
		if game.board.state.equipo_contador == game.board.state.equipo_cantidad_mision:
			pre_inicio_votacion(bot, game)
		else:
			#Si no se eligieron todos se le pide que siga eligiendo hasta llegar al cupo. Se pone tiempo para que no se sobrepise
			asignar_equipo(bot, game)
		
	except AttributeError as e:
		log.error("asignar_miembro: Game or board should not be None! Eror: " + str(e))
	except Exception as e:
		log.error("Unknown error: " + repr(e))
		log.exception(e)

def pre_inicio_votacion(bot, game):
	log.info('pre_inicio_votacion called')
	# Si esta el modulo de Cazador se le pide al Lider que elija a un investigador
	# Solamente si la mision es la 4 o menos. La mision 5 no tiene investigador.
	if "Cazador" in game.modulos and len(game.board.state.resultado_misiones) < 4:
		# Se elige investigador, no puede ser miembro del equipo ni el lider.
		# Se omite este paso si es la 5ta mision
		# Copio por valor, no referencia
		restriccion_jugador_a_elegir = game.board.state.equipo[:]		
		restriccion_jugador_a_elegir.append(game.board.state.lider_actual)
		texto_eleccion = "%s, por favor elige al investigador de esta ronda!" % (game.board.state.lider_actual.name)
		game.board.state.fase_actual = "eleccion_de_investigador_cazador"
		texto_menu = "¿A que jugador quieres elegir para ser el investigador?"
		elegir_jugador_general_menu(bot, game, texto_eleccion, texto_menu, restriccion_jugador_a_elegir, game.board.state.lider_actual.uid)		
	else:
		# Si es un juego normal...
		iniciar_votacion(bot, game)

# Metodo general para mostrar un menupara elegir a un jugador
# La idea es que se pone en el estado del juego para que es esta eleccion, a futuro cambiare todos los lugares
# que se elige a una persona con este.
def elegir_jugador_general_menu(bot, game, texto_publico, texto_menu, restriccion_jugador_a_elegir, id_jugador_eleccion):
	bot.send_message(game.cid, texto_publico, ParseMode.MARKDOWN)
	#Commands.save_game(game.cid, "Saved Round %d" % (game.board.state.currentround), game)	
	log.info('elegir_jugador_general_menu called: %s' % game.board.state.fase_actual)
	
	strcid = str(game.cid)	
	btns = []
	
	# Inicialmente se puede elegir a cualquiera para formar los equipos
	# Menos los que esten en el equipo elegido
	for uid in game.playerlist:
		if game.playerlist[uid] not in restriccion_jugador_a_elegir:
			name = game.playerlist[uid].name
			btns.append([InlineKeyboardButton(name, callback_data=strcid + "_elegirjugador_" + str(uid))])
	
	elegirjugador = InlineKeyboardMarkup(btns)
		
	if(game.is_debugging):
		bot.send_message(ADMIN, game.board.print_board(game.player_sequence), ParseMode.MARKDOWN)
		bot.send_message(ADMIN, texto_menu, reply_markup=elegirjugador)
	else:
		bot.send_message(id_jugador_eleccion, game.board.print_board(game.player_sequence), ParseMode.MARKDOWN)
		bot.send_message(id_jugador_eleccion, texto_menu, reply_markup=elegirjugador)

	
	
# Metodo general para recibir el update de eleccion de jugador por diferentes motivos
def elegir_jugador_general(update: Update, context: CallbackContext):
	bot = context.bot
	# Antes que cualquier cosa obtengo los datos del callback
	log.info('elegir_jugador_general')
	log.info(update.callback_query.data)	
	callback = update.callback_query
	regex = re.search("(-[0-9]*)_elegirjugador_([0-9]*)", callback.data)
	cid = int(regex.group(1))
	chosen_uid = int(regex.group(2))
	game = GamesController.games.get(cid, None)
	miembro_elegido = game.playerlist[chosen_uid]
	strcid = str(game.cid)
	log.info(game.board.state.fase_actual)
	# Luego hago accion dependiendo de la fase en la que este. 
	try:
		# (Cazador) Si esta eligiendo investigador para el modulo cazador.
		# Lo asigno como posible investigador y continuo con la votación.		
		if game.board.state.fase_actual == "eleccion_de_investigador_cazador":			
			bot.edit_message_text("Elegiste a %s para ser investigador en caso que falle la mision!" % miembro_elegido.name,
				callback.from_user.id, callback.message.message_id)
			game.board.state.investigador_nominado = miembro_elegido
			bot.send_message(game.cid, "El investigador elegido ha sido %s" % (miembro_elegido.name), ParseMode.MARKDOWN)
			iniciar_votacion(bot, game)
		# El cazador de la resistencia tiene que descubrir al jefe espia
		if game.board.state.fase_actual == "acusacion_resistencia_cazador":
			bot.edit_message_text("Te lanzas contra %s convencido de que es tu objetivo!" % miembro_elegido.name,
				callback.from_user.id, callback.message.message_id)
			# Si es alguno de los dos espias...
			if miembro_elegido.rol in ("Jefe Espia", "Jefe Espia 2"):
				bot.send_message(game.cid, "El cazador eligio como objetivo a %s" % (miembro_elegido.name), ParseMode.MARKDOWN)
				end_game(bot, game, 2)
			else:
				bot.send_message(game.cid, "El cazador eligio como objetivo a %s" % (miembro_elegido.name), ParseMode.MARKDOWN)
				# Elimino el ultimo resultado y agrego uno de Fracaso
				game.board.state.resultado_misiones.pop()
				game.board.state.resultado_misiones.append("Fracaso")
				# Se verifica nuevamente si hay fin de partida
				verify_fin_de_partida(bot, game)
		
		if game.board.state.fase_actual in ("acusacion_espias_cazador", "acusacion_temprana_espias_cazador"):
			bot.edit_message_text("Te lanzas contra %s convencido de que es tu objetivo!" % miembro_elegido.name,
				callback.from_user.id, callback.message.message_id)
			# Si es alguno de los dos es jefe resistencia. O el coordinador si este esta habilitado.
			if miembro_elegido.rol in ("Jefe Resistencia", "Jefe Resistencia 2", "Coordinador"):
				bot.send_message(game.cid, "El cazador eligio como objetivo a %s" % (miembro_elegido.name), ParseMode.MARKDOWN)
				end_game(bot, game, -3)
			else:
				if game.board.state.fase_actual == "acusacion_temprana_espias_cazador":
					game.board.state.se_ha_realizado_fin_temprano = True				
				bot.send_message(game.cid, "El cazador eligio como objetivo a %s" % (miembro_elegido.name), ParseMode.MARKDOWN)
				# Elimino el ultimo resultado y agrego uno de Fracaso
				game.board.state.resultado_misiones.pop()
				game.board.state.resultado_misiones.append("Exito")
				# Se verifica nuevamente si hay fin de partida
				verify_fin_de_partida(bot, game)
		if game.board.state.fase_actual == "investigacion_cazador":			
			bot.send_message(game.cid, "El investigador %s ha elegido investigar a %s" % (game.board.state.investigador.name, miembro_elegido.name), ParseMode.MARKDOWN)
			game.history.append("El investigador %s ha elegido investigar a %s" % (game.board.state.investigador.name, miembro_elegido.name))
			# Decidi que es no hay motivo estrategico para el jefe espia mostrar
			# que es jefe espia si no hay agente oculto y son 5-6 jugadores		
			if ("Cazador Agente Oculto" not in game.modulos) and len(game.playerlist) < 7:
				if miembro_elegido.rol in ("Jefe Espia", "Jefe Espia 2", "Jefe Resistencia", "Jefe Resistencia 2"):					
					bot.send_message(game.board.state.investigador.uid, "El jugador es: **Jefe**" % (miembro_elegido.name), ParseMode.MARKDOWN)
				else:
					bot.send_message(game.board.state.investigador.uid, "El jugador es: **No jefe**" % (miembro_elegido.name), ParseMode.MARKDOWN)
				start_next_round(bot, game)
			else:
				bot.edit_message_text("Has investigado a %s espera a que elija su respuesta!" % miembro_elegido.name,
					callback.from_user.id, callback.message.message_id)				
				btns = []
				# El jugador debe elegir entre dos ya que tenemos que simular la decision del jefe espia.			
				if miembro_elegido.rol in ("Jefe Espia", "Jefe Espia 2", "Jefe Resistencia", "Jefe Resistencia 2", "Agente Falso"):
					# Si es jefe tiene que decidir
					if miembro_elegido.rol in ("Jefe Resistencia", "Jefe Resistencia 2", "Agente Falso"):
						btns.append([InlineKeyboardButton("Mostrar Jefe", callback_data=strcid + "_mostrarinvestigador_Jefe")])					
						# Si ha 7+ jugadores el jefe de la resistencia puede mostrar la carta de Jefe Resistencia
						if len(game.playerlist) > 6:
							btns.append([InlineKeyboardButton("Mostrar Jefe Resistencia", callback_data=strcid + "_mostrarinvestigador_Jefe_Resistencia")])														
					else:
						# Jefe espia siempre puede mostrar lealtad del jefe y jefe espia
						btns.append([InlineKeyboardButton("Mostrar Jefe Espia", callback_data=strcid + "_mostrarinvestigador_Jefe_Espia")])
						btns.append([InlineKeyboardButton("Mostrar Jefe", callback_data=strcid + "_mostrarinvestigador_Jefe")])										
				else:
					# Si no es lider le pongo solo de opcion que diga "No un jefe"
					btns.append([InlineKeyboardButton("Mostrar No Jefe", callback_data=strcid + "_mostrarinvestigador_No_jefe")])			
				revelarMarkup = InlineKeyboardMarkup(btns)
				if game.is_debugging:
					bot.send_message(ADMIN, '¿Que carta queres mostrar al investigador?', reply_markup=revelarMarkup)
				else:
					bot.send_message(miembro_elegido.uid, '¿Que carta queres mostrar al investigador?', reply_markup=revelarMarkup)
			
	except AttributeError as e:
		log.error("asignar_miembro: Game or board should not be None! Eror: " + str(e))
	except Exception as e:
		log.error("Unknown error: " + repr(e))
		log.exception(e)
		
def iniciar_votacion(bot, game):
	miembros_elegidos = game.get_equipo_actual(False)			
	mensaje_votacion = "Quieres elegir al siguiente equipo para la mision %d:\n" % (len(game.board.state.resultado_misiones) + 1)
	mensaje_votacion += miembros_elegidos
	miembros_elegidos = game.get_equipo_actual(True)		
	game.board.state.mensaje_votacion = mensaje_votacion			
	mensaje_miembros_mision_elegidos = "El líder ha elegido a los siguientes miembros para ir a la misión:\n%s\nVoten en privado si les gusta dicho equipo." % (miembros_elegidos)			
	bot.send_message(game.cid, mensaje_miembros_mision_elegidos, ParseMode.MARKDOWN )	
	if "Trama" in game.modulos:
		creadores_de_opinion = game.get_creadores_de_opinion()
		# Si no hay creadores de opinion...
		if not creadores_de_opinion:
			vote(bot, game)
		else:
			vote_creadores_opinion(bot, game)
	else:
		vote(bot, game)
	
def vote_creadores_opinion(bot, game):
	log.info('vote_creadores_opinion called')
	game.board.state.fase_actual = "vote_creadores_opinion"
	#When voting starts we start the counter to see later with the vote command if we can see you voted.
	game.dateinitvote = datetime.datetime.now()
	game.board.state.fase_actual = "votacion_del_equipo_de_mision"
	strcid = str(game.cid)
	btns = [[InlineKeyboardButton("Si", callback_data=strcid + "_Si"), InlineKeyboardButton("No", callback_data=strcid + "_No")]]
	voteMarkup = InlineKeyboardMarkup(btns)
	
	bot.send_message(game.cid, "Los creadores de opinión deben votar primero tienen que votar ellos primero y mostrar su voto.")
	
	if game.is_debugging:
		bot.send_message(ADMIN, game.board.state.mensaje_votacion, reply_markup=voteMarkup)
		
	creadores_de_opinion = game.get_creadores_de_opinion()
	
	for player in creadores_de_opinion:
		if not game.playerlist[player.uid].esta_muerto and not game.is_debugging:
			if game.playerlist[player.uid] is not game.board.state.lider_actual:
				bot.send_message(player.uid, game.board.print_board(game.player_sequence), ParseMode.MARKDOWN)
			bot.send_message(player.uid, game.board.state.mensaje_votacion + "\nCUIDADO TU VOTO SERA PUBLICO Y NO PODRAS CAMBIARLO!", reply_markup=voteMarkup)
	
def vote(bot, game):
	log.info('Vote called')
	#When voting starts we start the counter to see later with the vote command if we can see you voted.
	game.dateinitvote = datetime.datetime.now()
	game.board.state.fase_actual = "votacion_del_equipo_de_mision"
	strcid = str(game.cid)
	btns = [[InlineKeyboardButton("Si", callback_data=strcid + "_Si"), InlineKeyboardButton("No", callback_data=strcid + "_No")]]
	voteMarkup = InlineKeyboardMarkup(btns)
	
	if game.is_debugging:
		bot.send_message(ADMIN, game.board.state.mensaje_votacion, reply_markup=voteMarkup)
	
	for uid in game.playerlist:
		player = game.playerlist[uid]
		# Me aseguro que los creadores de opinion no tengan para votar o cambiar su voto
		if not player.esta_muerto and not player.creador_de_opinion and not game.is_debugging:			
			# Solo envio votacion a los que no hayan votado
			if player.uid not in game.board.state.last_votes:
				if player is not game.board.state.lider_actual:
					bot.send_message(uid, game.board.print_board(game.player_sequence), ParseMode.MARKDOWN)
				bot.send_message(uid, game.board.state.mensaje_votacion, reply_markup=voteMarkup)
			
def handle_voting(update: Update, context: CallbackContext):
	bot = context.bot	
	callback = update.callback_query
	log.info('handle_voting called: %s' % callback.data)
	regex = re.search("(-[0-9]*)_(.*)", callback.data)
	cid = int(regex.group(1))
	answer = regex.group(2)
	strcid = regex.group(1)
	try:
		game = Commands.get_game(cid)
		
		uid = callback.from_user.id
		player = game.playerlist[uid]
		
		if game.board.state.fase_actual == "vote_creadores_opinion" and not player.creador_de_opinion:
			bot.edit_message_text("No eres un creador de opinion, no debes votar todavia!", uid, callback.message.message_id)
			return
		if game.board.state.fase_actual not in ["votacion_del_equipo_de_mision", "vote_creadores_opinion"]:
			bot.edit_message_text("No es el momento de votar!", uid, callback.message.message_id)
			return
		
		bot.edit_message_text("Gracias por tu voto %s al equipo:\n%s" % (answer, game.get_equipo_actual_flat(False)), uid, callback.message.message_id)
		log.info("Jugador %s (%d) voto %s" % (callback.from_user.first_name, uid, answer))

		#if uid not in game.board.state.last_votes:
		game.board.state.last_votes[uid] = answer
		
		# Ahora vienen los casos particulares
		# Si el usuario es un creador de opinion no le permito cambiar el voto y 
		# verifico si todos los creadores de opinion ya votaron
		if player.creador_de_opinion:
			bot.send_message(game.cid, "El creador de opinion %s ha votado *%s*" % (player.name, answer), ParseMode.MARKDOWN)
			game.history.append("El creador de opinion %s ha votado *%s*" % (player.name, answer))
			if len(game.board.state.last_votes) == len(game.get_creadores_de_opinion()):
				vote(bot, game)
				return
			else:
				return
		
		#Allow player to change his vote
		btns = [[InlineKeyboardButton("Si", callback_data=strcid + "_Si"), InlineKeyboardButton("No", callback_data=strcid + "_No")]]
		voteMarkup = InlineKeyboardMarkup(btns)
		bot.send_message(uid, "Puedes cambiar tu voto aquí.\n%s" % (game.board.state.mensaje_votacion), reply_markup=voteMarkup)
		Commands.save_game(game.cid, "Saved Round %d" % (game.board.state.currentround), game)
		if len(game.board.state.last_votes) == len(game.player_sequence):
			count_votes(bot, game)
	except Exception as e:
		log.error(str(e))


def count_votes(bot, game):
	# La votacion ha finalizado.
	game.dateinitvote = None
	# La votacion ha finalizado.
	log.info('count_votes called')
	voting_text = ""
	voting_success = False
	
	turno_actual = len(game.board.state.resultado_misiones) + 1
	
	for player in game.player_sequence:
		if game.board.state.last_votes[player.uid] == "Si":
			voting_text += game.playerlist[player.uid].name + " votó Si!\n"
		elif game.board.state.last_votes[player.uid] == "No":
			voting_text += game.playerlist[player.uid].name + " votó No!\n"
	if list(game.board.state.last_votes.values()).count("Si") > (len(game.player_sequence) / 2):  
		# because player_sequence doesnt include dead
		# VOTING WAS SUCCESSFUL
		log.info("Voting successful")
				
		voting_text += f"\nFelicitaciones al equipo de [{game.board.state.lider_actual.name}](tg://user?id={game.board.state.lider_actual.uid}) compuesto por:\n{game.get_equipo_actual(True)}\nNO SE PUEDE HABLAR"
		
		voting_success = True
		bot.send_message(game.cid, voting_text, ParseMode.MARKDOWN)
		# Hasta que no se sepa se puede hablar luego de los votos.
		#bot.send_message(game.cid, "\nNo se puede hablar ahora.")
		game.history.append(voting_text)
		log.info(game.history[game.board.state.currentround])
		
		# Si se juega con plot cards se tiene que preguntar si algun jugador tiene la carta de Sin Confianza
		if "Trama" in game.modulos:
			# Veo si algun jugador tiene intencion de usar carta de trama
			# Si ya se pregunto, o el usuario ya dijo que no la usaria...
			# Averiguo si algun jugador tiene carta para jugar primero antes de interrumpir.			
			if preguntar_intencion_uso_carta(bot, game, "Sin confianza 1-Uso", "sinconfianza"):			
				return			
		voting_aftermath(bot, game, voting_success)
	else:
		log.info("Voting failed")
		voting_text += "\nA la resistencia no le gusto el equipo de %s compuesto por:\n%s" % (
			game.board.state.lider_actual.name, game.get_equipo_actual(False))		
		bot.send_message(game.cid, voting_text)
		game.history.append(voting_text)		
		votacion_fallida(bot, game)
		
def votacion_fallida(bot, game):
	game.board.state.failed_votes += 1
	if game.board.state.failed_votes == 5:
		game.board.state.resultado_misiones.append("Fracaso")
		game.history.append("La mision ha sido un fracaso debido a no decidirse!\n\n")
		bot.send_message(game.cid, "La mision ha sido un fracaso debido a no decidirse!")
		verify_fin_de_partida(bot, game)
	else:
		voting_aftermath(bot, game, False)
			
def voting_aftermath(bot, game, voting_success):	
	log.info('voting_aftermath called')
	game.board.state.last_votes = {}
	if voting_success:
		# Se resetea los votos fallidos
		game.board.state.failed_votes = 0
		# (Cazador) el investigador nominado se convierte en investigador real.
		game.board.state.investigador = game.board.state.investigador_nominado
		game.board.state.investigador_nominado = None		
		# Antes que reciban las cartas se puede jugar una carta que obliga a jugar boca arriba su carta de mision.	
		if "Trama" in game.modulos:
			# Veo si algun jugador tiene intencion de usar carta de trama
			# Si ya se pregunto, o el usuario ya dijo que no la usaria...
			if preguntar_intencion_uso_carta(bot, game, "En El Punto De Mira 1-Uso", "enelpuntodemira"):
				return
		inicio_votacion_equipo(bot, game)						
	else:
		start_next_round(bot, game)
		
def inicio_votacion_equipo(bot, game):
	# Pongo para usar el call to vote
	log.info('inicio_votacion_equipo called')
	game.dateinitvote = datetime.datetime.now()
	game.board.state.fase_actual = "conducir_la_mision"
	
	if "Trama" in game.modulos:
		for player in game.board.state.equipo:
			if player.uid != game.board.state.miembroenelpuntodemira:
				enviar_votacion_equipo(bot, game, player)		
	else:
		for player in game.board.state.equipo:
			enviar_votacion_equipo(bot, game, player)

def enviar_votacion_equipo(bot, game, player):
	strcid = str(game.cid)
	
	btns_resistencia = [[InlineKeyboardButton("Exito", callback_data=strcid + "_Exito")]]
	voteMarkupResistencia = InlineKeyboardMarkup(btns_resistencia)

	btns_espias = [[InlineKeyboardButton("Exito", callback_data=strcid + "_Exito"), InlineKeyboardButton("Fracaso", callback_data=strcid + "_Fracaso")]]
	voteMarkupEspias = InlineKeyboardMarkup(btns_espias)
	
	btns_espia_jefe = [[InlineKeyboardButton("Exito", callback_data=strcid + "_Exito"), InlineKeyboardButton("Fracaso Jefe", callback_data=strcid + "_Fracaso Jefe")]]
	voteMarkupEspiaJefe = InlineKeyboardMarkup(btns_espia_jefe)
	
	if game.is_debugging:
		btns_todos = [[InlineKeyboardButton("Exito", callback_data=strcid + "_Exito"), 
				    InlineKeyboardButton("Fracaso", callback_data=strcid + "_Fracaso"), 
				    InlineKeyboardButton("Fracaso Jefe", callback_data=strcid + "_Fracaso Jefe")]]
		voteMarkupTodos = InlineKeyboardMarkup(btns_todos)
		bot.send_message(ADMIN, "¿Ayudaras en el exito de la misión?", reply_markup=voteMarkupTodos)
	else:		
		if player.afiliacion == "Resistencia":
			bot.send_message(player.uid, "¿Ayudaras en el exito de la misión?", reply_markup=voteMarkupResistencia)
		else:
			# (Cazador) si es alguno de los espias jefes y son mas de 7+ jugadores. Los jefes tienen Fracaso Jefe.
			if player.rol in ("Jefe Espia", "Jefe Espia 2") and len(game.playerlist) > 6:
				bot.send_message(player.uid, "¿Ayudaras en el exito de la misión?", reply_markup=voteMarkupEspiaJefe)
			else:
				bot.send_message(player.uid, "¿Ayudaras en el exito de la misión?", reply_markup=voteMarkupEspias)
		
def handle_team_voting(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	log.info('handle_team_voting called: %s' % callback.data)
	regex = re.search("(-[0-9]*)_(.*)", callback.data)
	cid = int(regex.group(1))
	answer = regex.group(2)
	try:
		game = Commands.get_game(cid)
		uid = callback.from_user.id
		bot.edit_message_text("Gracias por tu voto!", uid, callback.message.message_id)
		log.info(f"Jugador {callback.from_user.first_name} ({uid}) voto {answer}")

		#if uid not in game.board.state.last_votes:
		if not game.is_debugging:
			#Modulo Cazador, si el jefe espia pone un fracaso se habilita la acusaion fin de partida temprana
			if game.playerlist[uid].rol in ("Jefe Espia", "Jefe Espia 2") and answer in ("Fracaso", "Fracaso Jefe"):
				game.board.state.trigger_fin_temprano = True				
			game.board.state.votos_mision[uid] = answer
		
		# Si hay alguien en el punto de mira...
		# y es el jugador que recien voto...
		if "Trama" in game.modulos:
			if game.board.state.miembroenelpuntodemira is not None:
				if uid == game.board.state.miembroenelpuntodemira:
					bot.send_message(game.cid, "El voto del jugador %s es: %s" % (callback.from_user.first_name, answer))
					inicio_votacion_equipo(bot, game)
					return
					
		Commands.save_game(game.cid, "Saved Round %d" % (game.board.state.currentround), game)
		#log.info(len(game.board.state.votos_mision))
		#log.info(game.board.state.equipo_cantidad_mision)
		
		# Pretendo que todos votan juntos de una sola forma.
		if game.is_debugging:
			for player in game.board.state.equipo:
				game.board.state.votos_mision[player.uid] = answer
		
		if len(game.board.state.votos_mision) == game.board.state.equipo_cantidad_mision:
			game.dateinitvote = None
			if "Trampero" in game.modulos:
				game.board.state.fase_actual = "carta_mision_trampero"
				bot.send_message(game.cid, "El lider de la misión entonces decide aislar a un miembro para ver sus inteciones")
				elegir_carta_mision(bot, game, game.board.state.lider_actual.uid)
			else:
				# Antes de contar los votos, si hay cartas de trama,
				# preguntamos si algun jugador con la carta vigilancia estrecha quiere ver una carta de mision.
				# Importante no se puede ver la misma carta en una misma mision	
				if "Trama" in game.modulos:
					if preguntar_intencion_uso_carta(bot, game, "Vigilancia Estrecha 1-Uso", "vigilanciaestrecha"):
						return				
				count_mission_votes(bot, game)
	except Exception as e:
		log.error(str(e))

def count_mission_votes(bot, game):
	turno_actual = len(game.board.state.resultado_misiones)
	# La votacion ha finalizado.
	game.dateinitvote = None
	# La votacion ha finalizado.
	log.info('count_votes called')
	voting_text = ""
	voting_success = False
	#Aca se podra hacer llamados para ver las cartas de mision y descartarla antes. Pero primero quiero lo basico
	
	cantidad_fracasos = sum(x == "Fracaso" for x in game.board.state.votos_mision.values())
	cantidad_fracasos_jefe = sum(x == "Fracaso Jefe" for x in game.board.state.votos_mision.values())
	cantidad_exitos = sum(x == "Exito" for x in game.board.state.votos_mision.values())
	
	log.info("Misiones Fracasadas y exitosas") 
	log.info(sum( x == 'Fracaso' for x in game.board.state.resultado_misiones ))
	log.info(sum( x == 'Exito' for x in game.board.state.resultado_misiones ))
		
	bot.send_message(game.cid, "Exitos: %d\nFracasos: %d\n" % (cantidad_exitos, cantidad_fracasos))
	if "Cazador" in game.modulos and len(game.playerlist) > 6:
		bot.send_message(game.cid, "Fracasos Jefe: %d" % cantidad_fracasos_jefe)
	
	#Simplemente verifico si hay algun fracaso en la mision
	#log.info('Fracaso' in game.board.state.votos_mision.values())
	cantidad_fracasos += cantidad_fracasos_jefe
	
	fracaso = False
	
	# Si es una mision que requiere dos fallos...
	if "*" in game.board.misiones[turno_actual]:
		if cantidad_fracasos > 1:
			fracaso = True
		else:
			fracaso = False
	else:
		if cantidad_fracasos > 0:
			fracaso = True
	
	if fracaso:
		game.board.state.resultado_misiones.append("Fracaso")
		game.history.append("La mision ha sido un Fracaso")
		bot.send_message(game.cid, "La mision ha sido saboteada!")
		log.info("Mision fracasada") 
	else:
		game.board.state.resultado_misiones.append("Exito")
		game.history.append("La mision ha sido un Exito")
		bot.send_message(game.cid, "La mision ha sido un exito!")
		log.info("Mision exitosa") 
	
	log.info("Misiones Fracasadas y exitosas") 
	log.info(sum( x == 'Fracaso' for x in game.board.state.resultado_misiones ))
	log.info(sum( x == 'Exito' for x in game.board.state.resultado_misiones ))
	
	verify_fin_de_partida(bot, game)	
		
def verify_fin_de_partida(bot, game):
	finalizo_el_partido = False
	if sum(x == 'Fracaso' for x in game.board.state.resultado_misiones) == 3:
		if "Cazador" in game.modulos:
			finalizo_el_partido = False
			bot.send_message(game.cid, "Con 3 exitos los espias ahora deben encontrar a un jefe de la resistencia y darle caza!")
			# Si se consiguen 3 fallos se debe preguntar al Cazador de los espias que identifique al jefe
			game.board.state.fase_actual = "acusacion_espias_cazador"			
			cazador_espia = game.get_cazador_espia()
			restriccion_jugador_a_elegir = [cazador_espia]
			texto_eleccion = "Cazador de los espias, %s, ¿A quien deseas cazar?" % (cazador_espia.name)
			texto_menu = "¿A que jugador quieres cazar?"
			elegir_jugador_general_menu(bot, game, texto_eleccion, texto_menu, restriccion_jugador_a_elegir, cazador_espia.uid)
			return
		else:
			finalizo_el_partido = True
			end_game(bot, game, -1)		
	if sum(x == 'Exito' for x in game.board.state.resultado_misiones) == 3:
		# Si esta el modulo de asesino se deberia preguntar al asesino a quien mata y mostrar un mensaje de que puede matar
		if "Asesino" in game.modulos:
			finalizo_el_partido = True
			final_asesino(bot, game)
		elif "Cazador" in game.modulos:
			finalizo_el_partido = False
			bot.send_message(game.cid, "Con 3 exitos la resistencia ahora deben encontrar a un jefe de los espias y darle caza!")
			# Si se consiguen 3 exitos se debe preguntar al Cazador de la resistencia que identifique al jefe
			game.board.state.fase_actual = "acusacion_resistencia_cazador"			
			cazador_resistencia = game.get_cazador_resistencia()
			restriccion_jugador_a_elegir = [cazador_resistencia]
			texto_eleccion = "Cazador de la resistencia, %s, ¿A quien deseas cazar?" % (cazador_resistencia.name)
			texto_menu = "¿A que jugador quieres cazar?"
			elegir_jugador_general_menu(bot, game, texto_eleccion, texto_menu, restriccion_jugador_a_elegir, cazador_resistencia.uid)
			return
		else:
			finalizo_el_partido = True
			end_game(bot, game, 1)			
			
	if not finalizo_el_partido:
		# Antes de pasar al proximo turno le pregunto al cazador espia si va a finalizar la partida de forma temprana
		if "Cazador" in game.modulos:
			# Solamente si un Jefe espia ha pasado un fracaso se pregunta el desencadenante temprano.
			# Por lo que verifico si la mision tuvo fracasos o fracasos jefe y si no fue usado ya
			hubo_fracasos = any(x for x in game.board.state.votos_mision.values() if x in ("Fracaso Jefe", "Fracaso"))
			if hubo_fracasos and not game.board.state.se_ha_realizado_fin_temprano:
				# En partidos de 7+ jugadores solo se preguntará si hay fracasos jefe en los votos.
				if len(game.playerlist) > 6:
					if any(x for x in game.board.state.votos_mision.values() if x == "Fracaso Jefe"):
						preguntar_desencadenante_temprano(bot, game)
					else:
						investigacion_cazador(bot, game)
				else:
					# 5-6 jugadores se pregunta siempre que hay fallo ya que no hay fallos jefe.
					preguntar_desencadenante_temprano(bot, game)
			else:
				investigacion_cazador(bot, game)
				
		else:
			bot.send_message(game.cid, game.board.print_board(game.player_sequence), ParseMode.MARKDOWN)
			start_next_round(bot, game)

def preguntar_desencadenante_temprano(bot, game):
	game.board.state.fase_actual = "preguntar_desencadenante_temprano"
	log.info('preguntar_desencadenante_temprano called')
	cazador_espia = game.get_cazador_espia()
	strcid = str(game.cid)
	accion = "desencadenantefindepartidatemprana"
	if game.board.state.trigger_fin_temprano:
		btns = [[InlineKeyboardButton("Si", callback_data=strcid + ("_%s_" % (accion)) + "Si"), 
			 InlineKeyboardButton("No", callback_data=strcid + ("_%s_" % (accion)) + "No")]]
	else:
		btns = [[InlineKeyboardButton("No se dan las condiciones", callback_data=strcid + ("_%s_" % (accion)) + "No")]]		
	desicion = InlineKeyboardMarkup(btns)
	cazador_espia = game.get_cazador_espia()
	if game.is_debugging:
		bot.send_message(ADMIN, "¿Queres trigerear el fin de partido temprano?", reply_markup=desicion)
	else:
		bot.send_message(cazador_espia.uid, "¿Queres trigerear el fin de partido temprano?", reply_markup=desicion)
	
def respuesta_desencadenante_temprano(update: Update, context: CallbackContext):	
	callback = update.callback_query
	bot = context.bot
	log.info('respuesta_desencadenante_temprano called: %s' % callback.data)
	regex = re.search("(-[0-9]*)_desencadenantefindepartidatemprana_(Si|No)", callback.data)
	cid = int(regex.group(1))
	strcid = regex.group(1)	
	answer = regex.group(2)
	game = Commands.get_game(cid)		
	uid = callback.from_user.id
		
	try:
		if not game.board.state.fase_actual == 'preguntar_desencadenante_temprano':
			bot.edit_message_text("No puedes usar esta accion en este momento!", uid, callback.message.message_id)
			return				
		if answer == "Si":
			game.board.state.fase_actual = "acusacion_temprana_espias_cazador"			
			cazador_espia = game.get_cazador_espia()
			restriccion_jugador_a_elegir = [cazador_espia]
			texto_eleccion = "%s, por favor elige a quien cazar!" % (cazador_espia.name)
			texto_menu = "¿A que jugador quieres cazar?"
			elegir_jugador_general_menu(bot, game, texto_eleccion, texto_menu, restriccion_jugador_a_elegir, cazador_espia.uid)
		else:
			#Si no hay acusacion temprana se pasa a la fase de investigacion
			investigacion_cazador(bot, game)
			
	except Exception as e:
		log.error(str(e))

def investigacion_cazador(bot, game):
	# Veo si el ultimo objeto fue un fracaso o un exito.
	game.board.state.fase_actual = "investigacion_cazador"
	if game.board.state.resultado_misiones[-1] == "Exito":
		# En caso de exito el investigador es el lider
		game.board.state.investigador = game.board.state.lider_actual		
	restriccion_jugador_a_elegir = [game.board.state.investigador]
	texto_eleccion = "[%s](tg://user?id=%d), por favor elige a quien investigar esta ronda!" % (game.board.state.investigador.name, game.board.state.investigador.uid)		
	texto_menu = "¿A que jugador quieres investigar?"
	elegir_jugador_general_menu(bot, game, texto_eleccion, texto_menu, restriccion_jugador_a_elegir, game.board.state.investigador.uid)

def respuesta_investigador(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	log.info('respuesta_investigador called: %s' % callback.data)
	regex = re.search("(-[0-9]*)_mostrarinvestigador_(.*)", callback.data)
	cid = int(regex.group(1))
	strcid = regex.group(1)	
	answer = regex.group(2).replace("_", " ")
	game = Commands.get_game(cid)		
	uid = callback.from_user.id	
	
	bot.edit_message_text("Le has respondido al investigador lo siguiente: %s !" % answer, callback.from_user.id, callback.message.message_id)
	
	bot.send_message(game.board.state.investigador.uid, "El jugador es: **%s**" % (answer), ParseMode.MARKDOWN)
	bot.send_message(game.cid, "El investigado ha mostrado su carta al investigador, investigador puedes hablar (o mentir) sobre lo que has investigado")
	# Luego de la investigacion se comienza la proxima ronda 
	start_next_round(bot, game)
	
def start_next_round(bot, game):
	log.info('start_next_round called')
	# start next round if there is no winner (or /cancel)
	if game.board.state.game_endcode == 0:
		# start new round
		sleep(5)

		# Averiguo si algun jugador tiene la carta de Lider Fuerte (Modulo Trama) y le pregunto si quiere usarla
		if "Trama" in game.modulos:
			# Veo si algun jugador tiene intencion de usar carta de trama
			# Si ya se pregunto, o el usuario ya dijo que no la usaria...			
			if preguntar_intencion_uso_carta(bot, game, "Lider Fuerte 1-Uso", "liderfuerte"):
				return
		# if there is no special elected president in between
		if game.board.state.lider_elegido is None:
			increment_player_counter(game)
		start_round(bot, game)
		
#Comienzan metodos de expansiones
# Modulo Asesino
def final_asesino(bot, game):
	#Busco al Asesino y le mando un privado con todos los miembros de la resistencia
	asesino = game.get_asesino()
	miembros_resistencia = game.get_goodguys()
	bot.send_message(game.cid, "Juego finalizado! La Resistencia ganó pasando 3 misiones con...")
	bot.send_message(game.cid, "Minuto! Hay una sombra sobre el edificio con un rifle de francotirador, si mata al comandante habra sido todo por nada! (Los espias pueden charlar entre ellos)")
	# Creando botonera para el asesino
	strcid = str(game.cid)			
	btns = []
	for miembro_resistencia in miembros_resistencia:
		btns.append([InlineKeyboardButton(miembro_resistencia.name, callback_data=strcid + "_asesinato_" + str(miembro_resistencia.uid))])
	miembros_resistencia_markup = InlineKeyboardMarkup(btns)
	
	if game.is_debugging:
		bot.send_message(ADMIN, '¿A quien vas a asesinar? Puedes hablar con tu compañero al respecto', reply_markup=miembros_resistencia_markup)		
	else:
		bot.send_message(asesino.uid, '¿A quien vas a asesinar? Puedes hablar con tu compañero al respecto', reply_markup=miembros_resistencia_markup)		

def asesinar_miembro(update: Update, context: CallbackContext):	
	bot = context.bot
	log.info('asesinar_miembro called')
	log.info(update.callback_query.data)
	callback = update.callback_query
	regex = re.search("(-[0-9]*)_asesinato_([0-9]*)", callback.data)
	cid = int(regex.group(1))
	chosen_uid = int(regex.group(2))

	game = GamesController.games.get(cid, None)
	log.info(chosen_uid)
	miembro_asesinado = game.playerlist[chosen_uid]			
	
	log.info("Se ha asesinado a %s (%d)" % (miembro_asesinado.name, miembro_asesinado.uid))
					
	bot.edit_message_text("Tú asesinaste a %s !" % miembro_asesinado.name,
			callback.from_user.id, callback.message.message_id)
	
	text_asesinato = "La bala pega entre los ojos de %s!\n" % (miembro_asesinado.name)
	
	miembro_asesinado.esta_muerto = True
	
	if miembro_asesinado.rol == "Comandante":
		text_asesinato += "Lamentablemente era nuestro Comandante. La resistencia, sin alguien que los guie, se desbanda."
		bot.send_message(game.cid, text_asesinato)
		end_game(bot, game, -2)
	else:
		text_asesinato += "Los restantes miembros de la resistencia protegen a su lider. El imperio tiene los días contados."
		bot.send_message(game.uid, text_asesinato)
		end_game(bot, game, 1)
	

# Modulo Trama
def preguntar_intencion_uso_carta(bot, game, nombre_carta, accion_carta):
	log.info('preguntar_intencion_uso_carta called')
	result = False
	game.board.state.fase_actual = "plot_" + nombre_carta
		
	strcid = str(game.cid)
	btns = [[InlineKeyboardButton("Si", callback_data=strcid + ("_%s_" % (accion_carta)) + "Si"), 
		 InlineKeyboardButton("No", callback_data=strcid + ("_%s_" % (accion_carta)) + "No")]]
	desicion = InlineKeyboardMarkup(btns)
	jugadores = ""
	for uid in game.playerlist:
		if nombre_carta in game.playerlist[uid].cartas_trama:
			game.board.state.enesperadeaccion[uid] = nombre_carta
			bot.send_message(uid, "¿Queres usar la carta: %s?" % (nombre_carta), reply_markup=desicion)
			jugadores += "[%s](tg://user?id=%d)" % (game.playerlist[uid].name, game.playerlist[uid].uid) + ", "
			result = True
	if result:
		#jugadores = jugadores[:-2]
		bot.send_message(game.cid, "Los jugadores %scon la carta %s, deben decidir si la usan recuerden que si muchos quieren usarla hay prioridad al más cercano al lider actual" % (jugadores, nombre_carta), ParseMode.MARKDOWN)		
	
	return result

# Modulo Trampero
# Modulo Trama
def elegir_carta_mision(bot, game, uid):
	turno_actual = len(game.board.state.resultado_misiones)
	log.info('elegir_carta_mision called')
	strcid = str(game.cid)	
	btns = []
	
	# Inicialmente se puede elegir a cualquiera para ver la carta de mision, a menos que este excluido
	for player in game.board.state.equipo:		
		btns.append([InlineKeyboardButton(player.name, callback_data=strcid + "_verificarcarta_" + str(player.uid))])
	
	equipoMarkup = InlineKeyboardMarkup(btns)
	
	if(game.is_debugging):
		bot.send_message(ADMIN, game.board.print_board(game.player_sequence), ParseMode.MARKDOWN)
		bot.send_message(ADMIN, 'Por favor elegi al miembro de la mision al que quieres ver su carta de misión!', reply_markup=equipoMarkup)
	else:
		
		bot.send_message(uid, game.board.print_board(game.player_sequence), ParseMode.MARKDOWN)
		bot.send_message(uid, 'Por favor elegi al miembro de la mision al que quieres ver su carta de misión!', reply_markup=equipoMarkup)
		
		

def repartir_cartas_trama(bot, game):
	log.info('repartir_cartas_trama called')
	game.board.state.fase_actual = "repartir_cartas_trama"
	#game.board.state.lider_actual
	cantidad_sacar = int(math.ceil((game.board.num_players - 4)/2))		
	'''if game.board.num_players == 5 or game.board.num_players == 6:
		cantidad_sacar = 1
	elif game.board.num_players == 7 or game.board.num_players == 8:
		cantidad_sacar = 2
	elif game.board.num_players == 9 or game.board.num_players == 10:
		cantidad_sacar = 3
	'''
	for i in range(cantidad_sacar):
		game.board.state.cartas_trama_obtenidas.append(game.board.cartastrama.pop(0))
	# Le muestro a todos los jugadores las cartas que ha obtenido el lider
	cartas_disponibles = ""
	for carta in game.board.state.cartas_trama_obtenidas:
		cartas_disponibles += carta + ", "
	bot.send_message(game.cid, "Las cartas que ha obtenido el lider son: *%s*" % cartas_disponibles[:-2], ParseMode.MARKDOWN)
	elegir_carta_de_trama_a_repartir(bot, game)
			 
def elegir_carta_de_trama_a_repartir(bot, game):
	strcid = str(game.cid)
	btns = []	
	for carta in game.board.state.cartas_trama_obtenidas:
		btns.append([InlineKeyboardButton(carta, callback_data=strcid + "_elegircartatrama_" + carta)])		
	cartasMarkup = InlineKeyboardMarkup(btns)
	
	if(game.is_debugging):
		bot.send_message(ADMIN, game.board.print_board(game.player_sequence), ParseMode.MARKDOWN)
		bot.send_message(ADMIN, 'Elige la primera carta a repartir!', reply_markup=cartasMarkup)
	else:
		bot.send_message(game.board.state.lider_actual.uid, game.board.print_board(game.player_sequence), ParseMode.MARKDOWN)
		bot.send_message(game.board.state.lider_actual.uid, 'Elige una carta para repartir!', reply_markup=cartasMarkup)
		
def elegir_jugador_para_dar_carta_de_trama(update: Update, context: CallbackContext):
	bot = context.bot
	callback = update.callback_query
	log.info('handle_voting called: %s' % callback.data)
	regex = re.search("(-[0-9]*)_elegircartatrama_(.*)", callback.data)
	cid = int(regex.group(1))
	answer = regex.group(2)
	strcid = regex.group(1)
	try:
		game = Commands.get_game(cid)
		uid = callback.from_user.id
				
		if not game.board.state.fase_actual == "repartir_cartas_trama":
			bot.edit_message_text("No es el momento de dar cartas de trama!", uid, callback.message.message_id)
			return		
		btns = []
		game.board.state.carta_actual = answer
		# Inicialmente se puede elegir a cualquiera para formar los equipos
		# Menos los que esten en el equipo elegido
		bot.edit_message_text("Has elegido la carta %s!" % (answer), uid, callback.message.message_id)
		for uid in game.playerlist:
			if uid != game.board.state.lider_actual.uid:
				name = game.playerlist[uid].name
				btns.append([InlineKeyboardButton(name, callback_data=strcid + "_darcartatrama_" + str(uid))])
		jugadoresMarkup = InlineKeyboardMarkup(btns)
		if game.is_debugging:
			bot.send_message(ADMIN, 'Elige al jugador que le quieres dar la carta %s!' % (game.board.state.carta_actual), reply_markup=jugadoresMarkup)
		else:
			bot.send_message(game.board.state.lider_actual.uid, 'Elige al jugador que le quieres dar la carta %s!' % (game.board.state.carta_actual), reply_markup=jugadoresMarkup)
	except Exception as e:
		log.error(str(e))
		
def dar_carta_trama(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('dar_carta_trama called')
	log.info(update.callback_query.data)
	callback = update.callback_query
	regex = re.search("(-[0-9]*)_darcartatrama_([0-9]*)", callback.data)
	cid = int(regex.group(1))
	chosen_uid = int(regex.group(2))

	try:
		game = GamesController.games.get(cid, None)
		log.info(chosen_uid)
		miembro_elegido = game.playerlist[chosen_uid]		
		carta = game.board.state.carta_actual
		
		log.info("El lider %s (%d) le dio la carta %s a %s (%d)" % (game.board.state.lider_actual.name, game.board.state.lider_actual.uid, carta, miembro_elegido.name, miembro_elegido.uid))
		bot.edit_message_text("Tú elegiste a %s para la carta %s!" % (miembro_elegido.name, carta),
				callback.from_user.id, callback.message.message_id)		
		bot.send_message(game.cid,
			"El lider %s le dio a %s la carta %s!" % (
			game.board.state.lider_actual.name, miembro_elegido.name, carta))
		
		game.history.append("El lider %s le dio a %s la carta %s!" % (
			game.board.state.lider_actual.name, miembro_elegido.name, carta))
				
		#Agrego uno al contador de Miembros, minimo hay 2 por misión.
		#Lo agrego al equipo
				
		# Si es de 1 uso, se la dejo al jugador en sus cartas disponibles
		if "1-Uso" in carta:
			miembro_elegido.cartas_trama.append(carta)		
		elif "Permanente" in carta:
			# Actualmente solo hay 1 carta permanente
			miembro_elegido.creador_de_opinion = True
			miembro_elegido.cartas_trama.append(carta)
		elif "Inmediata" in carta:
			if carta == "Comunicación Intervenida Inmediata":
				# El jugador que recibe la carte debe investigar un jugador adyacente				
				menu_investigar_jugador(bot, game, chosen_uid)
				return
			if carta == "Compartir Opinión Inmediata":
				# El jugador tiene que mostrar su carta a un jugador adyacente a él				
				menu_revelarse_a_jugador(bot, game, chosen_uid)
				return
			if carta == "Establecer Confianza Inmediata":
				# La ejecuto inmediatamente ya que es simplemente mostrar la afiliacion del lider				
				mostrar_afiliacion(bot, game, chosen_uid, game.board.state.lider_actual.uid)
				verificar_cartas_a_entregar(bot, game)
				return
		verificar_cartas_a_entregar(bot, game)
	except AttributeError as e:
		log.error("dar_carta_trama: Game or board should not be None! Eror: " + str(e))
	except Exception as e:
		log.error("Unknown error: " + repr(e))
		log.exception(e)

def verificar_cartas_a_entregar(bot, game):
	# Remuevo la carta entregada asi se siguen repartiendo las siguientes cartas
	game.board.state.cartas_trama_obtenidas.remove(game.board.state.carta_actual)
	game.board.state.carta_actual =  None

	# Si la lista es vacia...
	if not game.board.state.cartas_trama_obtenidas:
		if preguntar_intencion_uso_carta(bot, game, "Asumir Responsabilidad 1-Uso", "asumirresponsabilidad"):
			return
		#preguntar_intencion_uso_carta(bot, game, "Asumir Responsabilidad 1-Uso", "asumirresponsabilidad")
		asignar_equipo(bot, game)
	else:
		elegir_carta_de_trama_a_repartir(bot, game)
		
def menu_investigar_jugador(bot, game, uidinvestigador):
	log.info('investigar_jugador called')
	strcid = str(game.cid)
	btns = []
	# Le muestro a todos menos el investigador
	for uid in game.playerlist:
		if uid != uidinvestigador:
			name = game.playerlist[uid].name
			btns.append([InlineKeyboardButton(name, callback_data=strcid + "_investigar_" + str(uid))])
	jugadoresMarkup = InlineKeyboardMarkup(btns)
	bot.send_message(uidinvestigador, 'Elige al jugador al que quieres investigar!', reply_markup=jugadoresMarkup)

def menu_revelarse_a_jugador(bot, game, uidrevelado):
	log.info('revelarse_a_jugador called')
	strcid = str(game.cid)
	btns = []
	# Le muestro solo los jugadores adyacentes		
	listaJugadoresDisponibles = get_jugadores_adjacentes(game, uidrevelado)
	
	for player in listaJugadoresDisponibles:
		btns.append([InlineKeyboardButton(player.name, callback_data=strcid + "_revelarse_" + str(player.uid))])
	jugadoresMarkup = InlineKeyboardMarkup(btns)
	bot.send_message(uidrevelado, 'Elige al jugador que le quieres mostrar tu afiliacion!', reply_markup=jugadoresMarkup)

def investigar_jugador(update: Update, context: CallbackContext):	
	bot = context.bot
	log.info('asignar_miembro called')
	log.info(update.callback_query.data)
	callback = update.callback_query
	regex = re.search("(-[0-9]*)_investigar_([0-9]*)", callback.data)
	cid = int(regex.group(1))
	chosen_uid = int(regex.group(2))
	caller_uid = callback.from_user.id
	try:
		game = GamesController.games.get(cid, None)
		mostrar_afiliacion(bot, game, caller_uid, chosen_uid)
		miembro_elegido = game.playerlist[chosen_uid]	
		bot.edit_message_text("Tú has investigado a %s!" % (miembro_elegido.name),
				callback.from_user.id, callback.message.message_id)	
		verificar_cartas_a_entregar(bot, game)
	except AttributeError as e:
		log.error("asignar_miembro: Game or board should not be None! Eror: " + str(e))
	except Exception as e:
		log.error("Unknown error: " + repr(e))
		log.exception(e)

def revelarse_jugador(update: Update, context: CallbackContext):	
	bot = context.bot
	log.info('asignar_miembro called')
	log.info(update.callback_query.data)
	callback = update.callback_query
	regex = re.search("(-[0-9]*)_revelarse_([0-9]*)", callback.data)
	cid = int(regex.group(1))
	chosen_uid = int(regex.group(2))
	caller_uid = callback.from_user.id
	try:
		game = GamesController.games.get(cid, None)
		mostrar_afiliacion(bot, game, chosen_uid, caller_uid)
		miembro_elegido = game.playerlist[chosen_uid]	
		bot.edit_message_text("Te has revelado a %s!" % (miembro_elegido.name),
				callback.from_user.id, callback.message.message_id)
		verificar_cartas_a_entregar(bot, game)
	except AttributeError as e:
		log.error("asignar_miembro: Game or board should not be None! Eror: " + str(e))
	except Exception as e:
		log.error("Unknown error: " + repr(e))
		log.exception(e)
	
def get_jugadores_adjacentes(game, uidjugador):
	indexJugadorRevelado = game.player_sequence.index(game.playerlist[uidjugador])
	indexJugadorALaDerecha = None
	indexJugadorALaIzquierda = None
	# Si es el primer jugador obtengo el segundo y el ultimo
	if indexJugadorRevelado == 0:
		indexJugadorALaIzquierda = indexJugadorRevelado + 1
		indexJugadorALaDerecha = len(game.player_sequence) - 1
	# Si es el ultimo jugador es el jugador primero y el ante ultimo.
	elif indexJugadorRevelado == len(game.player_sequence) - 1:
		indexJugadorALaIzquierda = 0
		indexJugadorALaDerecha = indexJugadorRevelado - 1
	else:
		indexJugadorALaIzquierda = indexJugadorRevelado + 1
		indexJugadorALaDerecha = indexJugadorRevelado - 1
	log.info('El indice del jugador a la derecha es %d' % (indexJugadorALaDerecha))
	log.info('El indice del jugador a la izquierda es %d' % (indexJugadorALaIzquierda))
	
	listaJugadoresDisponibles = []
	listaJugadoresDisponibles.append(game.player_sequence[indexJugadorALaIzquierda])
	listaJugadoresDisponibles.append(game.player_sequence[indexJugadorALaDerecha])
	
	return listaJugadoresDisponibles
	
def mostrar_afiliacion(bot, game, uidinvestigador, uidinvestigado):
	investigado = game.playerlist[uidinvestigado]
	investigador = game.playerlist[uidinvestigador]	
	if game.is_debugging:
		bot.send_message(ADMIN ,"Has investigado a %s y su afiliación es %s" % (investigado.name, investigado.afiliacion))
		bot.send_message(game.cid ,"El jugador %s ha investigado a %s" % (investigador.name, investigado.name))
	else:
		bot.send_message(uidinvestigador ,"Has investigado a %s y su afiliación es %s" % (investigado.name, investigado.afiliacion))
		bot.send_message(game.cid ,"El jugador %s ha investigado a %s" % (investigador.name, investigado.name))
		
def ver_carta_mision(update: Update, context: CallbackContext):	
	log.info('ver_carta_mision called')
	log.info(update.callback_query.data)
	bot = context.bot
	callback = update.callback_query
	regex = re.search("(-[0-9]*)_verificarcarta_([0-9]*)", callback.data)
	cid = int(regex.group(1))
	chosen_uid = int(regex.group(2))
	uid = callback.from_user.id
	try:
		game = Commands.get_game(cid)
		turno_actual = len(game.board.state.resultado_misiones)		
		#log.info(game.playerlist)
		#log.info(str(chosen_uid) in game.playerlist )
		#log.info(chosen_uid in game.playerlist)        
		log.info(chosen_uid)
		
		miembro_investigador = game.playerlist[uid]
		miembro_elegido = game.playerlist[chosen_uid]
		
		log.info("El miembro %s (%d) eligio la carta de %s (%d)" % (
			miembro_investigador.name, miembro_investigador.uid,
			miembro_elegido.name, miembro_elegido.uid))
		
		# Muestro el texto de la carta de mision elegida
		voto_mision = game.board.state.votos_mision[chosen_uid]
		
		bot.edit_message_text("La carta de %s es: %s!" % (miembro_elegido.name, voto_mision),
				uid, callback.message.message_id)
		
		bot.send_message(game.cid,
			"El miembro %s investigo la carta de %s!" % (
			miembro_investigador.name, miembro_elegido.name))
		
		if game.board.state.fase_actual == "carta_mision_trampero":
			# En Trampero se remueve el voto de mision que se ve.
			del game.board.state.votos_mision[chosen_uid]
			count_mission_votes(bot, game)
		else:			
			# Si es el de trama
			game.board.state.enesperadeaccion.pop(uid, None)
			if not game.board.state.enesperadeaccion:
				count_mission_votes(bot, game)
			
	except AttributeError as e:
		log.error("ver_carta_mision: Game or board should not be None! Eror: " + str(e))
	except Exception as e:
		log.error("Unknown error: " + repr(e))
		log.exception(e)

def carta_plot_sinconfianza(update: Update, context: CallbackContext):	
	bot = context.bot
	callback = update.callback_query
	log.info('handle_voting called: %s' % callback.data)
	regex = re.search("(-[0-9]*)_sinconfianza_(Si|No)", callback.data)
	cid = int(regex.group(1))
	strcid = regex.group(1)
	
	answer = regex.group(2)
	try:
		game = Commands.get_game(cid)		
		uid = callback.from_user.id
		nombre_carta = 'Sin confianza 1-Uso'
		fase = "plot_" + nombre_carta
		
		if not game.board.state.fase_actual == fase or not game.board.state.enesperadeaccion:
			bot.edit_message_text("No puedes usar la carta en este momento!", uid, callback.message.message_id)
			return
		if answer == "Si":
			# TODO Al definir que si tendria que ver que se vean prioridades, esto es importante en lider fuerte
			log.info("Jugador %s (%d) decidio usar la carta %s" % (callback.from_user.first_name, uid, nombre_carta))
			bot.send_message(cid, "Jugador %s decidio usar la carta %s" % (callback.from_user.first_name, nombre_carta))
			bot.send_message(cid, "La votacion exitosa se convierte en fallo")
			game.history.append("Jugador %s decidio usar la carta %s\n" % (callback.from_user.first_name, nombre_carta))
			game.playerlist[uid].cartas_trama.remove(nombre_carta)
			game.board.state.enesperadeaccion = {}
			bot.edit_message_text("Has utilizado la carta %s!" % (nombre_carta), uid, callback.message.message_id)
			votacion_fallida(bot, game)
		else:			
			log.info("Jugador %s (%d) decidio no usar la carta %s" % (callback.from_user.first_name, uid, nombre_carta))
			bot.edit_message_text("Gracias por responder!", uid, callback.message.message_id)
			bot.send_message(cid, "Jugador %s decidio no usar la carta %s" % (callback.from_user.first_name, nombre_carta))			
			# Quito la intencion del usuario
			game.board.state.enesperadeaccion.pop(uid, None)
			for jugador in game.board.state.enesperadeaccion:
				log.info("Jugadores que falta decidirse %d" % (jugador))
				
			
			# Si todos los jugadores con esa carta decidieron no usarla entonces se continua el juego normalmente
			# Empty dict bool as false, o sea que si esta vacia continuo.
			if not game.board.state.enesperadeaccion:				
				voting_aftermath(bot, game, True)			
				
	except Exception as e:
		log.error(str(e))

def carta_plot_enelpuntodemira(update: Update, context: CallbackContext):	
	bot = context.bot
	callback = update.callback_query
	log.info('handle_voting called: %s' % callback.data)
	regex = re.search("(-[0-9]*)_enelpuntodemira_(Si|No)", callback.data)
	cid = int(regex.group(1))
	strcid = regex.group(1)
	
	answer = regex.group(2)
	try:
		game = Commands.get_game(cid)		
		uid = callback.from_user.id
		
		nombre_carta = 'En El Punto De Mira 1-Uso'
		fase = "plot_" + nombre_carta
		
		if not game.board.state.fase_actual == fase or not game.board.state.enesperadeaccion:
			bot.edit_message_text("No puedes usar la carta en este momento!", uid, callback.message.message_id)
			return
		
		if answer == "Si":
			# TODO Al definir que si tendria que ver que se vean prioridades, esto es importante en ldier fuerte
			log.info("Jugador %s (%d) decidio usar la carta %s" % (callback.from_user.first_name, uid, nombre_carta))
			bot.send_message(cid, "Jugador %s decidio usar la carta %s" % (callback.from_user.first_name, nombre_carta))	
			game.history.append("Jugador %s decidio usar la carta %s\n" % (callback.from_user.first_name, nombre_carta))
			game.playerlist[uid].cartas_trama.remove('En El Punto De Mira 1-Uso')
			bot.edit_message_text("Has utilizado la carta %s!" % (nombre_carta), uid, callback.message.message_id)
			elegir_miembro_carta_plot_enelpuntodemira(bot, game, uid)
		else:
			# En este caso no se pregunta a otros jugadores ya que hay solo 1 carta de estas,
			# aunque se podria poner como base que siempre se pregunte...
			bot.edit_message_text("Gracias por responder!", uid, callback.message.message_id)
			log.info("Jugador %s (%d) decidio no usar la carta %s" % (callback.from_user.first_name, uid, nombre_carta))
			bot.send_message(cid, "Jugador %s decidio no usar la carta %s" % (callback.from_user.first_name, nombre_carta))
			# Quito la intencion del usuario
			game.board.state.enesperadeaccion.pop(uid, None)
			# Si todos los jugadores con esa carta decidieron no usarla entonces se continua el juego normalmente
			if not game.board.state.enesperadeaccion:
				inicio_votacion_equipo(bot, game)
			
	except Exception as e:
		log.error(str(e))
		
def elegir_miembro_carta_plot_enelpuntodemira(bot, game, uid):
	log.info('elegir_miembro_carta_plot_enelpuntodemira called')	
	try:
		strcid = str(game.cid)	
		btns = []	
		# Doy opcion de elegir cualquier miembro el cual debera poner su carta de mision adelantada
		for player in game.board.state.equipo:		
			btns.append([InlineKeyboardButton(player.name, callback_data=strcid + "_forzarvotomision_" + str(player.uid))])

		equipoMarkup = InlineKeyboardMarkup(btns)	

		if(game.is_debugging):
			bot.send_message(ADMIN, game.board.print_board(game.player_sequence), ParseMode.MARKDOWN)
			bot.send_message(ADMIN, 'Por favor elegi al miembro de la mision al que quieres forzar a jugar su carta de mision por adelantado!', reply_markup=equipoMarkup)
		else:
			bot.send_message(uid, game.board.print_board(game.player_sequence), ParseMode.MARKDOWN)
			bot.send_message(uid, 'Por favor elegi al miembro de la mision al que quieres forzar a jugar su carta de mision por adelantado!', reply_markup=equipoMarkup)
			
	except Exception as e:
		log.error(str(e))

def forzar_jugar_carta_mision_adelantada(update: Update, context: CallbackContext):
	log.info('forzar_jugar_carta_mision_adelantada called')
	log.info(update.callback_query.data)
	bot = context.bot
	callback = update.callback_query
	regex = re.search("(-[0-9]*)_forzarvotomision_([0-9]*)", callback.data)
	cid = int(regex.group(1))
	strcid = regex.group(1)
	
	chosen_uid = int(regex.group(2))
	
	try:
		# Se envia al jugar la opcion de votar normal.
		# La diferencia es que esta se muestra el resultado y hace que el resto siga votando		
		game = Commands.get_game(cid)
		uid = callback.from_user.id
		player = game.playerlist[uid]	
		game.board.state.miembroenelpuntodemira = chosen_uid
		bot.edit_message_text("Has forzado a %s a jugar su carta boca arriba!" % (player.name), uid, callback.message.message_id)
		bot.send_message(cid, "El Jugador %s ha sido forzado a jugar su carta de misión boca arriba" % (player.name))
		enviar_votacion_equipo(bot, game, player)
	except AttributeError as e:
		log.error("forzar_jugar_carta_mision_adelantada: Game or board should not be None! Eror: " + str(e))
	except Exception as e:
		log.error("Unknown error: " + repr(e))
		log.exception(e)
	
		
def carta_plot_vigilanciaestrecha(update: Update, context: CallbackContext):	
	callback = update.callback_query
	log.info('handle_voting called: %s' % callback.data)
	regex = re.search("(-[0-9]*)_vigilanciaestrecha_(Si|No)", callback.data)
	cid = int(regex.group(1))
	strcid = regex.group(1)
	bot = context.bot
	answer = regex.group(2)
	carta = "Vigilancia Estrecha"
	try:
		game = Commands.get_game(cid)		
		uid = callback.from_user.id
		
		nombre_carta = 'Vigilancia Estrecha 1-Uso'
		fase = "plot_" + nombre_carta
		
		if not game.board.state.fase_actual == fase or not game.board.state.enesperadeaccion:
			bot.edit_message_text("No puedes usar la carta en este momento!", uid, callback.message.message_id)
			return
				
		if answer == "Si":
			# TODO Al definir que si tendria que ver que se vean prioridades, esto es importante en ldier fuerte
			log.info("Jugador %s (%d) decidio usar la carta %s" % (callback.from_user.first_name, uid, nombre_carta))
			bot.send_message(cid, "Jugador %s decidio usar la carta %s" % (callback.from_user.first_name, nombre_carta))
			game.history.append("Jugador %s decidio usar la carta %s\n" % (callback.from_user.first_name, nombre_carta))
			game.playerlist[uid].cartas_trama.remove(nombre_carta)
			bot.edit_message_text("Has utilizado la carta %s!" % (nombre_carta), uid, callback.message.message_id)
			elegir_carta_mision(bot, game, uid)
		else:
			bot.edit_message_text("Gracias por responder!", uid, callback.message.message_id)
			log.info("Jugador %s (%d) decidio no usar la carta %s" % (callback.from_user.first_name, uid, nombre_carta))
			bot.send_message(cid, "Jugador %s decidio no usar la carta %s" % (callback.from_user.first_name, nombre_carta))
			# Quito la intencion del usuario
			game.board.state.enesperadeaccion.pop(uid, None)
			# Si todos los jugadores con esa carta decidieron no usarla entonces se continua el juego normalmente
			if not game.board.state.enesperadeaccion:
				count_mission_votes(bot, game)
			
	except Exception as e:
		log.error(str(e))

def carta_plot_liderfuerte(update: Update, context: CallbackContext):	
	bot = context.bot
	callback = update.callback_query
	log.info('handle_voting called: %s' % callback.data)
	regex = re.search("(-[0-9]*)_liderfuerte_(Si|No)", callback.data)
	cid = int(regex.group(1))
	strcid = regex.group(1)
	
	answer = regex.group(2)
	try:
		game = Commands.get_game(cid)		
		uid = callback.from_user.id
		
		nombre_carta = 'Lider Fuerte 1-Uso'
		fase = "plot_" + nombre_carta
		
		if not game.board.state.fase_actual == fase or not game.board.state.enesperadeaccion:
			bot.edit_message_text("No puedes usar la carta en este momento!", uid, callback.message.message_id)
			return
				
		if answer == "Si":
			# TODO Al definir que si tendria que ver que se vean prioridades, esto es importante en ldier fuerte
			log.info("Jugador %s (%d) decidio usar la carta %s" % (callback.from_user.first_name, uid, nombre_carta))
			bot.send_message(cid, "Jugador %s decidio usar la carta %s\n" % (callback.from_user.first_name, nombre_carta))
			game.board.state.lider_elegido = game.playerlist[uid]
			game.playerlist[uid].cartas_trama.remove('Lider Fuerte 1-Uso')
			game.board.state.enesperadeaccion = {}
			bot.edit_message_text("Has utilizado la carta %s!" % (nombre_carta), uid, callback.message.message_id)
			start_round(bot, game)
		else:
			bot.edit_message_text("Gracias por responder!", uid, callback.message.message_id)
			log.info("Jugador %s (%d) decidio no usar la carta %s" % (callback.from_user.first_name, uid, nombre_carta))
			bot.send_message(cid, "Jugador %s decidio no usar la carta %s" % (callback.from_user.first_name, nombre_carta))
			# Quito la intencion del usuario
			game.board.state.enesperadeaccion.pop(uid, None)
			# Si todos los jugadores con esa carta decidieron no usarla entonces se continua el juego normalmente
			if not game.board.state.enesperadeaccion:
				increment_player_counter(game)
				start_round(bot, game)
			
	except Exception as e:
		log.error(str(e))

def carta_plot_asumirresponsabilidad(update: Update, context: CallbackContext):	
	bot = context.bot
	callback = update.callback_query
	log.info('handle_voting called: %s' % callback.data)
	regex = re.search("(-[0-9]*)_asumirresponsabilidad_(Si|No)", callback.data)
	cid = int(regex.group(1))
	strcid = regex.group(1)
	
	answer = regex.group(2)
	try:
		game = Commands.get_game(cid)		
		uid = callback.from_user.id
		
		nombre_carta = 'Asumir Responsabilidad 1-Uso'
		fase = "plot_" + nombre_carta
		
		if not game.board.state.fase_actual == fase or not game.board.state.enesperadeaccion:
			bot.edit_message_text("No puedes usar la carta en este momento!", uid, callback.message.message_id)
			return
				
		if answer == "Si":
			# TODO Al definir que si tendria que ver que se vean prioridades, esto es importante en ldier fuerte
			log.info("Jugador %s (%d) decidio usar la carta %s" % (callback.from_user.first_name, uid, nombre_carta))
			
			bot.edit_message_text("Ahora te mostrare las opciones para usar la carta %s!" % (nombre_carta), uid, callback.message.message_id)
			elegir_miembro_carta_plot_asumirresponsabilidad(bot, game, uid)
		else:
			# En este caso no se pregunta a otros jugadores ya que hay solo 1 carta de estas,
			# aunque se podria poner como base que siempre se pregunte...
			bot.edit_message_text("Gracias por responder!", uid, callback.message.message_id)
			log.info("Jugador %s (%d) decidio no usar la carta %s" % (callback.from_user.first_name, uid, nombre_carta))
			bot.send_message(cid, "Jugador %s decidio no usar la carta %s" % (callback.from_user.first_name, nombre_carta))
			# Quito la intencion del usuario
			game.board.state.enesperadeaccion.pop(uid, None)
			# Si todos los jugadores con esa carta decidieron no usarla entonces se continua el juego normalmente
			if not game.board.state.enesperadeaccion:
				inicio_votacion_equipo(bot, game)
			
	except Exception as e:
		log.error(str(e))		

def elegir_miembro_carta_plot_asumirresponsabilidad(bot, game, uid):
	log.info('elegir_miembro_carta_plot_enelpuntodemira called')	
	try:
		strcid = str(game.cid)	
		btns = []	
		# Doy opcion de elegir cualquier miembro el cual debera poner su carta de mision adelantada
		for player in game.player_sequence:
			if player.cartas_trama and player.uid != uid:
				for carta in player.cartas_trama:
					txtBoton = "%s %s" % (player.name, carta)
					strCarta = carta.replace(" ", "_")
					#datos = strcid + "_elegircartaplot_" + str(player.uid) + "_carta_" + strCarta
					datos = strcid + "_elegircartaplot_" + str(player.uid) + "_" +strCarta
					log.info("Se crea boton con datos: %s %s" % (txtBoton, datos))					
					btns.append([InlineKeyboardButton(txtBoton, callback_data=datos)])
		equipoMarkup = InlineKeyboardMarkup(btns)	

		if(game.is_debugging):
			bot.send_message(ADMIN, game.board.print_board(game.player_sequence), ParseMode.MARKDOWN)
			bot.send_message(ADMIN, 'Por favor elegi la carta que quieres robar al miembro correspondiente!', reply_markup=equipoMarkup)
		else:
			bot.send_message(uid, game.board.print_board(game.player_sequence), ParseMode.MARKDOWN)
			bot.send_message(uid, 'Por favor elegi la carta que quieres robar al miembro correspondiente!', reply_markup=equipoMarkup)
			
	except Exception as e:
		log.error(str(e))
		
def robar_carta_plot(update: Update, context: CallbackContext):	
	bot = context.bot
	callback = update.callback_query
	log.info('robar_carta_plot called: %s' % callback.data)
	regex = re.search("(-[0-9]*)_elegircartaplot_([0-9]*)_(.*)", callback.data)
	cid = int(regex.group(1))
	strcid = regex.group(1)	
	player_objetivo_uid = int(regex.group(2))
	carta = regex.group(3).replace("_", " ")
	
	try:
		game = Commands.get_game(cid)		
		uid = callback.from_user.id
		player_objetivo = game.playerlist[player_objetivo_uid]
		player_ladron = game.playerlist[uid]
			
		if carta in player_objetivo.cartas_trama:
			player_objetivo.cartas_trama.remove(carta)
			bot.send_message(cid, "Jugador %s decidio usar la carta %s" % (player_ladron.name, carta))
			game.history.append("Jugador %s decidio usar la carta %s\n" % (player_ladron.name, carta))
			player_ladron.cartas_trama.remove('Asumir Responsabilidad 1-Uso')
			player_ladron.cartas_trama.append(carta)
			bot.send_message(cid, "El jugador %s ha robado la carta %s al jugador %s" % (player_ladron.name, carta, player_objetivo.name))
			bot.edit_message_text("Le has robado la carta %s a %s!" % (carta, player_objetivo.name), uid, callback.message.message_id)
		else:
			bot.send_message(player_ladron.uid, "El jugador %s ya no tiene la carta %s" % (player_objetivo.name, carta))
			preguntar_intencion_uso_carta(bot, game, "Asumir Responsabilidad 1-Uso", "asumirresponsabilidad")
			
			
	except Exception as e:
		log.error(str(e))
		
##
#
# End of round
#
##

def end_game(bot, game, game_endcode):
	log.info('end_game called')
	##
	# game_endcode:
	#   -2  fascists win by electing Hitler as chancellor
	#   -1  espias ganan con 3 misiones
	#   0   not ended
	#   1   resitencia gana con 3 misiones
	#   2   liberals win by killing Hitler
	#   99  game cancelled
	#
	
	
	
	if game_endcode == 99:
		if GamesController.games[game.cid].board is not None:
			bot.send_message(game.cid, "Juego cancelado!\n\n%s" % game.print_roles())
		else:
			bot.send_message(game.cid, "Juego cancelado!")
	else:
		if game_endcode == -3:
			bot.send_message(game.cid, "Juego finalizado! Los espías ganaron saboteando 3 misiones y descubriendo a un jefe de la resistencia !\n\n%s" % game.print_roles())
		if game_endcode == -2:
			bot.send_message(game.cid, "Juego finalizado! Los espías ganaron matando al Comandante!\n\n%s" % game.print_roles())
		if game_endcode == -1:
			bot.send_message(game.cid, "Juego finalizado! Los espias ganaron saboteando 3 misiones!\n\n%s" % game.print_roles())
		if game_endcode == 1:
			bot.send_message(game.cid, "Juego finalizado! La Resistencia ganó pasando 3 misiones con exito!\n\n%s" % game.print_roles())
		if game_endcode == 2:
			bot.send_message(game.cid, "Juego finalizado! La Resistencia ganó pasando 3 misiones y descubriendo a un jefe de los espias!\n\n%s" % game.print_roles())
		
	#showHiddenhistory(game.cid, bot)
	del GamesController.games[game.cid]
	Commands.delete_game(game.cid)

	
def configurar_partida(bot, game):
	try:
		# Metodo para configurar la partida actual
		strcid = str(game.cid)			
		btns = []
		for modulo in modules.keys():
			if modulo not in game.modulos:
				btns.append([InlineKeyboardButton(modulo, callback_data=strcid + "_modulo_" + modulo)])
		btns.append([InlineKeyboardButton("Finalizar Configuración", callback_data=strcid + "_modulo_" + "Fin")])
		modulosMarkup = InlineKeyboardMarkup(btns)
		bot.send_message(game.cid, 'Elija un modulo para agregar!', reply_markup=modulosMarkup)
	except AttributeError as e:
		log.error("incluir_modulo: " + str(e))
	except Exception as e:
		log.error("Unknown error: " + repr(e))
		log.exception(e)
		
def incluir_modulo(update: Update, context: CallbackContext):
	bot = context.bot
	log.info('incluir_modulo')
	log.info(update.callback_query.data)
	callback = update.callback_query
	regex = re.search("(-[0-9]*)_modulo_(.*)", callback.data)
	
	cid = int(regex.group(1))
	modulo_elegido = regex.group(2)
	strcid = regex.group(1)
	
	log.info(modulo_elegido)
	
	'''if debugging:
		chosen_uid = ADMIN
	'''
	try:
		game = Commands.get_game(cid)
		# Si se ha terminado de configurar los modulos...
		uid = callback.from_user.id
		
		if modulo_elegido == "Fin":
			bot.edit_message_text("Gracias por configurar el juego, para unirse usar /join y para comenzar presione /startgame", cid, callback.message.message_id)
		else:
			game.modulos.append(modulo_elegido)
			bot.edit_message_text("Se ha incluido el modulo %s" % (modulo_elegido), cid, callback.message.message_id)
			Commands.save_game(game.cid, "Configuracion", game)
			configurar_partida(bot, game)
	except AttributeError as e:
		log.error("incluir_modulo: " + str(e))
	except Exception as e:
		log.error("Unknown error: " + repr(e))
		log.exception(e)

		
def showHiddenhistory(cid, bot):
	#game.pedrote = 3
	try:
		#Check if there is a current game		
		game = GamesController.games.get(cid, None)
		history_text = "Historial Oculto:\n\n" 
		for x in game.hiddenhistory:				
			history_text += x + "\n\n"
		bot.send_message(cid, history_text, ParseMode.MARKDOWN)
	except Exception as e:
		bot.send_message(cid, str(e))
		log.error("Unknown error: " + str(e)) 
        
def inform_players(bot, game, cid, player_number):
	log.info('inform_players called')
	bot.send_message(cid,
		"Vamos a comenzar el juego con %d jugadores!\n%s\nVe a nuestro chat privado y mira tu rol secreto!" % (
	player_number, print_player_info(player_number)))
	afiliaciones_posibles = list(playerSets[player_number]["afiliacion"])  # copy not reference because we need it again later
	# Copio las afiliaciones y luego reemplazo por los roles posibles. Tendre que ver que pasa si supera la cantidad
	roles_posibles = list(playerSets[player_number]["afiliacion"])
	set_roles(bot, game, roles_posibles)
	
	if game.is_debugging:
		text_adming_roles_posibles = ""
		text_afiliaciones_posibles = ""
		for rol in roles_posibles:
			text_adming_roles_posibles += rol + " - "
		for afiliacion in afiliaciones_posibles:
			text_afiliaciones_posibles += afiliacion + " - "
			
		bot.send_message(ADMIN, text_adming_roles_posibles[:-3], ParseMode.MARKDOWN)
		bot.send_message(ADMIN, text_afiliaciones_posibles[:-3], ParseMode.MARKDOWN)
	
	for uid in game.playerlist:
		random_index = randrange(len(afiliaciones_posibles))
		#log.info(str(random_index))
		afiliacion = afiliaciones_posibles.pop(random_index)
		#log.info(str(role))
		rol = roles_posibles.pop(random_index)
		game.playerlist[uid].afiliacion = afiliacion
		game.playerlist[uid].rol = rol
		# I comment so tyhe player aren't discturbed in testing, uncomment when deploy to production
		if not game.is_debugging:
			bot.send_message(uid, "Tu rol secreto es: %s\nTu afiliación es: %s" % (rol, afiliacion))
		else:
			bot.send_message(ADMIN, "El jugador %s es %s y su afiliación es: %s" % (game.playerlist[uid].name, rol, afiliacion))


def set_roles(bot, game, lista_a_modificar):
	# Me fijo en cada modulo que roles hay y de que afiliacion son, cambio uno por uno.
	for modulo in game.modulos:
		# Me fijo si el modulo incluye roles
		if "roles" in modules[modulo]:
			modulo_actual = modules[modulo]["roles"]		
			if not modulo_actual == None:
				if modulo == "Cazador":
					# El modulo cazador tiene muchos roles y afiliaciones asi que lo hago aparte.
					# En el futuro se deberia ver por player num en cada modulo asi se hace generico
					player_number = str(len(game.playerlist))
					for rol, afiliacion in modules[modulo]["roles"][player_number].items():
						indice = next((i for i, v in enumerate(lista_a_modificar) if v in afiliacion), -1)
						if indice == -1:
							bot.send_message(ADMIN, "Se quiso agregar un afiliacion (%s) y rol (%s), cuando no hay afiliaciones disponibles" % (afiliacion, rol))	
						else:
							#bot.send_message(ADMIN, indice)
							lista_a_modificar[indice] = rol
				else:					
					for afiliacion, rol in modules[modulo]["roles"].items():	
						# Obtiene el indice y modifica el elemento en la lista 
						indice = next((i for i, v in enumerate(lista_a_modificar) if v in afiliacion), -1)
						if indice == -1:
							bot.send_message(ADMIN, "Se quiso agregar un afiliacion (%s) y rol (%s), cuando no hay afiliaciones disponibles" % (afiliacion, rol))	
						else:
							#bot.send_message(ADMIN, indice)
							lista_a_modificar[indice] = rol

						#bot.send_message(ADMIN, indice)
						'''for n, i in enumerate(a):
						if i == 1:
						a[n] = 10'''
			
def print_player_info(player_number):
    if player_number == 5:
        return "Hay 3 miembros de la resistencia y 2 Espias."
    elif player_number == 6:
        return "Hay 4 miembros de la resistencia y 2 Espias."
    elif player_number == 7:
        return "Hay 4 miembros de la resistencia y 3 Espias."
    elif player_number == 8:
        return "Hay 5 miembros de la resistencia y 3 Espias."
    elif player_number == 9:
        return "Hay 6 miembros de la resistencia y 3 Espias."
    elif player_number == 10:
        return "Hay 6 miembros de la resistencia y 4 Espias."

def inform_badguys(bot, game, player_number):
	log.info('inform_badguys called')

	for uid in game.playerlist:
		afiliacion = game.playerlist[uid].afiliacion
		rol = game.playerlist[uid].rol
			
		if afiliacion == "Espia" and not (rol in ("Espia Ciego", "Agente Oculto")):			
			badguys = game.get_badguys()
			fstring = ""
			for f in badguys:				
				if f.uid != uid:
					fstring += f.name
					if f.rol in ("Jefe Espia", "Jefe Espia 2"):
						fstring += " (%s)" % f.rol
					fstring += ", "
			fstring = fstring[:-2]
			if not game.is_debugging:
				bot.send_message(uid, "Tus compañeros espías son: %s" % fstring)
			else:
				bot.send_message(ADMIN, "Usuario con rol %s: Los espías son: %s" % (rol, fstring))			
		elif afiliacion == "Resistencia":
			if rol == "Comandante":
				badguys = game.get_badguys2()
				fstring = ""
				for f in badguys:
					fstring += f.name + ", "
				fstring = fstring[:-2]
				if not game.is_debugging:
					bot.send_message(uid, "Los espías son: %s" % fstring)
				else:
					bot.send_message(ADMIN, "Comandante: Los espías son: %s" % fstring)
			if rol == "Guardaespaldas":	
				badguys = game.get_comandantes()
				fstring = ""
				for f in badguys:
					fstring += f.name + ", "
				fstring = fstring[:-2]
				if not game.is_debugging:
					bot.send_message(uid, "El/los comandante/s es/son: %s" % fstring)
				else:
					bot.send_message(ADMIN, "Guardaespaldas: Los comandantes son: %s" % fstring)	
			
			if rol in ("Jefe Resistencia", "Jefe Resistencia 2") and player_number > 7:
				jefes_resistencia = game.get_jefes_resistencia()
				fstring = ""
				for f in jefes_resistencia:
					if f.uid != uid:
						fstring += f.name + ", "
				fstring = fstring[:-2]
				if not game.is_debugging:
					bot.send_message(uid, "El otro jefe de la resistencia es: %s" % fstring)
				else:
					bot.send_message(ADMIN, "Jefe resistencia: El otro jefe es: %s" % fstring)
					
				coordinador = game.get_coordinador()
				if coordinador:
					if not game.is_debugging:
						bot.send_message(uid, "El coordinador es: %s" % coordinador[0].name)
					else:
						bot.send_message(ADMIN, "Jefe resistencia: El coordinador es: %s" % coordinador[0].name)
						
		else:
			log.error("inform_badguys: no se que hacer con la afiliacion: %s" % afiliacion)

def increment_player_counter(game):
    log.info('increment_player_counter called')
    if game.board.state.player_counter < len(game.player_sequence) - 1:
        game.board.state.player_counter += 1
    else:
        game.board.state.player_counter = 0


def shuffle_policy_pile(bot, game):
    log.info('shuffle_policy_pile called')
    if len(game.board.policies) < 3:
        game.history[game.board.state.currentround] += "\n\nNo habia cartas suficientes en el mazo de políticas asi que he mezclado el resto con el mazo de descarte!"
        game.board.discards += game.board.policies
        game.board.policies = random.sample(game.board.discards, len(game.board.discards))
        game.board.discards = []
        bot.send_message(game.cid,
                         "No habia cartas suficientes en el mazo de políticas asi que he mezclado el resto con el mazo de descarte!")


def error(update, context):
    # add all the dev user_ids in this list. You can also add ids of channels or groups.
    devs = [ADMIN]
    # we want to notify the user of this problem. This will always work, but not notify users if the update is an
	# callback or inline query, or a poll update. In case you want this, keep in mind that sending the message 
    # could fail
    '''
	if update.effective_message:
        text = "Hey. I'm sorry to inform you that an error happened while I tried to handle your update. " \
               "My developer(s) will be notified."
        update.effective_message.reply_text(text)
	'''
    # This traceback is created with accessing the traceback object from the sys.exc_info, which is returned as the
    # third value of the returned tuple. Then we use the traceback.format_tb to get the traceback as a string, which
    # for a weird reason separates the line breaks in a list, but keeps the linebreaks itself. So just joining an
    # empty string works fine.
    trace = "".join(traceback.format_tb(sys.exc_info()[2]))
    # lets try to get as much information from the telegram update as possible
    payload = ""
    # normally, we always have an user. If not, its either a channel or a poll update.
    if update.effective_user:
        payload += f' with the user {mention_html(update.effective_user.id, update.effective_user.first_name)}'
    # there are more situations when you don't get a chat
    if update.effective_chat:
        payload += f' within the chat <i>{update.effective_chat.title}</i>'
        if update.effective_chat.username:
            payload += f' (@{update.effective_chat.username})'
    # but only one where you have an empty payload by now: A poll (buuuh)
    if update.poll:
        payload += f' with the poll id {update.poll.id}.'
    # lets put this in a "well" formatted text
    text = f"Hey.\n The error <code>{context.error}</code> happened{payload}. The full traceback:\n\n<code>{trace}" \
           f"</code>"
    # and send it to the dev(s)
    for dev_id in devs:
        context.bot.send_message(dev_id, text, parse_mode=ParseMode.HTML)
    # we raise the error again, so the logger module catches it. If you don't use the logger module, use it.
    logger.warning('Update "%s" caused error "%s"', update, context.error)
		
def main():
	GamesController.init() #Call only once
	#initialize_testdata()

	#Init DB Create tables if they don't exist   
	log.info('Init DB')
	conn.autocommit = True
	cur = conn.cursor()
	cur.execute(open("DBCreate.sql", "r").read())
	log.info('DB Created/Updated')
	conn.autocommit = False
	'''
	log.info('Insertando')
	query = "INSERT INTO users(facebook_id, name , access_token , created) values ('2','3','4',1) RETURNING id;"
	log.info('Por ejecutar')
	cur.execute(query)       
	user_id = cur.fetchone()[0]        
	log.info(user_id)
	query = "SELECT ...."
	cur.execute(query)
	'''

	TOKEN = os.environ.get('BOT_TOKEN_RESISTENCIA', None)
	updater = Updater(TOKEN, use_context=True)
	
	

	# Get the dispatcher to register handlers
	dp = updater.dispatcher

	# on different commands - answer in Telegram
	dp.add_handler(CommandHandler("start", Commands.command_start))
	dp.add_handler(CommandHandler("help", Commands.command_help))
	dp.add_handler(CommandHandler("board", Commands.command_board))
	dp.add_handler(CommandHandler("rules", Commands.command_rules))
	dp.add_handler(CommandHandler("ping", Commands.command_ping))
	dp.add_handler(CommandHandler("symbols", Commands.command_symbols))
	dp.add_handler(CommandHandler("stats", Commands.command_stats))
	dp.add_handler(CommandHandler("newgame", Commands.command_newgame))
	dp.add_handler(CommandHandler("startgame", Commands.command_startgame))
	dp.add_handler(CommandHandler("cancelgame", Commands.command_cancelgame))
	dp.add_handler(CommandHandler("join", Commands.command_join, pass_args = True))
	dp.add_handler(CommandHandler("history", Commands.command_showhistory))
	dp.add_handler(CommandHandler("votes", Commands.command_votes))
	dp.add_handler(CommandHandler("calltovote", Commands.command_calltovote))	
	dp.add_handler(CommandHandler("claim", Commands.command_claim, pass_args = True))
	dp.add_handler(CommandHandler("reload", Commands.command_reloadgame))
	dp.add_handler(CommandHandler("debug", Commands.command_toggle_debugging))
	dp.add_handler(CommandHandler("prueba", Commands.command_prueba, pass_args = True))
	dp.add_handler(CommandHandler("cartas", Commands.command_cartas))
	dp.add_handler(CommandHandler("modulos", Commands.command_showmodulos))
	
	#Testing commands
	dp.add_handler(CommandHandler("ja", Commands.command_ja))
	dp.add_handler(CommandHandler("nein", Commands.command_nein))

	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_equipo_(.*)", callback=asignar_miembro))	
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_(Si|No)", callback=handle_voting))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_(Exito|Fracaso|Fracaso Jefe)", callback=handle_team_voting))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_modulo_(.*)", callback=incluir_modulo))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_asesinato_(.*)", callback=asesinar_miembro))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_verificarcarta_(.*)", callback=ver_carta_mision))
	
	# Comandos de cartas de trama
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_elegircartatrama_(.*)", callback=elegir_jugador_para_dar_carta_de_trama))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_darcartatrama_(.*)", callback=dar_carta_trama))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_revelarse_(.*)", callback=revelarse_jugador))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_investigar_(.*)", callback=investigar_jugador))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_sinconfianza_(Si|No)", callback=carta_plot_sinconfianza))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_enelpuntodemira_(Si|No)", callback=carta_plot_enelpuntodemira))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_forzarvotomision_(.*)", callback=forzar_jugar_carta_mision_adelantada))	
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_vigilanciaestrecha_(Si|No)", callback=carta_plot_vigilanciaestrecha))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_liderfuerte_(Si|No)", callback=carta_plot_liderfuerte))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_asumirresponsabilidad_(Si|No)", callback=carta_plot_asumirresponsabilidad))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_elegircartaplot_([0-9]*)_(.*)", callback=robar_carta_plot))
	
	# Comandos de Cazador exclusivamente
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_desencadenantefindepartidatemprana_(Si|No)", callback=respuesta_desencadenante_temprano))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_mostrarinvestigador_(.*)", callback=respuesta_investigador))
	
	# Callbacks de Botones Generales
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_elegirjugador_(.*)", callback=elegir_jugador_general))
	
	# Metodos util
	dp.add_handler(CommandHandler("jugadores", Commands.command_jugadores))
	
	# log all errors
	dp.add_error_handler(error)


	# Codigo con hooks para Telegram
	PORT = int(os.environ.get('PORT', '8443'))
	updater.start_webhook(listen="0.0.0.0",
	      port=PORT,
	      url_path=TOKEN,
		  webhook_url="https://resistenciabot.herokuapp.com/" + TOKEN)
	# Fin codigo con hooks


	# Start the Bot
	# Comentar cuando no se use webhooks
	# updater.start_polling()

	# Run the bot until the you presses Ctrl-C or the process receives SIGINT,
	# SIGTERM or SIGABRT. This should be used most of the time, since
	# start_polling() is non-blocking and will stop the bot gracefully.
	updater.idle()



if __name__ == '__main__':
    main()
