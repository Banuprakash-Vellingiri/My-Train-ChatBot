#=================================================== My Train ChatBot ================================================================================

#Importing dependencies
import streamlit as st
from streamlit_chat import message
#--------------------------------------------------------------
import os
import random
import warnings
warnings.filterwarnings("ignore")
#--------------------------------------------------------------
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain.chains import create_sql_query_chain
#--------------------------------------------------------------
import re
import speech_recognition as sr
import pickle
#=================================================== Streamlit Page Configuration ======================================================================
st.set_page_config (
                    page_title="My Train ChatBot by Banuprakash Vellingiri",
                    page_icon= "🚂",  
                    initial_sidebar_state="expanded",  
                   )

#---------------------------------------------------------------------------------------------
#Heading 
heading_text = "# <center><span style='color:#0b92e6'>🚂 My Train ChatBot</span></center>"
st.markdown(heading_text, unsafe_allow_html=True)
#---------------------------------------------------------------------------------------------
text = "<center><strong>📅 Inquire About The Schedules Of Trains Operated By Indian Railways</strong></center>"
st.write(text, unsafe_allow_html=True)
#-----------------------------------------------------------------------------------------------
st.image(r"cover_image.png", use_column_width=True)
st.text("🔔Note: Use only English Language as Input")
st.markdown("*"*100)

#================================================= Lang Chain and Gemini LLM Connection ===============================================================
os.environ["GEMINI_API"]= "AIzaSyDssnjSoToexad71K-09nJYgnUWcH0SPgw"
llm = ChatGoogleGenerativeAI(model="gemini-pro", convert_system_message_to_human=True,google_api_key=os.environ.get("GEMINI_API"),temperature=0.0)
#================================================= Loading Whisper Model =============================================================================
#Base Model
with open("whisper_base_model.pkl", "rb") as file:
    whisper_model = pickle.load(file)
#================================================== MYSQL Database Connection ==========================================================================
db_user = "root"
db_password = "952427"
db_host = "localhost"
db_name = "train_db"
#----------------------------------------------------------------------------------------------
db = SQLDatabase.from_uri(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}")
#================================================== Prompts =============================================================================================
prompt = """
                "Imagine you're an AI designed specifically to provide information on Indian train availabilities. If the user's query contains spelling mistakes  or grammatical mistakes, attempt to comprehend the context and adjust accordingly.

                Example 1: If asked about Indian train details or schedules,like for example tell me the trains available from  X to Y , or asking for train times from X to Y or asking for train numbers from X to Y or count number of unique train numbers or any query related to train scedule database respond simply with 'yes'.

                Example 2: If asked about your creator, reply with 'I am 'My Train ChatBot', created by 👨🏻‍💻 Mr. Banuprakash Vellingiri. I am equipped with Gemini LLM and LangChain technologies to provide Indian train availabilities and schedules.'

                Example 3: For queries unrelated to Indian train details or offensive questions, reply with '🙁 Apologies, I'm not equipped to address that query. Please feel free to ask about train schedules or availability instead.'

                Example 4: If asked about your well-being, respond with variations like:

                - 'I'm good. Feel free to ask about Indian Railways train schedules or details if you need.'
                - 'I'm okay. I'm ready to answer your queries about Indian Railways train schedules or details.'
                - 'I'm good. Ask me  questions about Indian Railways train schedules or details'

                Example 5: If the question pertains to train details or schedules for a country other than Indian cities or towns, respond with:
                - 'Sorry for any confusion, but could you please ask me about train times for Indian Railways only?'
                - 'I'm sorry, but could you assist me with Indian Railways train schedules exclusively?'
                - 'Apologies, but I'm only able to provide train details for Indian Railways right now.'
                - 'Sorry if it's inconvenient, but could you limit the questions to Indian Railways train info, please?'
                - 'I apologize, but could you keep the questions about trains restricted to Indian Railways only?'

                Example 6: For questions like for example 'what is the capital of India', respond with 'Apologies, I'm not equipped to address that query. Please feel free to ask about train schedules or availability instead.'

                Example 7: If the user types empty space(s) like for example "  " or " " etc.., respond with 'Sorry, Invalid Query❗'"

                Example 8: If the user types hi, hello, whats up like that, respond with 'Hi,Ask me  questions about Indian Railways train schedules or details'"

                Example 9: If the user inputs "bye", "see you again",Thanks bye, or any queries related to leaving, reply with "Alright, thank you for using our service! Remember, I'm here whenever you need assistance. Bye!" or
                        "Thanks for reaching out! Don't hesitate to return if you have more questions or need further assistance. Bye!",or
                        "Thank you for your inquiry! Feel free to come back anytime if you require any help or have additional questions. Goodbye!"
]
"""
#-----------------------------------------------------------------------------------------------------------------
not_available_response_list=[
                            "😔Apologies for the inconvenience, but what you're seeking is currently unavailable. Can I aid you in locating a suitable alternative?",
                            "🙁Regrettably, what you're looking for is not available at the moment. Is there anything else I can assist you with?",  
                            "😔I regret to inform you that what you're looking for is presently unavailable. However, can I assist you in finding a comparable alternative?"
                           ]
