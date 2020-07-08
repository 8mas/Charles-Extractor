from typing import Callable, List, Dict, Tuple, Set
from collections import Counter
import base64
import json
import textwrap


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

    def _apply_transformer(self, transformer, transformer_type: str, mine_type=None):
        for index, json_element in enumerate(self.charles_session):
            if json_element[transformer_type]["sizes"]["body"] == 0:
                continue

            if mine_type:
                json_element[transformer_type]["mimeType"] = mine_type
                for h_index, header in enumerate(json_element[transformer_type]["header"]["headers"]):
                    if header["name"] == "Content-Type":
                        json_element[transformer_type]["header"]["headers"][h_index]["value"] = mine_type

            request_base64 = json_element[transformer_type]["body"]["encoded"]
            request_bytes = base64.b64decode(request_base64)
            new_request_bytes = transformer(request_bytes)
            new_request_bytes_base64 = base64.b64encode(new_request_bytes).decode()

            for h_index, header in enumerate(json_element[transformer_type]["header"]["headers"]):
                if header["name"] == "Content-Length":
                    json_element[transformer_type]["header"]["headers"][h_index]["value"] = len(new_request_bytes)

            json_element[transformer_type]["sizes"]["body"] = len(new_request_bytes)
            json_element[transformer_type]["body"]["encoded"] = new_request_bytes_base64
            self.charles_session[index] = json_element

    def _get_headers(self) -> Tuple[Set, Set, Set]:
        header_list: List[List[Tuple[str, str]]] = list()
        header_name_list: List[List[str]] = list()
        request_data: List[Dict] = list()
        endpoint_list = list()

        for json_element in self.charles_session:
            endpoint = json_element["request"]["header"]["firstLine"]
            if endpoint in endpoint_list:
                continue
            endpoint_list.append(endpoint)

            headers = []
            header_names = []
            for h_index, header in enumerate(json_element["request"]["header"]["headers"]):
                name = header["name"]
                value = header["value"]
                header_names.append(name)
                headers.append((name, value))
            header_name_list.append(header_names)
            header_list.append(headers)

            # TODO identify common request data
            request_content = json_element["request"]["body"]["encoded"]
            request_data.append(request_content)

        flatten_header_names = [name for header in header_name_list for name in header]
        c = Counter(flatten_header_names)

        common_headers = set()
        for key, item in c.items():
            if item / len(endpoint_list) > 0.5:
                common_headers.add(key)

        static_headers = set(header_list[0])
        for header in header_list[1:]:
            static_headers = static_headers & set(header)

        all_headers = set(c.keys())
        return common_headers, static_headers, all_headers

    def apply_request_transformer(self, mine_type=None):
        self._apply_transformer(self.request_transformer, "request", mine_type)

    def apply_response_transformer(self, mine_type=None):
        self._apply_transformer(self.response_transformer, "response", mine_type)

    def write_changes_to_session_file(self, path_to_session: str):
        data = json.dumps(self.charles_session)
        with open(path_to_session, "w") as session_file:
            session_file.write(data)