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

