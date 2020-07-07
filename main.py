from typing import Callable
import base64
import json


class CharlesSessionHacker:
    def __init__(self, path_to_session: str, request_transformer: Callable[[bytes], bytes] = None,
                 response_transformer: Callable[[bytes], bytes] = None):
        with open(path_to_session, "r") as session_file:
            session_data = session_file.read()
        try:
            self.charles_session: dict = json.loads(session_data)
        except Exception as e:
            print("Session could not be decoded. Faulty format (not json)?")

        self.request_transformer = request_transformer if request_transformer else lambda x: x
        self.response_transformer = response_transformer if response_transformer else lambda x: x

    def _apply_transformer(self, transformer, transformer_type: str):
        for index, json_element in enumerate(self.charles_session):
            if json_element[transformer_type]["sizes"]["body"] == 0:
                continue

            request_base64 = json_element[transformer_type]["body"]["encoded"]
            request_bytes = base64.b64decode(request_base64)
            new_request_bytes = transformer(request_bytes)
            new_request_bytes_base64 = base64.b64encode(new_request_bytes).decode()

            json_element[transformer_type]["sizes"]["body"] = len(new_request_bytes)
            json_element[transformer_type]["body"]["encoded"] = new_request_bytes_base64
            self.charles_session[index] = json_element

    def extract_resource_path(self):
        pass

    def generate_method_blueprint(self):
        pass

    def apply_request_transformer(self):
        self._apply_transformer(self.request_transformer, "request")

    def apply_response_transformer(self):
        self._apply_transformer(self.response_transformer, "response")

    def write_changes_to_session_file(self, path_to_session: str):
        data = json.dumps(self.charles_session)
        with open(path_to_session, "w") as session_file:
            session_file.write(data)


