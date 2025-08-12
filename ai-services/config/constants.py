"""
Constants used throughout the Civic Educator AI service.
"""

# Document types
DOCUMENT_TYPES = [
    "act", "bill", "policy", "report", "form", "guideline", "circular", "notice"
]

# Kenyan counties
KENYAN_COUNTIES = [
    "Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret", "Kakamega",
    "Kisii", "Meru", "Thika", "Nyeri", "Garissa", "Wajir", "Mandera",
    "Marsabit", "Isiolo", "Nakuru", "Narok", "Kajiado", "Kiambu",
    "Nyandarua", "Murang'a", "Nyeri", "Kirinyaga", "Laikipia",
    "Nandi", "Baringo", "Samburu", "Turkana", "West Pokot", "Uasin Gishu",
    "Elgeyo-Marakwet", "Trans Nzoia", "Bungoma", "Busia", "Vihiga",
    "Bomet", "Bungoma", "Kakamega", "Vihiga", "Siaya", "Kisumu",
    "Homa Bay", "Migori", "Kisii", "Nyamira", "Narok", "Kajiado",
    "Makueni", "Machakos", "Kitui", "Embu", "Tharaka-Nithi", "Meru",
    "Nyeri", "Kirinyaga", "Murang'a", "Kiambu", "Turkana", "West Pokot",
    "Samburu", "Trans Nzoia", "Uasin Gishu", "Elgeyo-Marakwet", "Nandi",
    "Baringo", "Laikipia", "Nakuru", "Narok", "Kajiado", "Kericho",
    "Bomet", "Kakamega", "Vihiga", "Bungoma", "Busia", "Siaya", "Kisumu",
    "Homa Bay", "Migori", "Kisii", "Nyamira", "Nairobi"
]

# Common Kenyan government terms and abbreviations
GOVERNMENT_TERMS = {
    "cbd": "Central Business District",
    "matatu": "public transport vehicle",
    "boda": "motorcycle taxi",
    "nyama choma": "roasted meat",
    "harambee": "community cooperation",
    "chief": "local administrator",
    "ward": "electoral area",
    "mca": "Member of County Assembly",
    "governor": "county governor",
    "huduma": "service center",
    "kra": "Kenya Revenue Authority",
    "nssf": "National Social Security Fund",
    "nhif": "National Hospital Insurance Fund"
}

# Document categories
DOCUMENT_CATEGORIES = [
    "Environment & Waste Management",
    "Trade & Business",
    "Water & Sanitation",
    "Transport & Roads",
    "Health Services",
    "Education",
    "Planning & Development",
    "General Administration"
]

# Priority levels for queries
PRIORITY_LEVELS = {
    "high": ["emergency", "urgent", "broken", "not working", "complaint"],
    "medium": ["application", "apply", "process", "how to"],
    "normal": []
}

# Default contact information for Nairobi County
NAIROBI_CONTACT = {
    "email": "info@nairobi.go.ke",
    "phone": "+254 20 2245566",
    "address": "City Hall, City Hall Way, P.O. Box 30075-00100, Nairobi, Kenya",
    "website": "https://nairobi.go.ke"
}
