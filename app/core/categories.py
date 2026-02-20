"""Predefined transaction categories (suggested)."""

# Expense categories (gastos)
EXPENSE_CATEGORIES = [
    "alimentación",
    "supermercado",
    "restaurantes",
    "transporte",
    "combustible",
    "vivienda",
    "alquiler",
    "servicios",
    "electricidad",
    "agua",
    "internet",
    "teléfono",
    "entretenimiento",
    "streaming",
    "cine",
    "suscripciones",
    "salud",
    "farmacia",
    "medicamentos",
    "educación",
    "ropa",
    "regalos",
    "donaciones",
    "viajes",
    "hotel",
    "seguros",
    "impuestos",
    "otro",
]

# Income categories (ingresos)
INCOME_CATEGORIES = [
    "salario",
    "freelance",
    "inversiones",
    "dividendos",
    "intereses",
    "alquiler_ingreso",
    "regalo",
    "reembolso",
    "venta",
    "otro",
]

# Special category for transfers (internal)
TRANSFER_CATEGORY = "transferencia"

DEFAULT_CATEGORIES = {
    "expense": EXPENSE_CATEGORIES,
    "income": INCOME_CATEGORIES,
}
