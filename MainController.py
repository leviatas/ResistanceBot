#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Leviatas"

import json
import logging as log
import random
import re
from random import randrange
from time import sleep

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import (Updater, CommandHandler, CallbackQueryHandler)

import Commands
from Constants.Cards import playerSets
from Constants.Config import TOKEN, STATS, ADMIN
from Boardgamebox.Game import Game
from Boardgamebox.Player import Player
import GamesController
import datetime

import os
import psycopg2
import urllib.parse

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

debugging = False

def initialize_testdata():
    # Sample game for quicker tests
    testgame = Game(-1001113216265, 15771023)
    GamesController.games[-1001113216265] = testgame
    players = [Player("Александр", 320853702), Player("Gustav", 305333239), Player("Rene", 318940765), Player("Susi", 290308460), Player("Renate", 312027975)]
    for player in players:
        testgame.add_player(player.uid, player)

##
#
# Beginning of round
#
##

def start_round(bot, game):        
        Commands.save_game(game.cid, "Saved Round %d" % (game.board.state.currentround + 1), game)
        log.info('start_round called')
        # Starting a new round makes the current round to go up    
        game.board.state.currentround += 1
        
	# Si el lider fue elegido por un evento o jugador... El chosen presidente no sera nulo
        log.info(game.board.state.lider_elegido)
        
        if game.board.state.lider_elegido is None:
                game.board.state.lider_elegido = game.player_sequence[game.board.state.player_counter]
        else:
                game.board.state.lider_actual = game.board.state.lider_elegido
                game.board.state.lider_elegido = None
        
        msgtext =  "El próximo Lider es [%s](tg://user?id=%d).\n%s, por favor elige a los miembros que irán a la mision en nuestro chat privado!" % (game.board.state.nominated_president.name, game.board.state.nominated_president.uid, game.board.state.nominated_president.name)
        bot.send_message(game.cid, msgtext, ParseMode.MARKDOWN)
        asignar_equipo(bot, game)
        # --> nominate_chosen_chancellor --> vote --> handle_voting --> count_votes --> voting_aftermath --> draw_policies
        # --> choose_policy --> pass_two_policies --> choose_policy --> enact_policy --> start_round


def asignar_equipo(bot, game):
	log.info('choose_members called')
	strcid = str(game.cid)
	pres_uid = 0
	chan_uid = 0
	btns = []
			
	#Inicialmente se puede elegir a cualquiera para formar los equipos
	for uid in game.playerlist:
		name = game.playerlist[uid].name
		btns.append([InlineKeyboardButton(name, callback_data=strcid + "_equipo_" + str(uid))])
	equipoMarkup = InlineKeyboardMarkup(btns)

	if(debugging):
		game.board.state.lider_actual.uid = ADMIN		
	bot.send_message(game.board.state.lider_actual.uid, game.board.print_board(game.player_sequence))
	bot.send_message(game.board.state.lider_actual.uid, 'Por favor nomina a un miembro para la misión!', reply_markup=equipoMarkup)


def asignar_miembro(bot, update):
	log.info('asignar_miembro called')
	log.info(update.callback_query.data)
	callback = update.callback_query
	regex = re.search("(-[0-9]*)_chan_([0-9]*)", callback.data)
	cid = int(regex.group(1))
	chosen_uid = int(regex.group(2))

	if debugging:
		chosen_uid = ADMIN   
	try:
		game = GamesController.games.get(cid, None)
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
			mensaje_votacion = "Quieres elegir al siguiente equipo para la mision %s\n" (game.board.state.currentround + 2)
			for player in game.board.state.equipo:
				mensaje_votacion += game.playerlist[player.uid].name + "\n"
			game.board.state.mensaje_votacion = mensaje_votacion			
			vote(bot, game)
		#Si no se eligieron todos se le pide que siga eligiendo hasta llegar al cupo.
		asignar_equipo(bot, game)
		
	except AttributeError as e:
		log.error("asignar_miembro: Game or board should not be None! Eror: " + str(e))
	except Exception as e:
		log.error("Unknown error: " + repr(e))
		log.exception(e)


