import os
import streamlit as st
from pytube import YouTube
import re
import openai

from dotenv import load_dotenv, find_dotenv
# Specify the path to your .env file
env_path = '/home/USER/.env/openai_api' # Change the Path
# Load the OpenAI API key from the .env file
load_dotenv(env_path)
openai.api_key = os.getenv('OPENAI_API_KEY')

def youtube_audio_downloader(link):

    yt = YouTube(link)

    # Check for valid youtube link
    if 'youtube.com' not in link and 'youtu.be' not in link:
        st.error('Invalid Youtube link!')
        return False
    
    # Downloading the Audio from the video
    audio = yt.streams.filter(only_audio=True).first()
    print('Downloading the Audiostream ...')
    output_file = audio.download()
    if os.path.exists(output_file):
        print('Done!')
    else:
        print('Error Downloading the file!')
        return False
    
    # rename into .mp3
    basename = os.path.basename(output_file)
    name, extension = os.path.splitext(basename)
    audio_file = f'{name}.mp3'

    # replace spaces with underscore
    audio_file =re.sub('\s+', '_', audio_file)
    os.rename(basename, audio_file)
    
    return audio_file

def transcribe(audio_file): # Add not_english=False to translate in english
    if not os.path.exists(audio_file):
        print('Audio file does not exist!')
        return False

    with open(audio_file, 'rb') as f:
        print('Starting transcribing ...', end='')
        transcript = openai.Audio.transcribe('whisper-1', f)
        print('Done!')

        name, extension = os.path.splitext(audio_file)
        transcript_filename = f'transcript-{name}.txt'
        with open(transcript_filename, 'w') as f:
            f.write(transcript['text'])

    return transcript_filename

def summarize(transcript_filename, language):
    if not os.path.exists(transcript_filename):
        print('Transcript file does not exist!')
        return False
    with open (transcript_filename) as f:
        transcript = f.read()

    system_prompt = 'I want you to act as a Life Coach that can create good summarize!'
    prompt = f'''Create a summary of the following text in {language}.
    Text: {transcript}

    Add a title to the summary in {language}. 
    Your summary should be informative and factual, covering the most important aspects of the topic. 
    Start your summary with an INTRODUCTION PARAGRAPH that gives an overview of the topc FOLLOWED
    by BULLET POINTS if possible AND end the summary with a CONCLUSION PHRASE. In {language}'''


    print('Starting summarizing ...', end='')
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo', # change the model to 'gpt-3.5-turbo-16k' for longer videos
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': prompt}
        ],
        # max_tokens=2048,
        temperature=1
    )

    print('Done')
    r = response['choices'][0]['message']['content']
    return r

def delete_files(*files):
    for file in files:
        if os.path.exists(file):
            os.remove(file)
            print(f'{file} deleted!')
        else:
            print(f'The file {file} does not exist')


def main():
    st.title('YouTube video summarizer')
    
    link = st.text_input('Enter the link of the YouTube video you want to summarize:')
    language = st.selectbox('Select the language of the summary:', ['german', 'english', 'france', 'spanish', 'albanian', 'polisch', 'italian', 'russian'])

    if st.button('Start'):
        if link:
            try:
                st.info('Editing can take from 1 minute to 10 minutes, depending on the length of the video.')
                # Initialize progress bar and status text
                progress = st.progress(0)
                status_text = st.empty()

                status_text.text('Download and transcribe the video...')
                progress.progress(25)  # Progress after downloading and transcribing
                mp3_file = youtube_audio_downloader(link)
                transcript_filename = transcribe(mp3_file)
                progress.progress(50)

                status_text.text('Create summary...')
                progress.progress(75)  # Progress after summarizing
                summary = summarize(transcript_filename, language)
                
                status_text.text('Summary:')
                st.markdown(summary)
                progress.progress(100)  # Progress after summary

                # Delete the files after creating the summary
                delete_files(mp3_file, transcript_filename)
            except Exception as e:
                st.write(str(e))
        else:
            st.write('Please enter a valid YouTube link.')


if __name__ == "__main__":
    main()