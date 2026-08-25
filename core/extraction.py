from google import genai
from google.genai import types
from dotenv import load_dotenv
from data.models import VocabPair, ExtractedVocabList


load_dotenv()
client = genai.Client()


def describe_image(image_bytes,mime_type):

    
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=["Describe what's in this image.", image_part]
        )
    except Exception as e:
        print("Oops, something went wrong on our end, please try again:",e)
        exit()        
        
        
    return response.text


def extract_vocab_from_image(image_bytes, mime_type):

    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    prompt = """
            scan the image for word pairs, which is a word followed by a separator such as
            ':' or '->' or other similar symbol, and then another word, for example 'house -> casa'. extract each pair and 
            save as a vocabPair object. store all the vocabPairs into a extractedVocabList object.

        """
    
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[prompt, image_part],
            config= types.GenerateContentConfig(
                            response_schema=ExtractedVocabList,
                            response_mime_type= "application/json"
                        )
        )
    except Exception as e:
        print("Oops, something went wrong on our end, please try again:",e)
        exit()       

    return response.parsed.pairs