def vote(bot, game):
	log.info('Vote called')
	#When voting starts we start the counter to see later with the vote command if we can see you voted.
	game.dateinitvote = datetime.datetime.now()
	strcid = str(game.cid)
	btns = [[InlineKeyboardButton("Si", callback_data=strcid + "_Si"), InlineKeyboardButton("No", callback_data=strcid + "_No")]]
	voteMarkup = InlineKeyboardMarkup(btns)
	for uid in game.playerlist:
		if not game.playerlist[uid].esta_muerto and not debugging:
			if game.playerlist[uid] is not game.board.state.nominated_president:
				bot.send_message(uid, game.board.print_board(game.player_sequence))
			bot.send_message(uid, game.board.state.mensaje_votacion, reply_markup=voteMarkup)
			
def handle_voting(bot, update):
    callback = update.callback_query
    log.info('handle_voting called: %s' % callback.data)
    regex = re.search("(-[0-9]*)_(.*)", callback.data)
    cid = int(regex.group(1))
    answer = regex.group(2)
    strcid = regex.group(1)
    try:
        game = GamesController.games[cid]
        uid = callback.from_user.id
        bot.edit_message_text("Gracias por tu voto!", uid, callback.message.message_id)
        log.info("Jugador %s (%d) voto %s" % (callback.from_user.first_name, uid, answer))
        
        #if uid not in game.board.state.last_votes:
        game.board.state.last_votes[uid] = answer
        
        #Allow player to change his vote
        btns = [[InlineKeyboardButton("Si", callback_data=strcid + "_Si"), InlineKeyboardButton("No", callback_data=strcid + "_No")]]
        voteMarkup = InlineKeyboardMarkup(btns)
        bot.send_message(uid, "Puedes cambiar tu voto aquí.\n", reply_markup=voteMarkup)
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
	for player in game.player_sequence:
		if game.board.state.last_votes[player.uid] == "Si":
			voting_text += game.playerlist[player.uid].name + " votó Si!\n"
		elif game.board.state.last_votes[player.uid] == "No":
			voting_text += game.playerlist[player.uid].name + " votó No!\n"
	if list(game.board.state.last_votes.values()).count("Si") > (len(game.player_sequence) / 2):  
		# because player_sequence doesnt include dead
		# VOTING WAS SUCCESSFUL
		log.info("Voting successful")
		voting_text += "Felicitaciones al equipo elegido por [%s](tg://user?id=%d)!" % (
			game.board.state.lider_actual.name, game.board.state.lider_actual .uid)
		#game.board.state.chancellor = game.board.state.nominated_chancellor
		#game.board.state.president = game.board.state.nominated_president
		#game.board.state.nominated_president = None
		#game.board.state.nominated_chancellor = None
		voting_success = True
		bot.send_message(game.cid, voting_text, ParseMode.MARKDOWN)
		bot.send_message(game.cid, "\nNo se puede hablar ahora.")
		game.history.append(("Ronda %d.%d\n\n" % (game.board.state.currentround + 2, game.board.state.failed_votes + 1) ) + voting_text)
		log.info(game.history[game.board.state.currentround])
		voting_aftermath(bot, game, voting_success)
	else:
		log.info("Voting failed")
		voting_text += "A la resistencia no le gusto el equipo de %s!" % (
			game.board.state.lider_actual.name)
		#Reseteo el equipo
		game.board.state.equipo = []
		game.board.state.failed_votes += 1
		bot.send_message(game.cid, voting_text)
		game.history.append(("Ronda %d.%d\n\n" % (game.board.state.currentround + 2, game.board.state.failed_votes) ) + voting_text)
		log.info(game.history[game.board.state.currentround])
		if game.board.state.failed_votes == 5:
			do_anarchy(bot, game)
		else:
			voting_aftermath(bot, game, voting_success)


def voting_aftermath(bot, game, voting_success):
    log.info('voting_aftermath called')
    game.board.state.last_votes = {}
    if voting_success:
	#Si es exitoso reparto las cartas para votar
	btns_resistencia = [[InlineKeyboardButton("Exito", callback_data=strcid + "_Exito")]]
        voteMarkup = InlineKeyboardMarkup(btns)
	
	btns_espias = [[InlineKeyboardButton("Exito", callback_data=strcid + "_Exito"), InlineKeyboardButton("Fracaso", callback_data=strcid + "_Fracaso")]]
        voteMarkup = InlineKeyboardMarkup(btns)
	
	for player in game.board.state.equipo:		
		bot.send_message(player.uid, "", reply_markup=voteMarkup)
    else:
        bot.send_message(game.cid, game.board.print_board(game.player_sequence))
        start_next_round(bot, game)
	
