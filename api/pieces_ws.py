import json
import websocket
import threading
import pieces_os_client
import queue
import time
WEBSOCKET_URL = "ws://localhost:1000/qgpt/stream"
TIMEOUT = 10  # seconds




class WebSocketManager:
    def __init__(self):
        self.ws = None
        self.is_connected = False
        self.response_received = None
        self.model_id = ""
        self.query = ""
        self.loading = False
        self.final_answer = ""
        self.open_event = threading.Event()  # wait for opening event
        self.conversation = None
        self.message_queue = queue.Queue()
        #self.QGPTRelevanceInput = pieces_os_client.QGPTRelevanceInput(seeds=)
        #self.message_compeleted = threading.Event()
        threading.Thread(target=self._start_ws).start()
        self.open_event.wait()
        
    def on_message(self,ws, message):
        """Handle incoming websocket messages."""
        try:
            response = pieces_os_client.QGPTStreamOutput.from_json(message)
            if response.question:
                answers = response.question.answers.iterable
                for answer in answers:
                    text = answer.text
                    if text:
                        self.message_queue.put(text)
                        print(text, end='')

            if response.status == 'COMPLETED':
                print("\n")
                self.conversation = response.conversation
                self.loading = False   # signal that the conversation is complete

        except Exception as e:
            print(f"Error processing message: {e}")

    def on_error(self, ws, error):
        """Handle websocket errors."""
        print(f"WebSocket error: {error}")
        self.is_connected = False

    def on_close(self, ws, close_status_code, close_msg):
        """Handle websocket closure."""
        print("WebSocket closed")
        self.is_connected = False

    def on_open(self, ws):
        """Handle websocket opening."""
        print("WebSocket connection opened.")
        self.is_connected = True
        self.open_event.set()

    def _start_ws(self):
        """Start a new websocket connection."""
        print("Starting WebSocket connection...")
        ws =  websocket.WebSocketApp(WEBSOCKET_URL,
                                         on_open=self.on_open,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        self.ws = ws
        ws.run_forever()
        

    def send_message(self):
        """Send a message over the websocket."""
        message = {
            "question": {
                "query": self.query,
                "relevant": {"iterable": []},
                "model": self.model_id
            },
            "conversation": self.conversation
        }
        json_message = json.dumps(message)

        if self.is_connected:
            try:
                self.ws.send(json_message)
                print("Response: ")
            except websocket.WebSocketException as e:
                print(f"Error sending message: {e}")
        else:
            raise ConnectionError("WebSocket connection is not open, unable to send message.")

    def close_websocket_connection(self):
        """Close the websocket connection."""
        if self.ws and self.is_connected:
            self.ws.close()
            self.is_connected = False

    def message_generator(self, model_id, query):
        """
        Stream messages from on message.
        This function is a generator that yields messages as they become available.
        """
        
        # Set loading to True and initialize model_id and query
        self.loading = True
        self.model_id = model_id
        self.query = query
        
        # Send the initial message
        self.send_message()
        
        # While loading is True, try to get messages from the queue
        while self.loading:
            try:
                # If a message is available, yield it
                yield self.message_queue.get(timeout=2)
            except queue.Empty:
                #endtime = time.time() + TIMEOUT
                #while self.message_queue.empty():
                    #remaining = endtime - time.time()
                    #if remaining <= 0.0:
                        #self.loading=False
                        #raise ConnectionError("Timeout")
                continue
        
        # Once loading is False, drain any remaining messages from the queue
        while not self.message_queue.empty():
            try:
                # If a message is available, yield it
                yield self.message_queue.get_nowait()
            except queue.Empty:
                # If the queue is empty, break the loop
                break
