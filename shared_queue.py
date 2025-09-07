import queue

# This file holds the single, shared UI update queue.
# Both main.py and brain.py will import this file to access the same queue object.
ui_update_queue = queue.Queue()