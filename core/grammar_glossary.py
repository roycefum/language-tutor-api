# The shared vocabulary behind grammar-list labels. A grammar row stores a
# "kind" (subject pronoun, preposition, ...) and a few "tags" (1st person,
# singular, informal, ...) as English keys; this glossary says how each is
# written in every supported native language, so a learner reads the label in
# their own language. Row-specific meanings live on the row itself (they can't
# be shared). The Spanish and French entries are model-drafted and have not
# been reviewed by a native speaker yet.

GLOSSARY = {
    "subject pronoun": {"Spanish": "pronombre sujeto", "French": "pronom sujet"},
    "1st person": {"Spanish": "1.ª persona", "French": "1re personne"},
    "2nd person": {"Spanish": "2.ª persona", "French": "2e personne"},
    "3rd person": {"Spanish": "3.ª persona", "French": "3e personne"},
    "singular": {"Spanish": "singular", "French": "singulier"},
    "plural": {"Spanish": "plural", "French": "pluriel"},
    "masculine": {"Spanish": "masculino", "French": "masculin"},
    "feminine": {"Spanish": "femenino", "French": "féminin"},
    "masculine or mixed group": {"Spanish": "masculino o grupo mixto", "French": "masculin ou groupe mixte"},
    "informal": {"Spanish": "informal", "French": "familier"},
    "formal": {"Spanish": "formal", "French": "formel"},
    "informal (Spain)": {"Spanish": "informal (España)", "French": "familier (Espagne)"},
    "preposition": {"Spanish": "preposición", "French": "préposition"},
    "prepositional phrase": {"Spanish": "locución preposicional", "French": "locution prépositive"},
    "coordinating conjunction": {"Spanish": "conjunción coordinante", "French": "conjonction de coordination"},
    "subordinating conjunction": {"Spanish": "conjunción subordinante", "French": "conjonction de subordination"},
    "possessive adjective": {"Spanish": "adjetivo posesivo", "French": "adjectif possessif"},
    "interrogative adverb": {"Spanish": "adverbio interrogativo", "French": "adverbe interrogatif"},
    "interrogative pronoun": {"Spanish": "pronombre interrogativo", "French": "pronom interrogatif"},
    "interrogative quantifier": {"Spanish": "cuantificador interrogativo", "French": "quantifieur interrogatif"},
    "interrogative adjective": {"Spanish": "adjetivo interrogativo", "French": "adjectif interrogatif"},
    "interrogative pronoun or determiner": {"Spanish": "pronombre o determinante interrogativo", "French": "pronom ou déterminant interrogatif"},
    "interrogative determiner": {"Spanish": "determinante interrogativo", "French": "déterminant interrogatif"},
    "interrogative phrase": {"Spanish": "locución interrogativa", "French": "locution interrogative"},
    "relative pronoun": {"Spanish": "pronombre relativo", "French": "pronom relatif"},
    "relative adjective": {"Spanish": "adjetivo relativo", "French": "adjectif relatif"},
    "relative adverb": {"Spanish": "adverbio relativo", "French": "adverbe relatif"},
    "relative determiner": {"Spanish": "determinante relativo", "French": "déterminant relatif"},
    "negative adverb": {"Spanish": "adverbio negativo", "French": "adverbe négatif"},
    "negative pronoun": {"Spanish": "pronombre negativo", "French": "pronom négatif"},
    "negative adjective": {"Spanish": "adjetivo negativo", "French": "adjectif négatif"},
    "negative adjective or pronoun": {"Spanish": "adjetivo o pronombre negativo", "French": "adjectif ou pronom négatif"},
    "negative determiner": {"Spanish": "determinante negativo", "French": "déterminant négatif"},
    "negative adverbial phrase": {"Spanish": "locución adverbial negativa", "French": "locution adverbiale négative"},
    "indefinite pronoun": {"Spanish": "pronombre indefinido", "French": "pronom indéfini"},
    "indefinite adjective": {"Spanish": "adjetivo indefinido", "French": "adjectif indéfini"},
    "indefinite adjective or pronoun": {"Spanish": "adjetivo o pronombre indefinido", "French": "adjectif ou pronom indéfini"},
    "indefinite adverb": {"Spanish": "adverbio indefinido", "French": "adverbe indéfini"},
    "indefinite adverbial phrase": {"Spanish": "locución adverbial indefinida", "French": "locution adverbiale indéfinie"},
    "adverb": {"Spanish": "adverbio", "French": "adverbe"},
    "masculine singular": {"Spanish": "masculino singular", "French": "masculin singulier"},
    "feminine singular": {"Spanish": "femenino singular", "French": "féminin singulier"},
    "masculine plural": {"Spanish": "masculino plural", "French": "masculin pluriel"},
    "feminine plural": {"Spanish": "femenino plural", "French": "féminin pluriel"},
    "used with ne": {"Spanish": "se usa con ne", "French": "s'emploie avec ne"},
    "takes the subjunctive": {"Spanish": "lleva subjuntivo", "French": "se construit avec le subjonctif"},
    "more formal": {"Spanish": "más formal", "French": "plus soutenu"},
    "with no noun before it": {"Spanish": "sin un nombre antes", "French": "sans nom avant"},
    "in questions and negatives": {"Spanish": "en preguntas y negaciones", "French": "dans les questions et les négations"},
    "as the subject of the clause": {"Spanish": "como sujeto de la oración", "French": "comme sujet de la proposition"},
    "as the object of the clause": {"Spanish": "como complemento de la oración", "French": "comme complément de la proposition"},
    "after a preposition": {"Spanish": "tras una preposición", "French": "après une préposition"},
    "one thing owned": {"Spanish": "una sola cosa poseída", "French": "un seul objet possédé"},
    "several things owned": {"Spanish": "varias cosas poseídas", "French": "plusieurs objets possédés"},
    "masculine singular thing owned": {"Spanish": "cosa poseída masculina singular", "French": "objet possédé masculin singulier"},
    "feminine singular thing owned": {"Spanish": "cosa poseída femenina singular", "French": "objet possédé féminin singulier"},
    "masculine plural things owned": {"Spanish": "cosas poseídas masculinas plurales", "French": "objets possédés masculins pluriel"},
    "feminine plural things owned": {"Spanish": "cosas poseídas femeninas plurales", "French": "objets possédés féminins pluriel"},
    "object pronoun": {"Spanish": "pronombre de complemento", "French": "pronom complément"},
    "adverbial pronoun": {"Spanish": "pronombre adverbial", "French": "pronom adverbial"},
    "reflexive pronoun": {"Spanish": "pronombre reflexivo", "French": "pronom réfléchi"},
    "article": {"Spanish": "artículo", "French": "article"},
    "demonstrative adjective": {"Spanish": "adjetivo demostrativo", "French": "adjectif démonstratif"},
    "demonstrative pronoun": {"Spanish": "pronombre demostrativo", "French": "pronom démonstratif"},
    "demonstrative": {"Spanish": "demostrativo", "French": "démonstratif"},
    "negative particle": {"Spanish": "partícula negativa", "French": "particule négative"},
    "direct object": {"Spanish": "complemento directo", "French": "complément d'objet direct"},
    "indirect object": {"Spanish": "complemento indirecto", "French": "complément d'objet indirect"},
    "direct, indirect or reflexive": {"Spanish": "directo, indirecto o reflexivo", "French": "direct, indirect ou réfléchi"},
    "reflexive": {"Spanish": "reflexivo", "French": "réfléchi"},
    "definite": {"Spanish": "definido", "French": "défini"},
    "indefinite": {"Spanish": "indefinido", "French": "indéfini"},
    "partitive": {"Spanish": "partitivo", "French": "partitif"},
    "contracted with a preposition": {"Spanish": "contracto con una preposición", "French": "contracté avec une préposition"},
    "neuter": {"Spanish": "neutro", "French": "neutre"},
    "before a vowel or silent h": {"Spanish": "ante vocal o h muda", "French": "devant une voyelle ou un h muet"},
    "before a consonant": {"Spanish": "ante consonante", "French": "devant une consonne"},
    "before a consonant sound": {"Spanish": "ante un sonido consonante", "French": "devant un son consonantique"},
    "before a vowel sound": {"Spanish": "ante un sonido vocálico", "French": "devant un son vocalique"},
    "near the speaker": {"Spanish": "cerca de quien habla", "French": "près de celui qui parle"},
    "near the listener": {"Spanish": "cerca de quien escucha", "French": "près de celui qui écoute"},
    "far from both": {"Spanish": "lejos de ambos", "French": "loin des deux"},
    "far from the speaker": {"Spanish": "lejos de quien habla", "French": "loin de celui qui parle"},
    "stressed pronoun": {"Spanish": "pronombre tónico", "French": "pronom disjoint"},
    "prepositional pronoun": {"Spanish": "pronombre preposicional", "French": "pronom prépositionnel"},
    "general or impersonal": {"Spanish": "general o impersonal", "French": "général ou impersonnel"},
    "combined with con": {"Spanish": "unido a con", "French": "combiné avec con"},
    "replaces the article": {"Spanish": "sustituye al artículo", "French": "remplace l'article"},
    "before a noun": {"Spanish": "ante un nombre", "French": "devant un nom"},
}


def render_label(native_language, kind, tags, meaning=None):
    """
    One label in the learner's native language: "kind, meaning, tag, tag".
    English is the glossary's own key; any term missing a translation falls
    back to the English key so a gap shows as English, never as an error.
    """
    def term(key):
        if native_language == "English":
            return key
        return GLOSSARY.get(key, {}).get(native_language, key)

    parts = [term(kind)]
    if meaning:
        parts.append(meaning)
    parts.extend(term(t) for t in tags)
    return ", ".join(parts)