#======================================================================================================================================================
#Fuction to query MySQL database and for output response 
def handle_query(llm,db,user_question):
  try:
        generate_query = create_sql_query_chain(llm, db,)
        query = generate_query.invoke({"question":user_question})
        query = query.replace(' JUNCTION', '').replace(' JN', '')
        query = query.replace(' NR', '')
        query = query.strip('```sql').strip('```')
        print(query)
        #-------------------------------------------------------------------------------------
        if query.startswith("SELECT") or query.startswith("\nSELECT") :
            print("Querying MySQL database")
            execute_query = QuerySQLDataBaseTool(db=db)
            results=execute_query.invoke(query)
            print (results)
            if not results.strip():
              print("Not available")
              return random.choice(not_available_response_list)
            else:
               output= llm.invoke( f"{query}Given the SQL query provided, the output appears as follows: {results}.convert this output into natural language based on the query with easily understandable manner.")   
               print(output.content)
               return output.content
        if query.startswith("DELETE")or query.startswith("ALTER") :
            return "Sorry, Access Denied❗"
        else:
            return random.choice(not_available_response_list)
        #-------------------------------------------------------------------------------------
  except Exception as error:
        print(error)
        return random.choice(not_available_response_list)
#======================================================================================================================================================
#Finction for input Assessment
def input_assessment(llm,db,user_question):
      response= llm.invoke(f"'{prompt}'+ The question is :'{user_question}'")
      print(response)
      if response.content.lower().startswith("yes"):
          print("yes")
          return handle_query(llm,db,user_question)
      else:
          return response.content
      
#======================================================================================================================================================
#Function for converting Voice to Text 
def voice_input(audio_file):
     result = whisper_model.transcribe(audio_file)
     st.session_state['past'].append(result["text"])
     #st.markdown(result["text"])
     user_voice_input=result["text"]
     #st.markdown(input_assessment(llm,db,user_voice_input))
     st.session_state['generated'].append(input_assessment(llm,db,user_voice_input))
#======================================================================================================================================================
#Chat History
if 'history' not in st.session_state:
        st.session_state['history'] = []

if 'generated' not in st.session_state:
        st.session_state['generated'] = ["👋 Hello, Ask Me About Train Schedules 🚊"]

if 'past' not in st.session_state:
         st.session_state['past'] = ["hi"]
#----------------------------------------------------------------------------------        
#container for the chat history
response_container = st.container()
#container for the user's text input
container = st.container()
 #----------------------------------------------------------------------------------
with container:
        #----------------------------------------------------------------------------------
        #Text input
        with st.form(key='my_form', clear_on_submit=True):
            user_query = st.text_input(":blue[Text Input:]", placeholder="Your Quries ", key='input')
            submit_button = st.form_submit_button(label='Send')

        if submit_button and user_query:
            output = input_assessment(llm,db,user_query)
            st.session_state['past'].append(user_query)
            st.session_state['generated'].append(output)
        #----------------------------------------------------------------------------------
        #Voice input
        voice_input_button=st.button("🎙️:blue[Voice Input]")
        if voice_input_button:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
             with st.spinner("Capturing"):
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source)
             with open("voice_input.wav", "wb") as f:
                    f.write(audio.get_wav_data())  
             audio_input="voice_input.wav"
             voice_input(audio_input)


if st.session_state['generated']:
        with response_container:
            for i in range(len(st.session_state['generated'])):
              if i==0:
                    # message(st.session_state["past"][i], is_user=True, key=str(i) + '_user', avatar_style="big-smile")
                    message(st.session_state["generated"][i], key=str(i), avatar_style="thumbs")
              else:
                   message(st.session_state["past"][i], is_user=True, key=str(i) + '_user', avatar_style="big-smile")
                   message(st.session_state["generated"][i], key=str(i), avatar_style="thumbs")
st.text("Developed By ❤️ Banuprakash Vellingiri")
#================================================================================================================

