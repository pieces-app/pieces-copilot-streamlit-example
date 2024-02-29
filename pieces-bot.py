import streamlit as st
import pieces_os_client as pos_client
from api import *

# Initialize variables
pieces_os_version = None
asset_ids = {}  # Asset ids for any list or search
assets_are_models = False
current_asset = {}
parser = None
query = ""

if "ws_manager" not in st.session_state:
    st.session_state.ws_manager = WebSocketManager()

# Initialize the ApiClient globally
configuration = pos_client.Configuration(host="http://localhost:1000")
api_client = pos_client.ApiClient(configuration)
api_instance = pos_client.ModelsApi(api_client)

# Get models
api_response = api_instance.models_snapshot()
models = {model.name: model.id for model in api_response.iterable if model.cloud or model.downloading}

# Set default model
default_model_name = "GPT-3.5-turbo Chat Model"
model_id = models[default_model_name]
models_name = list(models.keys())
default_model_index = models_name.index(default_model_name)



# Streamlit UI
st.title("Pieces Copilot Streamlit Bot")
url = "https://images.g2crowd.com/uploads/product/image/social_landscape/social_landscape_43395aae44695b07e11c5cb6aa5bcc60/pieces-for-developers.png"
st.image(url, caption="Pieces Copilot Streamlit Bot", use_column_width=True, width=10)

selected_model = st.selectbox("Choose a model", index=default_model_index, options=models_name, key="dropdown")
model_id = models[selected_model]

# Initialize chat history for Streamlit
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Ask me Anything - Pieces Copilot"}]

# Display chat messages from history on Pieces Bot app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Process and store Query and Response
def pieces_copilot_function(query):
    
    with st.chat_message("user"): # Displaying the User Message
        st.markdown(query)
    try:
        # Storing the User Message
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("assistant"):
            response = st.write_stream(st.session_state.ws_manager.message_generator(model_id, query))
        st.session_state.messages.append({"role": "assistant", "content": response})
    except Exception as e:
        print(f"Error occurred while asking the question: {e}")

# Accept the user input
query = st.chat_input("Ask a question to the Pieces Copilot")

# Calling the Function when Input is Provided
if query:
    if st.session_state.ws_manager.loading:
        st.warning('Hold on there is already a response generating', icon="⚠️")
    else:
        pieces_copilot_function(query)