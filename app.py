from flask import Flask, render_template, request,  jsonify, send_file
from flask import abort, session, redirect, url_for, Response
from langchain_openai import ChatOpenAI
import os
import replicate
import fal_client
import json

JSON_FILE_PATH = "/Users/williamstanford/Cortina_Album_Art_Prototype/image_prompts.json"

ART_QUESTIONS = [
    {
        "name": "concept",
        "title": "What concept do you want your art to be about?",
        "options": [
            "Nature", "Urban", "Space", "Fantasy", "Mythology", "Technology", 
            "Underwater", "Dystopian", "Retro-futurism", "Dreamscape" "Cityscape",
            "Jungle", "Desert", "Nightlife", "Botanical", "Oceanic", "Cyberpunk",
            "Utopia", "Apocalyptic", "Folklore", "Hologram", "Bioluminescence",
            "Liquid", "Afrofuturism"
        ]
    },
    {
        "name": "feeling",
        "title": "How do you want your album to feel",
        "options": [
            "Energetic", "Calm", "Mysterious", "Joyful", 
            "Whimsical", "Nostalgic", "Dramatic", "Ethereal",
            "Uplifting", "Weird", "Mysterious", "Sad",
            "Powerful", "Anxious", "Melancholic", "Powerful", 
            "Happy", "Lonely", "Hopeful", "Playful",
            "Inspiring", "Relaxed", "Edgy", "Loving",
            "Gloomy", "Scary", "Warm", "Cold",
            "Overwhelming", "Disruptive", "Dreamy", "Emotional",
            "Ethereal", "Expressive", "Mystical", "Natural",
            "Profound", "Chaotic", "Angry", "Romantic",
            "Spiritual", "Surreal", "Heavenly"
        ]
    },
    {
        "name": "theme",
        "title": "Okay, what themes are you interested in?",
        "options": [
            "Love", "Loss", "Grief", "Adversity",
            "Society", "Self-Discovery", "Justice", "Adventure",
            "Bravery", "Self-Love", "Defeat", "Change",
            "Friendship"      
        ] 
    },
    {
        "name": "color_scheme",
        "title": "What sort of color schemes do you like?",
        "options": [
            "Vibrant", "Pastel", "Monochrome", "Earthy",
            "Neon", "Muted", "Cool-tones", "Warm-tones",
            "Metallic", "Gradient", "Analogous", "Complementary",
            "Triadic", "Tetradic", "Split-complementary", "Jewel tones",
            "Black and white", "Grayscale", "Neutral", "Vintage",
            "Retro", "Bold", "Red", "Orange", "Yellow", "Green", 
            "Blue", "Indigo", "Violet", "Cyan", "Magenta", "Pink",
            "Beige", "Brown", "Dark", "Neutral"
        ]
    },
    {
        "name": "style",
        "title": "Which of these visual styles inspire you",
        "options": [
            "Photography", "Collage", "Illustration", "8-bit", "Extremely Detailed",
            "Futuristic", "Renaissance Painting", "Abstract", "Neon Light",
            "Experimental", "Retro / Vintage" "Minimalist", "Surrealist",
            "Pop Art", "Impressionist", "Pixel Art", "Watercolor",
            "Art Nouveau", "Cubist", "Street Art", "Digital Painting",
            "Japanese Woodblock Print", "Oil Painting", "Geometric"
        ]
    }
]

