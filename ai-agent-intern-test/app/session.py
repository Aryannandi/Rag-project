sessions = {}


def get_history(session_id="default"):
    if session_id not in sessions:
        sessions[session_id] = []

    return sessions[session_id]


def add_message(session_id, user_message, assistant_message):
    if session_id not in sessions:
        sessions[session_id] = []

    sessions[session_id].append({
        "user": user_message,
        "assistant": assistant_message
    })


def clear_session(session_id="default"):
    if session_id in sessions:
        sessions[session_id] = []