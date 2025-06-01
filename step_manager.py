import json, os
from settings import SERVER, NODE

LOG_FILE = f"logs/{SERVER}-{NODE}.json"

# Загрузка выполненных этапов
def load_state():
    if not os.path.exists(LOG_FILE):
        return {}
    with open(LOG_FILE) as f:
        return json.load(f)

# Сохранение выполненного этапа
def save_state(state):
    with open(LOG_FILE, "w") as f:
        json.dump(state, f, indent=2)

# Выполнение или пропуск этапа
def run_step(name, func, *args, **kwargs):
    state = load_state()
    if state.get(name):
        print(f"Step \"{name}\" already completed")
        return
    print(f"Running step: {name}")
    try:
        result = func(*args, **kwargs)
        state[name] = True
        save_state(state)
        print(f"Step \"{name}\" completed")
        return result
    except Exception as e:
        print(f"Error in step \"{name}\": {e}")