LYRIC_QUESTIONS = [
    {
        "name": "lyric_inspiration",
        "title": "What inspires you?",
        "options": [
            "Nature", "Art", "Music", "Literature", "Science", 
            "Innovation", "Kindness", "Perseverance", "Creativity", 
            "Love", "Success stories", "Challenges", "Dreams", "History", 
            "Culture", "Space exploration", "Human resilience", "Family", 
            "Friends", "Personal growth", "Travel", "Philosophy", "Courage", 
            "Passion", "Beauty", "Progress", "Spirituality", "Diversity", 
            "Education", "Teamwork", "Compassion", "Imagination", 
            "Problem-solving", "Self-discovery", "Social change", "Athletics",
            "Mentors", "Overcoming adversity", "Acts of generosity"
        ]
    },
    {
        "name": "lyric_feeling",
        "title": "How do you want your lyrics to feel",
        "options": [
            "Joyful", "Romantic", "Heartbreaking", "Nostalgic",
            "Serene", "Rebellious", "Hopeful", "Longing",
            "Proud", "Melancholic", "Passionate", "Liberating",
            "Grateful", "Struggle-filled", "Exciting", "Redemptive",
            "Content", "Desiring", "Empathetic", "Mournful",
            "Inspiring", "Angry", "Blissful", "Journey-like",
            "Courageous", "Sad", "Wondrous", "Empowering",
            "Optimistic", "Regretful", "Euphoric", "Transformative",
            "Compassionate", "Yearning", "Triumphant", "Healing",
            "Enthusiastic", "Betrayed", "Energetic", "Introspective",
            "Confident", "Sorrowful", "Appreciative", "Resilient",
            "Determined", "Forgiving", "Elated", "Unifying",
            "Tender", "Defiant", "Amazing", "Awakening",
            "Playful", "Despair-filled", "Curious", "Uplifting",
            "Fulfilled", "Lonely", "Warm", "Transcendent"
        ]
    },
    {
        "name": "lyric_music_preferences",
        "title": "What type of music should these lyrics take inspiration from?",
        "options": [
            "Classical", "Jazz", "Rock", "Pop", "Hip-hop", 
            "Country", "Blues", "Electronic", "R&B", "Reggae", 
            "Folk", "Metal", "Punk", "Soul", "Funk", 
            "Disco", "Techno", "House", "Ambient", "Gospel", 
            "Opera", "Indie", "Alternative", "Grunge", "Ska", 
            "Dubstep", "Trance", "Salsa", "Bossa Nova", "Flamenco", 
            "Bluegrass", "Swing", "Baroque", "New Age", "Psychedelic",
            "Grime", "Trap", "K-pop", "Bachata", "Afrobeat"
        ]
    }
]


app = Flask(__name__)
app.secret_key = os.urandom(24)


LLM = ChatOpenAI(model=model,
  temperature=0,
  max_tokens=None,
  timeout=None,
  max_retries=2,)

def art_prompt(style):

  prompt = f"""
  Given a user style of: {style}
  Write a description of some album art using natural language that incorporates 
  these elements. Keep it short, and emphasize wording that would either not generate
  people, or instead generate silhouettes. 
  Emphasize environments, layouts, designs. 
  If you describe a human silhouette, make it racially diverse. 
  keep it concise, no more than 30 words
  """
  return prompt


@app.route('/')
def attract():
    return render_template('attract.html')

@app.route('/find-your-voice')
def find_your_voice():
    return render_template('find_your_voice_intro.html')

@app.route('/start-from-scratch', methods=['GET', 'POST'])
def start_from_scratch():
    if request.method == 'POST':
        
        inspiration = request.form.get('lyric_inspiration', '')
        feeling = request.form.get('lyric_feeling', '')
        music_preferences = request.form.get('lyric_music_preferences', '')

        return redirect(url_for('generate_lyrics', 
                                inspiration=inspiration,
                                feeling=feeling,
                                music_preferences=music_preferences))
        
    return render_template('start_from_scratch.html', questions=LYRIC_QUESTIONS)


@app.route('/find-your-voice/generate-lyrics', methods=['GET', 'POST'])
def generate_lyrics():
    if request.method == 'POST':
        data = request.json
        feedback_type = data.get('feedback_type', 'dropdown')
        line_selection = data.get('line_selection', 'all')
        
        if feedback_type == 'text':
            feedback = data.get('feedback', '')
        else:
            emotion = data.get('emotion', '')
            structure = data.get('structure', '')
            theme = data.get('theme', '')
            feedback = f"Emotion: {emotion}, Structure: {structure}, Theme: {theme}"

        lyric_features = session.get('lyric_features', '')
        inspiration = session.get('inspiration', '')
        feeling = session.get('feeling', '')
        music_preferences = session.get('music_preferences', '')
        full_lyrics = data.get('full_lyrics', '')

        line_instruction = "all lines"
        if line_selection == 'single':
            line_instruction = f"line {data.get('single_line', '')}"
        elif line_selection == 'range':
            line_instruction = f"lines {data.get('start_line', '')} to {data.get('end_line', '')}"

        regeneration_prompt = f"""
        Original lyric features:
        {lyric_features}

        Current lyrics:
        {full_lyrics}

        User feedback:
        {feedback}

        Please regenerate {line_instruction} of the lyrics based on the user's feedback.
        Ensure the new lyrics incorporate the user's feedback while still adhering to the original inspiration, feeling, and music style.
        DO NOT use the same lyrics.
        """

        generated_lyrics = LLM.invoke(regeneration_prompt).content

        session['generated_lyrics'] = generated_lyrics
        session['feedback'] = feedback

        return jsonify({'regenerated_lyrics': generated_lyrics})

    inspiration = request.args.get('inspiration', '')
    feeling = request.args.get('feeling', '')
    music_preferences = request.args.get('music_preferences', '')

    session['inspiration'] = inspiration
    session['feeling'] = feeling
    session['music_preferences'] = music_preferences
    
    lyric_features = f"""
    Generated 8 lines of lyrics to a song. 
    First 4 should be the first verse. 
    The next 4 should be a chorus.
    
    The song should take inspiration from {inspiration}
    The emotional elements present in the lyrics should be {feeling}
    The lyrics should match the style of lyrics present in {music_preferences}

    """
    print(lyric_features)
    
    if 'timestamp' in request.args:
        generated_lyrics = LLM.invoke(lyric_features).content
    else:
        generated_lyrics = session.get('generated_lyrics')
        if not generated_lyrics:
            generated_lyrics = LLM.invoke(lyric_features).content
    
    session['generated_lyrics'] = generated_lyrics

    return render_template('generated_lyrics.html', 
                           inspiration=inspiration,
                           feeling=feeling,
                           music_preferences=music_preferences,
                           lyrics=generated_lyrics,
                           lyric_features=lyric_features)


