docker-compose up

# .env requirements

DATABASE_URL = "" //postgres
BUCKET_NAME = ""  //AWS bucket
SECRET_KEY = abc  // Any 
ELASTIC_SEARCH_API_KEY="" 
AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""
OPENAI_API_KEY=""  //chat gpt


# for running locally

create environment:
    eg: for mac:
        python3.8 -m venv venv
        source venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload