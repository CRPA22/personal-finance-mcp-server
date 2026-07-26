"""Predefined transaction categories (suggested)."""

# Expense categories (gastos) - sincronizado con Supabase
EXPENSE_CATEGORIES = [
    "Alquiler",
    "Despensa",
    "Educacion",
    "Entretenimiento",
    "Otros",
    "Pasajes",
    "Restaurante",
    "Salud",
    "Snacks",
    "Suscripciones",
    "Taxi",
    "Telefono",
    "Vehiculo",
    "Vestimenta",
]

# Income categories (ingresos) - sincronizado con Supabase
INCOME_CATEGORIES = [
    "alquiler_ingreso",
    "dividendos",
    "familia",
    "freelance",
    "intereses",
    "inversiones",
    "otro",
    "reembolso",
    "regalo",
    "salario",
    "venta",
]

# Special category for transfers (internal)
TRANSFER_CATEGORY = "transferencia"

DEFAULT_CATEGORIES = {
    "expense": EXPENSE_CATEGORIES,
    "income": INCOME_CATEGORIES,
}