@app.route('/regenerate-lyrics', methods=['POST'])
def regenerate_lyrics():
    data = request.json
    
    feedback_type = data.get('feedback_type')
    line_selection = data.get('line_selection')
    selected_text = data.get('selected_text')
    full_lyrics = data.get('full_lyrics')
    
    if feedback_type == 'text':
        feedback = data.get('feedback', '')
    else:
        emotion = data.get('emotion', '')
        structure = data.get('structure', '')
        theme = data.get('theme', '')
        feedback = f"Emotion: {emotion}, Structure: {structure}, Theme: {theme}"

    lyric_features = session.get('lyric_features', '')
    inspiration = session.get('inspiration', '')
    feeling = session.get('feeling', '')
    music_preferences = session.get('music_preferences', '')

    regeneration_prompt = f"""
    Original lyric features:
    {lyric_features}

    Full lyrics (including section headers):
    {full_lyrics}

    Selected text to regenerate:
    {selected_text}

    User feedback:
    {feedback}

    Line selection: {line_selection}

    Please regenerate only the selected portion of the lyrics based on the user's feedback.
    Incorporate the feedback while still adhering to the original inspiration ({inspiration}), feeling ({feeling}), and music style ({music_preferences}).
    The regenerated lyrics should seamlessly fit into the existing structure and match the number of lines in the selected text.
    Do not include or modify any section headers (lines starting with **) in your regeneration.

    Only return the regenerated portion, not the full lyrics.
    Ensure that the regenerated lyrics maintain the same structure and line count as the selected text.
    """

    try:
        regenerated_lyrics = LLM.invoke(regeneration_prompt).content
        response_data = {
            'regenerated_lyrics': regenerated_lyrics.strip()
        }
        
        if line_selection == 'single':
            response_data['single_line'] = data.get('single_line')
        elif line_selection == 'range':
            response_data['start_line'] = data.get('start_line')
            response_data['end_line'] = data.get('end_line')
        
        return jsonify(response_data)
    except Exception as e:
        print("Error during regeneration:", str(e)) 
        return jsonify({'error': 'Failed to regenerate lyrics'}), 500
        
@app.route('/extend-lyrics', methods=['POST'])
def extend_lyrics():
    data = request.json
    current_lyrics = data.get('current_lyrics', '')
    
    extension_prompt = f"""
    Current lyrics:
    {current_lyrics}

    Please extend these lyrics by adding another verse or chorus.
    Maintain the same style, theme, and emotional elements as the existing lyrics.

    Return the current lyrics and the new verse or chorus.
    """

    extended_lyrics = LLM.invoke(extension_prompt).content

    return jsonify({'extended_lyrics': extended_lyrics})

