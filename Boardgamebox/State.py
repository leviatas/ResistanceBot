class State(object):
    """Storage object for game state"""
    def __init__(self):
        # Datos generales
        self.currentround = -1
        # Mensaje a enviar en las votaciones
        self.mensaje_votacion = None
        # Misiones y como han salido
        self.resultado_misiones = []
        
        # Datos sobre la mision
        self.equipo_cantidad_mision = 0
        
        
        # Equipo para ir a la misión
        self.equipo = []        
        self.equipo_contador = 0
        self.votos_mision = {}
                      
        #self.nominated_president = None Lider por orden
        self.lider_actual = None                
        #self.chosen_president = None Lider elegido por evento o jugador
        self.lider_elegido = None
        
        # Modulo Cazador
        self.investigador_nominado = None
        self.investigador = None
        self.trigger_fin_temprano = False
        self.se_ha_realizado_fin_temprano = False
        
        # Fase Actual
        self.fase_actual = None
        
        # Variables de modulo de trama
        self.miembroenelpuntodemira = None
        self.enesperadeaccion = {}
        self.cartas_trama = []
        self.cartas_trama_obtenidas = []
        self.carta_actual = None
        
        self.chancellor = None
        self.dead = 0
        self.last_votes = {}
        self.game_endcode = 0
        self.drawn_policies = []
        self.player_counter = 0
        self.veto_refused = False
        self.not_hitlers = []
        
        self.liberal_track = 0
        self.fascist_track = 0
        self.failed_votes = 0
