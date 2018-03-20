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
            "Asesino": "Espia",
            "Comandante": "Resistencia"
        },
        "rules": [
            "Asesino"
        ]
    },
    "Desertor": {
        "roles": {
            "Desertor": "Espia",
            "Desertor": "Resistencia"
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
            "Inversor": "Espia",
            "Inversor": "Resistencia"
        },
        "rules": [
            "Inversor"
        ]
    },
    "Cazador": {
        "roles": {
            "Cazador": "Espia",
            "Cazador": "Resistencia",
            "Jefe": "Espia",
            "Jefe": "Resistencia"
        },
        "rules": [
            "Cazador"
        ]
    },
    "Trama": {
        "plot": [
            "plotcard",
            "plotcard",
            "plotcard",
            "plotcard",
            "plotcard",
            "plotcard",
            "plotcard",
            "plotcard",
            "plotcard"
        ],
        "rules": [
            "plot"
        ]
    },
    "Sargento": {
        "roles": {
            "Sargento": "Ambos"
        },
        "rules": [
            "Sargento"
        ]
    },
    "Picaro": {
        "roles": {
            "Picaro": "Espia",
            "Picaro": "Resistencia"
        },
        "rules": [
            "Picaro"
        ]
    }

}