def handle_team_voting(bot, update):
	callback = update.callback_query
	log.info('handle_voting called: %s' % callback.data)
	regex = re.search("(-[0-9]*)_(.*)", callback.data)
	cid = int(regex.group(1))
	answer = regex.group(2)
	strcid = regex.group(1)
	try:
		game = GamesController.games[cid]
		uid = callback.from_user.id
		bot.edit_message_text("Gracias por tu voto!", uid, callback.message.message_id)
		log.info("Jugador %s (%d) voto %s" % (callback.from_user.first_name, uid, answer))

		#if uid not in game.board.state.last_votes:
		game.board.state.votos_mision[uid] = answer
		
		Commands.save_game(game.cid, "Saved Round %d" % (game.board.state.currentround), game)
		if len(game.board.state.last_votes) == len(game.player_sequence):
			count_mission_votes(bot, game)
	except Exception as e:
		log.error(str(e))
		
def count_mission_votes(bot, game):
	# La votacion ha finalizado.
	game.dateinitvote = None
	# La votacion ha finalizado.
	log.info('count_votes called')
	voting_text = ""
	voting_success = False
	#Aca se podra hacer llamados para ver las cartas de mision y descartarla antes. Pero primero quiero lo basico
	
	cantidad_fracasos = sum(x == 'Fracaso' for x in game.board.state.votos_mision.values())
	
	log.info(sum( x == 'Fracaso' for x in game.board.state.votos_mision.values() ))
	log.info(sum( x == 'Exito' for x in game.board.state.votos_mision.values() ))
	
	#Simplemente verifico si hay algun fracaso en la mision
	if 'Fracaso' in game.board.state.votos_mision.values():
		voting_success = False
	else:
		voting_success = True	
	
	game.history.append("La mision ha sido un exito/fracaso")
	start_next_round(bot, game)
	#Despues de poner el resultado de la mision vuelvo al comienzo.
		
def start_next_round(bot, game):
    log.info('start_next_round called')
    # start next round if there is no winner (or /cancel)
    if game.board.state.game_endcode == 0:
        # start new round
        sleep(5)
        # if there is no special elected president in between
        if game.board.state.lider_elegido is None:
            increment_player_counter(game)
        start_round(bot, game)


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
        #   -1  fascists win with 6 fascist policies
        #   0   not ended
        #   1   liberals win with 5 liberal policies
        #   2   liberals win by killing Hitler
        #   99  game cancelled
        #
        if game_endcode == 99:
                if GamesController.games[game.cid].board is not None:
                        bot.send_message(game.cid, "Juego cancelado!\n\n%s" % game.print_roles())
                else:
                        bot.send_message(game.cid, "Juego cancelado!")
        else:
                if game_endcode == -2:
                        bot.send_message(game.cid, "Juego finalizado! Los fascistas ganaron eligiendo a Hitler como Canciller!\n\n%s" % game.print_roles())
                if game_endcode == -1:
                        bot.send_message(game.cid, "Juego finalizado! Los fascistas ganaron promulgando 6 políticas fascistas!\n\n%s" % game.print_roles())
                if game_endcode == 1:
                        bot.send_message(game.cid, "Juego finalizado! Los liberales ganaron promulgando 5 políticas liberales!\n\n%s" % game.print_roles())
                if game_endcode == 2:
                        bot.send_message(game.cid, "Juego finalizado! Los liberales ganaron matando a Hitler!\n\n%s" % game.print_roles())
        #showHiddenhistory(game.cid)
        del GamesController.games[game.cid]
        Commands.delete_game(game.cid)

