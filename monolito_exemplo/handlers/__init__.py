def register_handlers(app):
    @app.post("/process")
    def process_handler(payload: dict):
        return {"received": payload}
