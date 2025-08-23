"""
@author: amannirala13
@date: 2025-8-23
@description: This module provides functionality to load environment variables from a .env file.
             It uses the python-dotenv package to read the .env file and set the environment variables accordingly.
"""
from dotenv import load_dotenv

def config_env() -> None:
    """
    Load environment variables from a .env file.
    This function uses the python-dotenv package to read the .env file located in the current directory
    and set the environment variables accordingly.
    If the .env file is not found, no error is raised, and the function simply returns.
    :example:
        # Assuming a .env file with the following content:
        # OPENAI_API_KEY=your_api_key_here
        config_env()
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        print(api_key)  # Output: your_api_key_here
    :return: None
    """
    load_dotenv(".env")
