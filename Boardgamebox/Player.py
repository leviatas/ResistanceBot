class Player(object):
    def __init__(self, name, uid):
        self.name = name
        self.uid = uid
        self.rol = None
        self.afiliacion = None
        self.esta_muerto = False        
        self.was_investigated = False
        self.is_the_insquisitor = False
        self.was_the_insquisitor = False
        self.creador_de_opinion = False
        self.cartas_trama = []
