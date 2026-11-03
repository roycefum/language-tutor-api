# Curated "everyday" sample lists — the four lists of about 50 words offered in the app's
# Essentials screen (Common Words, Common Verbs, Irregular Verbs, Food) —
# as static, hand-written tables. Nothing here is generated at request time:
# adding one of these lists is instant, free, and identical for every user, and
# the content can be reviewed once instead of changing on every generation.
#
# Each row is one concept written in the three supported languages, in the
# order (English, Spanish, French). Any language pair is assembled from the
# matching two columns (see everyday_pairs), so a Spanish -> French list pairs
# the Spanish and French columns directly.
#
# A cell is a plain word, or "word|note". A note only appears in the English
# column, where one English word can stand for several (to be -> ser / estar),
# and it is shown only when English is the SOURCE side ("to be (permanent)");
# when English is the target the answer is just "to be". Verbs are infinitives
# ("to speak" in English; the bare infinitive otherwise). No article on nouns.
#
# Common Verbs holds only verbs that are regular in all three languages (so
# one table serves any pair): predictable spelling changes such as -ger or -car
# are fine, but no stem-changing or irregular verb. The irregular ones live in
# IRREGULAR_VERBS.
#
# Two concepts can share a word in another language (ser and estar are both
# "être"); everyday_pairs keeps only the first, so a list never repeats a
# target word.
#
# Spanish is Spain Spanish throughout: where the two varieties differ the Spain
# form is used (coche, ordenador, zumo, ternera, patata, melocotón, gamba,
# plátano, tarta), as chosen by the reviewer.

COMMON_WORDS = [
    ("house", "casa", "maison"),
    ("dog", "perro", "chien"),
    ("cat", "gato", "chat"),
    ("book", "libro", "livre"),
    ("table", "mesa", "table"),
    ("chair", "silla", "chaise"),
    ("water", "agua", "eau"),
    ("food", "comida", "nourriture"),
    ("school", "escuela", "école"),
    ("friend", "amigo", "ami"),
    ("family", "familia", "famille"),
    ("car", "coche", "voiture"),
    ("city", "ciudad", "ville"),
    ("country", "país", "pays"),
    ("day", "día", "jour"),
    ("night", "noche", "nuit"),
    ("week", "semana", "semaine"),
    ("month", "mes", "mois"),
    ("year", "año", "an"),
    ("money", "dinero", "argent"),
    ("job", "trabajo", "emploi"),
    ("door", "puerta", "porte"),
    ("window", "ventana", "fenêtre"),
    ("street", "calle", "rue"),
    ("park", "parque", "parc"),
    ("beach", "playa", "plage"),
    ("mountain", "montaña", "montagne"),
    ("river", "río", "rivière"),
    ("sea", "mar", "mer"),
    ("sky", "cielo", "ciel"),
    ("sun", "sol", "soleil"),
    ("moon", "luna", "lune"),
    ("star", "estrella", "étoile"),
    ("tree", "árbol", "arbre"),
    ("flower", "flor", "fleur"),
    ("fruit", "fruta", "fruit"),
    ("phone", "teléfono", "téléphone"),
    ("computer", "ordenador", "ordinateur"),
    ("music", "música", "musique"),
    ("movie", "película", "film"),
    ("letter", "carta", "lettre"),
    ("picture", "imagen", "image"),
    ("key", "llave", "clé"),
    ("clothing", "ropa", "vêtements"),
    ("shoe", "zapato", "chaussure"),
    ("hat", "sombrero", "chapeau"),
    ("shirt", "camisa", "chemise"),
    ("clock", "reloj", "horloge"),
    ("bridge", "puente", "pont"),
    ("garden", "jardín", "jardin"),
]

