playerSets = {    
    5: {
        "afiliacion": [
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Espia",
            "Espia"
        ],
        "misiones": [
            "2",
            "3",
            "2",
            "3",
            "3"            
        ]
    },
    6: {
        "afiliacion": [
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Espia",
            "Espia"
        ],
        "misiones": [
            "2",
            "3",
            "4",
            "3",
            "4"            
        ]
    },
    7: {
        "afiliacion": [
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Espia",
            "Espia",
            "Espia"
        ],
        "misiones": [
            "2",
            "3",
            "3",
            "4*",
            "4"            
        ]
    },
    8: {
        "afiliacion": [
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Espia",
            "Espia",
            "Espia"
        ],
        "misiones": [
            "3",
            "4",
            "4",
            "5*",
            "5"            
        ]
    },
    9: {
        "afiliacion": [
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Espia",
            "Espia",
            "Espia"
        ],
        "misiones": [
            "3",
            "4",
            "4",
            "5*",
            "5"            
        ]
    },
    10: {
        "afiliacion": [
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Espia",
            "Espia",
            "Espia",
            "Espia"
        ],
        "misiones": [
            "3",
            "4",
            "4",
            "5*",
            "5"            
        ]
    },
}

modules = {
    "Asesino": {
        "roles": {
            "Espia": "Asesino",
            "Resistencia": "Comandante"
        },
        "descripcion" : "Agrega al commandante (Sabe quienes son los espias) y el asesino (que puede intentar matar al comandante si gana la resistencia)."
    },
    "Asesino Comandante Falso": {
        "roles": {
            "Espia": "Comandante Falso"
        },
        "descripcion" : "Agrega un espía que se ve como comandante a Guardaespaldas."
    },
    "Asesino Guardaespaldas": {
        "roles": {
            "Resistencia": "Guardaespaldas"
        },
        "descripcion" : "Agrega un resistencia que sabe quien es el comandante, si hay comandante falso le muestra a ambos como comandantes."
    },
    "Asesino Encubierto": {
        "roles": {
            "Espia": "Encubierto"
        },
        "descripcion" : "Agrega un espía que no es conocido por el comandante."
    },
    "Asesino Espia Ciego": {
        "roles": {
            "Espia": "Espia Ciego"
        },
        "descripcion" : "Agrega un espía que no conoce a sus compañeros ni sus compañeros lo conocen a él, pero es conocido por el comandante."
    },
    "Desertor": {
        "roles": {
            "Espia": "Desertor",
            "Resistencia": "Desertor"
        },
        "rules": [
            "Desertor"
        ],
        "mazoalianza": [
            "Sin Cambio",
            "Sin Cambio",
            "Sin Cambio",
            "Cambia La Lealtad",
            "Cambia La Lealtad"
        ],
        "descripcion" : "Pendiente"
    },
    "Trampero": {
        "rules": [
            "Trampero"
        ],
        "descripcion" : "Pendiente"
    },
    "Inquisidor": {
        "rules": [
            "Inquisidor"
        ],
        "descripcion" : "Pendiente"
    },
    "Inversor": {
        "roles": {
            "Espia": "Inversor",
            "Resistencia": "Inversor"
        },
        "rules": [
            "Inversor"
        ],
        "descripcion" : "Pendiente"
    },
    "Cazador": {
        "roles": {
            "5" : {
                "Cazador Resistencia": "Resistencia",                
                "Jefe Resistencia": "Resistencia",
                "Cazador Espia": "Espia",
                "Jefe Espia": "Espia"
            },
            "6" : {
                "Cazador Resistencia": "Resistencia",
                "Jefe Resistencia": "Resistencia",
                "Cazador Espia": "Espia",                
                "Jefe Espia": "Espia"
            },
            "7" : {
                "Cazador Resistencia": "Resistencia",
                "Jefe Resistencia": "Resistencia",
                "Cazador Espia": "Espia",                
                "Jefe Espia": "Espia"
            },
            "8" : {
                "Cazador Resistencia": "Resistencia",                
                "Jefe Resistencia": "Resistencia",
                "Jefe Resistencia 2": "Resistencia",
                "Jefe Espia": "Espia",
                "Cazador Espia": "Espia"
            },
            "9" : {
                "Cazador Resistencia": "Resistencia",                
                "Jefe Resistencia": "Resistencia",
                "Jefe Resistencia 2": "Resistencia",
                "Jefe Espia": "Espia",
                "Cazador Espia": "Espia"
            },
            "10" : {
                "Cazador Resistencia": "Resistencia",                
                "Jefe Resistencia": "Resistencia",
                "Jefe Resistencia 2": "Resistencia",
                "Cazador Espia": "Espia",
                "Jefe Espia": "Espia",
                "Jefe Espia 2": "Espia"
            }            
        },
        "rules": [
            "Cazador"
        ],
        "descripcion" : "Pendiente"
    },
    "Cazador Agente Falso": {
        "roles": {
            "Resistencia": "Agente Falso"
        },
        "descripcion" : "Pendiente"
    },
    "Cazador Coordinador": {
        "roles": {
            "Resistencia": "Coordinador"
        },
        "descripcion" : "Pendiente"
    },
    "Cazador Agente Oculto": {
        "roles": {
            "Espia": "Agente Oculto"
        },
        "descripcion" : "Pendiente"
    },
    "Cazador Pretendiente": {
        "roles": {
            "Resistencia": "Pretendiente"
        },
        "descripcion" : "Pendiente"
    },
    "Trama": {
        "plot": {
            "5" : [                
                "Lider Fuerte 1-Uso",
                "Lider Fuerte 1-Uso",
                "Sin confianza 1-Uso",                
                "Vigilancia Estrecha 1-Uso",
                "Vigilancia Estrecha 1-Uso",                
                "Creador De Opinión Permanente",
                "Asumir Responsabilidad 1-Uso"
            ],
            "7" : [
                "Comunicación Intervenida Inmediata",
                "Comunicación Intervenida Inmediata",
                "En El Punto De Mira 1-Uso",
                "Compartir Opinión Inmediata",
                "Establecer Confianza Inmediata",
                "Creador De Opinión Permanente",
                "Sin confianza 1-Uso",
                "Sin confianza 1-Uso"
            ]
        },
        "rules": [
            "plot"
        ],
        "descripcion" : "Pendiente"
    },
    "Sargento": {        
        "rules": [
            "Sargento"
        ],
        "descripcion" : "Pendiente"
    },
    "Picaro": {
        "roles": {
            "Espia": "Picaro",
            "Resistencia": "Picaro"
        },
        "rules": [
            "Picaro"
        ],
        "descripcion" : "Pendiente"
    }

}