def showHiddenhistory(cid):
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
    available_roles = list(playerSets[player_number]["roles"])  # copy not reference because we need it again later
    for uid in game.playerlist:
        random_index = randrange(len(available_roles))
        #log.info(str(random_index))
        role = available_roles.pop(random_index)
        #log.info(str(role))
        party = get_membership(role)
        game.playerlist[uid].role = role
        game.playerlist[uid].party = party
        # I comment so tyhe player aren't discturbed in testing, uncomment when deploy to production
        if not debugging:
                bot.send_message(uid, "Tu rol secreto es: %s\nTu afiliación política es: %s" % (role, party))
        else:
                bot.send_message(ADMIN, "El jugador %s es %s y su afiliación política es: %s" % (game.playerlist[uid].name, role, party))


def print_player_info(player_number):
    if player_number == 5:
        return "Hay 3 Liberales, 1 Fascista y Hitler. Hitler conoce quien es el Fascista."
    elif player_number == 6:
        return "Hay  4 Liberales, 1 Fascista y Hitler. Hitler conocer quienes quien es el Fascista."
    elif player_number == 7:
        return "Hay  4 Liberales, 2 Fascistas y Hitler. Hitler no conoce quienes son los Fascistas."
    elif player_number == 8:
        return "Hay  5 Liberales, 2 Fascistas y Hitler. Hitler no conoce quienes son los Fascistas."
    elif player_number == 9:
        return "Hay  5 Liberales, 3 Fascistas y Hitler. Hitler no conoce quienes son los Fascistas."
    elif player_number == 10:
        return "Hay  6 Liberales, 3 Fascistas y Hitler. Hitler no conoce quienes son los Fascistas."


def inform_fascists(bot, game, player_number):
    log.info('inform_fascists called')

    for uid in game.playerlist:
        role = game.playerlist[uid].role
        if role == "Fascista":
            fascists = game.get_fascists()
            if player_number > 6:
                fstring = ""
                for f in fascists:
                    if f.uid != uid:
                        fstring += f.name + ", "
                fstring = fstring[:-2]
                if not debugging:
                        bot.send_message(uid, "Tus compañeros fascistas son: %s" % fstring)
            hitler = game.get_hitler()
            if not debugging:
                        bot.send_message(uid, "Hitler es: %s" % hitler.name) #Uncoomend on production
        elif role == "Hitler":
            if player_number <= 6:
                fascists = game.get_fascists()
                if not debugging:
                        bot.send_message(uid, "Tu compañero fascista es: %s" % fascists[0].name)
        elif role == "Liberal":
            pass
        else:
            log.error("inform_fascists: can\'t handle the role %s" % role)


def get_membership(role):
    log.info('get_membership called')
    if role == "Fascista" or role == "Hitler":
        return "fascista"
    elif role == "Liberal":
        return "liberal"
    else:
        return None


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


def error(bot, update, error):
    #bot.send_message(387393551, 'Update "%s" caused error "%s"' % (update, error) ) 
    logger.warning('Update "%s" caused error "%s"' % (update, error))

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

	#PORT = int(os.environ.get('PORT', '5000'))
	updater = Updater(TOKEN)
	'''
	updater.start_webhook(listen="0.0.0.0",
	      port=PORT,
	      url_path=TOKEN)
	updater.bot.set_webhook("https://secrethitlertest.herokuapp.com/" + TOKEN)
	'''

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

	#Testing commands
	dp.add_handler(CommandHandler("ja", Commands.command_ja))
	dp.add_handler(CommandHandler("nein", Commands.command_nein))

	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_equipo_(.*)", callback=asignar_equipo))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_insp_(.*)", callback=choose_inspect))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_choo_(.*)", callback=choose_choose))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_kill_(.*)", callback=choose_kill))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_(yesveto|noveto)", callback=choose_veto))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_(liberal|fascista|veto)", callback=choose_policy))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_(Si|No)", callback=handle_voting))
	dp.add_handler(CallbackQueryHandler(pattern="(-[0-9]*)_(Exito|Fracaso)", callback=handle_team_voting))


	# log all errors
	dp.add_error_handler(error)

	# Start the Bot
	updater.start_polling()

	# Run the bot until the you presses Ctrl-C or the process receives SIGINT,
	# SIGTERM or SIGABRT. This should be used most of the time, since
	# start_polling() is non-blocking and will stop the bot gracefully.
	updater.idle()



if __name__ == '__main__':
    main()