COMMON_VERBS = [
    ("to speak", "hablar", "parler"),
    ("to eat", "comer", "manger"),
    ("to arrive", "llegar", "arriver"),
    ("to look for", "buscar", "chercher"),
    ("to carry", "llevar", "porter"),
    ("to leave|behind", "dejar", "laisser"),
    ("to call", "llamar", "appeler"),
    ("to create", "crear", "créer"),
    ("to work", "trabajar", "travailler"),
    ("to study", "estudiar", "étudier"),
    ("to walk", "caminar", "marcher"),
    ("to finish", "terminar", "finir"),
    ("to sell", "vender", "vendre"),
    ("to love", "amar", "aimer"),
    ("to sing", "cantar", "chanter"),
    ("to dance", "bailar", "danser"),
    ("to watch", "mirar", "regarder"),
    ("to listen", "escuchar", "écouter"),
    ("to use", "utilizar", "utiliser"),
    ("to visit", "visitar", "visiter"),
    ("to cook", "cocinar", "cuisiner"),
    ("to swim", "nadar", "nager"),
    ("to travel", "viajar", "voyager"),
    ("to forget", "olvidar", "oublier"),
    ("to help", "ayudar", "aider"),
    ("to wait", "esperar", "attendre"),
    ("to answer", "responder", "répondre"),
    ("to enter", "entrar", "entrer"),
    ("to change", "cambiar", "changer"),
    ("to explain", "explicar", "expliquer"),
    ("to prepare", "preparar", "préparer"),
    ("to wash", "lavar", "laver"),
    ("to decide", "decidir", "décider"),
    ("to teach", "enseñar", "enseigner"),
    ("to ask|a question", "preguntar", "demander"),
    ("to spend|time", "pasar", "passer"),
    ("to cry", "llorar", "pleurer"),
    ("to cut", "cortar", "couper"),
    ("to share", "compartir", "partager"),
    ("to fill", "llenar", "remplir"),
]

IRREGULAR_VERBS = [
    ("to be|permanent", "ser", "être"),
    ("to be|state or location", "estar", "être"),
    ("to have", "tener", "avoir"),
    ("to obtain", "obtener", "obtenir"),
    ("to go", "ir", "aller"),
    ("to do|or to make", "hacer", "faire"),
    ("to be able to", "poder", "pouvoir"),
    ("to want", "querer", "vouloir"),
    ("to know|a fact", "saber", "savoir"),
    ("to know|a person", "conocer", "connaître"),
    ("to say|or to tell", "decir", "dire"),
    ("to see", "ver", "voir"),
    ("to come", "venir", "venir"),
    ("to put", "poner", "mettre"),
    ("to leave|go out", "salir", "sortir"),
    ("to sleep", "dormir", "dormir"),
    ("to feel", "sentir", "sentir"),
    ("to serve", "servir", "servir"),
    ("to write", "escribir", "écrire"),
    ("to read", "leer", "lire"),
    ("to drive", "conducir", "conduire"),
    ("to be born", "nacer", "naître"),
    ("to die", "morir", "mourir"),
    ("to run", "correr", "courir"),
    ("to drink", "beber", "boire"),
    ("to believe", "creer", "croire"),
    ("to live", "vivir", "vivre"),
    ("to follow", "seguir", "suivre"),
    ("to laugh", "reír", "rire"),
    ("to fear", "temer", "craindre"),
    ("to paint", "pintar", "peindre"),
    ("to reach", "alcanzar", "atteindre"),
    ("to solve", "resolver", "résoudre"),
    ("to sew", "coser", "coudre"),
    ("to defeat", "vencer", "vaincre"),
    ("to convince", "convencer", "convaincre"),
    ("to receive", "recibir", "recevoir"),
    ("to offer", "ofrecer", "offrir"),
    ("to be worth", "valer", "valoir"),
    ("to send", "enviar", "envoyer"),
    ("to build", "construir", "construire"),
    ("to destroy", "destruir", "détruire"),
    ("to produce", "producir", "produire"),
    ("to translate", "traducir", "traduire"),
    ("to bring", "traer", "apporter"),
    ("to fall", "caer", "tomber"),
    ("to hear", "oír", "entendre"),
    ("to choose", "elegir", "choisir"),
    ("to ask for", "pedir", "demander"),
    ("to repeat", "repetir", "répéter"),
]

