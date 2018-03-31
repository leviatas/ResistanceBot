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
        }
    },
    "Asesino Comandante Falso": {
        "roles": {
            "Espia": "Comandante Falso"
        }
    },
    "Asesino Guardaespaldas": {
        "roles": {
            "Resistencia": "Guardaespaldas"
        }
    },
    "Asesino Encubierto": {
        "roles": {
            "Espia": "Encubierto"
        }
    },
    "Asesino Espia Ciego": {
        "roles": {
            "Espia": "Espia Ciego"
        }
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
    },
    "Trampero": {
        "rules": [
            "Trampero"
        ]
    },
    "Inquisidor": {
        "rules": [
            "Inquisidor"
        ]
    },
    "Inversor": {
        "roles": {
            "Espia": "Inversor",
            "Resistencia": "Inversor"
        },
        "rules": [
            "Inversor"
        ]
    },
    "Cazador": {
        "roles": {
            "EspiaC": "Cazador",
            "ResistenciaC": "Cazador",
            "EspiaJ": "Jefe",
            "ResistenciaJ": "Jefe"
        },
        "rules": [
            "Cazador"
        ]
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
        ]
    },
    "Sargento": {        
        "rules": [
            "Sargento"
        ]
    },
    "Picaro": {
        "roles": {
            "Espia": "Picaro",
            "Resistencia": "Picaro"
        },
        "rules": [
            "Picaro"
        ]
    }

}