@app.route('/explain-lyrics', methods=['GET','POST'])
def explain_lyrics():
    data = request.json
    feedback_type = data.get('feedback_type', 'dropdown')
    line_selection = data.get('line_selection', 'all')
    
    if feedback_type == 'text':
        feedback = data.get('feedback', '')
    else:
        emotion = data.get('emotion', '')
        structure = data.get('structure', '')
        theme = data.get('theme', '')
        feedback = f"Emotion: {emotion}, Structure: {structure}, Theme: {theme}"

    lyric_features = session.get('lyric_features', '')
    inspiration = session.get('inspiration', '')
    feeling = session.get('feeling', '')
    music_preferences = session.get('music_preferences', '')
    full_lyrics = data.get('full_lyrics', '')

    line_instruction = "all lines"
    if line_selection == 'single':
        line_instruction = f"line {data.get('single_line', '')}"
    elif line_selection == 'range':
        line_instruction = f"lines {data.get('start_line', '')} to {data.get('end_line', '')}"

    explanation_prompt = f"""
    Analyze the following lyrics and explain how they reflect the given inspiration, feeling, and music style:

    Lyrics:
    {full_lyrics}

    Inspiration: {inspiration}
    Feeling: {feeling}
    Music Style: {music_preferences}

    Please provide a brief explanation for each aspect:
    1. How each of the user selected inpirations ({inspiration}) is reflected in the lyrics
    2. How each of the user selected feelings ({feeling}) is conveyed through the lyrics
    3. How the music style ({music_preferences}) influences the lyrical structure or content

    Keep each explanation concise, about 2-3 sentences each. 
    Add paragraph breaks for each of the musical features explained.
    """

    #If there is feedback, explain how the feedback altered the lyrics as well.
    #4. How the feedback: {feedback} for lines: {line_instruction} altered the lyrics.
    #Only add this point if there is feedback. Do not add the fourth point if there is no feedback.
   

    explanation = LLM.invoke(explanation_prompt).content

    class PrettyJSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, str):
                return obj.replace('\n', '\\n')
            return super().default(obj)

    response_data = {
        'explanation': explanation
    }

    return Response(
        json.dumps(response_data, cls=PrettyJSONEncoder, ensure_ascii=False),
        mimetype='application/json'
    )
    
@app.route('/notebook')
def notebook():
    saved_lyrics = session.get('saved_lyrics', [])
    feedback = session.get('feedback', '')
    artists = session.get('artists', '').split(',')
    return render_template('notebook.html', lyrics=saved_lyrics, feedback=feedback, artists=artists)

@app.route('/start-with-lyric', methods=['GET', 'POST'])
def start_with_lyric():
    if request.method == 'POST':
        return jsonify({
            'generatedLyrics': [
                request.json['userLyric'],
                "A follow-up line to your lyric",
                "Another line inspired by your input",
                "A fourth line to complete the verse"
            ]
        })
    return render_template('start_with_lyric.html')
    
@app.route('/pick-up-session', methods=['GET', 'POST'])
def pick_up_session():
    if request.method == 'POST':
        session_code = request.json['sessionCode']
        return jsonify({
            'isValid': True,
            'savedLyrics': [
                "First line of your previous session",
                "Second line you wrote last time",
                "Third line from before"
            ]
        })
    return render_template('pick_up_session.html')

@app.route('/select-user', methods=['POST'])
def select_user():
    user_type = request.form.get('user_type')
    session['user_type'] = user_type
    return redirect(url_for('activity_selection'))

@app.route('/activity-selection')
def activity_selection():
    return render_template('activity_selection.html')

@app.route('/remix-otis')
def remix_otis():
    return render_template('remix_otis.html')

@app.route('/style-questions', methods=['GET', 'POST'])
def style_questions():
    if request.method == 'POST':
        concept = request.form.get('concept', '')
        feeling = request.form.get('feeling', '')
        theme = request.form.get('theme', '')
        color_scheme = request.form.get('color_scheme', '')
        style = request.form.get('style', '')
        
        prompt = f"{concept}, {feeling}, {theme}, {color_scheme} colors, {style} style album art"
        
        session['art_prompt'] = prompt
        
        return redirect(url_for('find_your_style', prompt=prompt))
    
    return render_template('style_questions.html', questions=ART_QUESTIONS)

@app.route('/find-your-style', methods=['GET', 'POST'])
def find_your_style():
    if request.method == 'POST':
        
        user_selections = request.form.get('prompt', '')
        art_desc = art_prompt(user_selections)
        prompt = LLM.invoke(art_desc).content
        model = "fal-ai/flux/schnell"
        
        handler = fal_client.submit(
            model,
            arguments={
                "prompt": prompt,
                "image_size": "square"
            },
            )
        result = handler.get()
        image_url = result['images'][0]["url"]


        return jsonify({
            'image_url': image_url,
            'prompt': prompt
        }) 
        
    return render_template('find_your_style.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)



