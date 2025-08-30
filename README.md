# Instructions to run:

## Frontend:
- cd frontend
- npm i --legacy-peer-deps
- npm start

## Backend:
- pip install -r requirements.txt
- python .\backend\app.py


## Things to put in your .env file:
- GOOGLE_API_KEY = *<your_gemini_key>*
- SOURCE_FOLDER = *<the_full_path_to_your_MeDocs_directory(include MeDocs in the path)>*
- JWT_SECRET_KEY = "84be622f951abd78963b0c11d4b10043be570fb022863588f7fbe7471653659a" or you can make your own
- JWT_ALGORITHM = "HS256"
- SESSION_SECRET_KEY = "2b88100748c91b37b8dab631c9633493cbbbc3657c03345b50ef40aeb7ae70c3" or you can make your own
- CHROMADB_PATH = *<the_full_path_to_where_you_want_your_chromadb_database_to_be>*