FOOD = [
    ("apple", "manzana", "pomme"),
    ("bread", "pan", "pain"),
    ("milk", "leche", "lait"),
    ("coffee", "café", "café"),
    ("egg", "huevo", "œuf"),
    ("meat", "carne", "viande"),
    ("fish", "pescado", "poisson"),
    ("fruit", "fruta", "fruit"),
    ("vegetable", "verdura", "légume"),
    ("juice", "zumo", "jus"),
    ("rice", "arroz", "riz"),
    ("pasta", "pasta", "pâtes"),
    ("cheese", "queso", "fromage"),
    ("butter", "mantequilla", "beurre"),
    ("sugar", "azúcar", "sucre"),
    ("salt", "sal", "sel"),
    ("pepper", "pimienta", "poivre"),
    ("oil", "aceite", "huile"),
    ("soup", "sopa", "soupe"),
    ("salad", "ensalada", "salade"),
    ("chicken", "pollo", "poulet"),
    ("beef", "ternera", "bœuf"),
    ("pork", "cerdo", "porc"),
    ("ham", "jamón", "jambon"),
    ("sausage", "salchicha", "saucisse"),
    ("shrimp", "gamba", "crevette"),
    ("potato", "patata", "pomme de terre"),
    ("tomato", "tomate", "tomate"),
    ("onion", "cebolla", "oignon"),
    ("garlic", "ajo", "ail"),
    ("carrot", "zanahoria", "carotte"),
    ("lettuce", "lechuga", "laitue"),
    ("banana", "plátano", "banane"),
    ("orange", "naranja", "orange"),
    ("lemon", "limón", "citron"),
    ("strawberry", "fresa", "fraise"),
    ("grape", "uva", "raisin"),
    ("watermelon", "sandía", "pastèque"),
    ("pineapple", "piña", "ananas"),
    ("peach", "melocotón", "pêche"),
    ("nut", "nuez", "noix"),
    ("honey", "miel", "miel"),
    ("jam", "mermelada", "confiture"),
    ("cake", "tarta", "gâteau"),
    ("cookie", "galleta", "biscuit"),
    ("chocolate", "chocolate", "chocolat"),
    ("ice cream", "helado", "glace"),
    ("wine", "vino", "vin"),
    ("beer", "cerveza", "bière"),
    ("tea", "té", "thé"),
]

EVERYDAY_CATEGORIES = {
    "common_words": COMMON_WORDS,
    "common_verbs": COMMON_VERBS,
    "irregular_verbs": IRREGULAR_VERBS,
    "food": FOOD,
}

_COLUMN = {"English": 0, "Spanish": 1, "French": 2}


def _split(cell):
    word, _, note = cell.partition("|")
    return word, note or None


def is_everyday_category(category_key):
    return category_key in EVERYDAY_CATEGORIES


def everyday_pairs(category_key, source_language, target_language):
    """
    One everyday list in the app's own pair shape, for any pair of the three
    supported languages. The target is the bare word; the source is the word,
    with its note in parentheses when it has one ("to be (permanent)").
    Rows whose target word repeats an earlier row's are dropped, so a list
    never asks for the same answer twice. Returns None for an unknown category
    or an unsupported language.
    """
    rows = EVERYDAY_CATEGORIES.get(category_key)
    if rows is None or source_language not in _COLUMN or target_language not in _COLUMN:
        return None
    s, t = _COLUMN[source_language], _COLUMN[target_language]
    seen, pairs = set(), []
    for row in rows:
        source_word, source_note = _split(row[s])
        target_word, _ = _split(row[t])
        key = target_word.lower()
        if key in seen:
            continue
        seen.add(key)
        source = f"{source_word} ({source_note})" if source_note else source_word
        pairs.append({"source word": source, "target word": target_word})
    return pairs
