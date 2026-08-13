with open('cv-backend-core/app/main.py', 'r') as f:
    text = f.read()

start = text.find('def create_application() -> FastAPI:')
end = text.find('    app = FastAPI(', start)

if start != -1 and end != -1:
    before = text[:start + len('def create_application() -> FastAPI:\n')]
    after = text[end:]
    with open('cv-backend-core/app/main.py', 'w') as f:
        f.write(before + after)
        print("FIX APPLIED")
else:
    print("FAILED TO FIND")
