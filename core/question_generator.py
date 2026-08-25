from google import genai
from google.genai import types
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List
from data.models import Question,QuestionBatch

load_dotenv()
client = genai.Client()

def question_generator (source_term: str, target_term: str, source_language: str, target_language:str) -> Question:

    prompt = f""" {source_term} is the source term in the {source_language}. This is the language that the user already knows.
                {target_term} is the target term in the {target_language}. This is the language that the user is learning.
                Write a fill in the blanks language quiz type question using a translation of {source_term} from {source_language}.
                This question is meant to test how well the user knows the {target_term}. The sentence must include a specific descriptive detail or defining clue about {target_term} 
                so that it is the only word that could logically complete the sentence — not a generic statement 
                that many different words could equally complete.
                Here are examples of well-constrained questions:

                Situational/scenario-based (like the math exam one): "Este examen de matemáticas es muy ___, no entiendo nada." → difícil
                Cause-and-effect/reasoning-based: "Como no dormí anoche, hoy me siento muy ___." (Since I didn't sleep last night, today I feel very ___.) → cansado (tired)
                Comparison-based: "A diferencia de mi hermano, que es muy alto, yo soy bastante ___." (Unlike my brother, who is very tall, I am quite ___.) → bajo (short)

                Here are some bad exmaples:
                Too generic: "Mi ___ es muy grande." → fails because many nouns fit
                Definitional: "A standalone residential building where a family lives is a ___." → fails because it defines the word instead of using it naturally
                Leaks the answer: "My parents bought me a big furry ___. (perro)" → fails because the parenthetical directly reveals the translation

                Now write a similar question for: {target_term}
                The question should be a natural sentence phrased to test the user's knowledge of {target_language}
                Do NOT write the question as a dictionary-style definition of {target_term}. 
                The sentence should use the word naturally, in a realistic situation or context, 
                not describe or define what the word means.
                Use "_____" to mark where the blank goes. The blank is the {target_term}
                Do not use {source_term} in the question text.



            """

    


    try: 
        response = client.models.generate_content(
        model = "gemini-3.6-flash",
        contents = prompt,
        config = types.GenerateContentConfig(
            response_mime_type= "application/json",
            response_schema= Question

        )
    )

    except Exception as e:
        print("Oops, something went wrong on our end, please try again:",e)
        exit()        


    return response.parsed


def generate_question_batch (pairs:list[dict], source_language: str, target_language:str,batch_size:int) -> QuestionBatch:

    prompt = f""" {pairs} is a list of dictionaries and each dictionary is in the form "source term : target term" The source term (the first term) is in the
                {source_language}. This is the language that the user already knows. The target term (the second term) is in the {target_language}. This is the
                language that the user is learning.
                Write a batch of {batch_size} questions. One question per pair, in the same order Each question should be formed with the following guidelines:
                Write a fill in the blanks language quiz type question using a translation of source_term from {source_language}.
                This question is meant to test how well the user knows the target_term. The sentence must include a specific descriptive detail or defining clue about each pair's target term
                so that it is the only word that could logically complete the sentence — not a generic statement 
                that many different words could equally complete.

                "CRITICAL: every single question's sentence AND its answer must be entirely in {target_language}.
                Do not write any question in {source_language}. Double-check each question before finalizing — 
                the sentence language and the answer language must always match {target_language}."
                Here are examples of well-constrained questions:

                Situational/scenario-based (like the math exam one): "Este examen de matemáticas es muy ___, no entiendo nada." → difícil
                Cause-and-effect/reasoning-based: "Como no dormí anoche, hoy me siento muy ___." (Since I didn't sleep last night, today I feel very ___.) → cansado (tired)
                Comparison-based: "A diferencia de mi hermano, que es muy alto, yo soy bastante ___." (Unlike my brother, who is very tall, I am quite ___.) → bajo (short)

                Here are some bad exmaples:
                Too generic: "Mi ___ es muy grande." → fails because many nouns fit
                Definitional: "Un edificio residencial independiente con paredes y techo donde vive una sola familia es una ___." → fails
                because it defines the word instead of using it naturally
                Leaks the answer: "Mis padres me compraron un ___ grande y peludo. (perro)" → fails because the parenthetical directly reveals the translation
                
                CRITICAL: every single question's sentence AND its answer must be entirely in {target_language}.
                Do not write any question in {source_language}. Double-check each question before finalizing.
                
                Now write a similar question for target term
                The question should be a natural sentence phrased to test the user's knowledge of {target_language}
                Do NOT write the question as a dictionary-style definition of target term. 
                The sentence should use the word naturally, in a realistic situation or context, 
                not describe or define what the word means.
                Use "_____" to mark where the blank goes. The blank is the target_term
                Do not use source_term in the question text.



            """

    


    try: 
        response = client.models.generate_content(
        model = "gemini-3.5-flash-lite",
        contents = prompt,
        config = types.GenerateContentConfig(
            response_mime_type= "application/json",
            response_schema= QuestionBatch

        )
    )

    except Exception as e:
        print("Oops, something went wrong on our end, please try again:",e)
        exit()        


    return response.parsed.questions


   

