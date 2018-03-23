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
        "rules": [
            "Asesino"
        ]
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
            "card",
            "card",
            "card",
            "card",
            "card",
            "card",
            "card",
            "card",
            "card"
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
            "Ambos": "Cazador",
            "Ambos": "Jefe"
        },
        "rules": [
            "Cazador"
        ]
    },
    "Trama": {
        "plot": [
            "Lider Fuerte",
            "Sin confianza",
            "Sin confianza",
            "Sin confianza",
            "Comunicación Intervenida",
            "Comunicación Intervenida",
            "Vigilancia Estrecha",
            "Vigilancia Estrecha",
            "Creador De Opinión",
            "En El Punto De Mira",
            "Compartir Opinión",
            "Establecer Confianza"
        ],
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

