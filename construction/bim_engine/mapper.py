class BIMMapper:
    def map_to_template(self, input_data):
        if input_data["element"] == "wall":
            return "wall.alvenaria.v1"
        raise Exception("Template não encontrado")
