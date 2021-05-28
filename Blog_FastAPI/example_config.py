from pydantic import BaseSettings


# rename this file to config.py and fill in the real info below
class Settings(BaseSettings):
    # generate a secret key - here is a simple python option - import secrets, secrets.token_hex(16)
    secret_key: str = "actual_secret_key"
    # domain of your api
    api_base_url: str = r"https://api.com"
    # domain of this blog website
    blog_base_url: str = r"https://blog.com"
    # local file paths for static and template files
    static_file_path: str = "/home/user/Blog_FastAPI/Blog_FastAPI/static"
    template_file_path: str = "/home/user/Blog_FastAPI/Blog_FastAPI/templates"


config_settings = Settings()
