import shutil
import os

def cleanup_session(session_dir):
    if os.path.exists(session_dir):
        shutil.rmtree(session_dir)
