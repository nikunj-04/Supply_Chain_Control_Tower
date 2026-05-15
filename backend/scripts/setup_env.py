"""Copy .env.example to .env on first run."""
import shutil
import os

env_example = '.env.example'
env_file = '.env'

if not os.path.exists(env_file) and os.path.exists(env_example):
    shutil.copy(env_example, env_file)
    print(f"Created {env_file} from {env_example}")
