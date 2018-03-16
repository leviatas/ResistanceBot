playerSets = {    
    5: {
        "roles": [
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Espia",
            "Espia"
        ],
        "track": [
            "2",
            "3",
            "2",
            "3",
            "3"            
        ]
    },
    6: {
        "roles": [
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Espia",
            "Espia"
        ],
        "track": [
            "2",
            "3",
            "4",
            "3",
            "4"            
        ]
    },
    7: {
        "roles": [
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Espia",
            "Espia",
            "Espia"
        ],
        "track": [
            "2",
            "3",
            "3",
            "4*",
            "4"            
        ]
    },
    8: {
        "roles": [
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Resistencia",
            "Espia",
            "Espia",
            "Espia"
        ],
        "track": [
            "3",
            "4",
            "4",
            "5*",
            "5"            
        ]
    },
    9: {
        "roles": [
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
        "track": [
            "3",
            "4",
            "4",
            "5*",
            "5"            
        ]
    },
    10: {
        "roles": [
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
        "track": [
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
        ]
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
