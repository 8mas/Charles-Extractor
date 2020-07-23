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

    class MethodBlueprint:
        def __init__(self):
            self.function_name = None
            self.rest_type = None
            self.endpoint = None
            self.expected_request = None
            self.expected_response = None
            # Which extra headers for this function
            self.extra_headers = []
            self.unused_headers = []

        def __hash__(self):
            return hash(self.function_name)

        def __eq__(self, other):
            if not isinstance(other, type(self)): return NotImplemented
            return self.function_name == other.function_name

    def _get_method_information(self, common_headers):
        method_blueprint_list = list()

        for json_element in self.charles_session:
            method_blueprint = self.MethodBlueprint()

            rest_type = json_element["method"]
            endpoint: str = json_element["path"]
            function_name = rest_type + endpoint[1:].replace("/", "_")
            method_blueprint.function_name = function_name

            if method_blueprint in method_blueprint_list:
                continue

            method_blueprint.rest_type = rest_type
            method_blueprint.endpoint = endpoint

            if json_element["request"]["sizes"]["body"] == 0:
                method_blueprint.expected_request = "Empty"
            else:
                decoded_request = base64.b64decode(json_element["request"]["body"]["encoded"]).decode()
                request_json = json.loads(decoded_request)
                method_blueprint.expected_request = json.dumps(request_json, indent=4)

            if json_element["response"]["sizes"]["body"] == 0:
                method_blueprint.expected_response = "Empty"
            else:
                decoded_request = base64.b64decode(json_element["response"]["body"]["encoded"]).decode()
                response_json = json.loads(decoded_request)
                method_blueprint.expected_response = json.dumps(response_json, indent=4)

            request_headers = set()
            for header in json_element["request"]["header"]["headers"]:
                name = header["name"]
                request_headers.add(name)

            method_blueprint.extra_headers = request_headers - common_headers
            method_blueprint.unused_headers = common_headers - request_headers
            method_blueprint_list.append(method_blueprint)
        return method_blueprint_list

    def generate_method_blueprint(self, skip_hints="response"):
        common_headers, static_headers, all_headers = self._get_headers()
        method_blueprint_list = self._get_method_information(common_headers)

        headers_print = dict(static_headers)
        for name in common_headers:
            if name not in headers_print.keys():
                headers_print[name] = "TODO_Define"

        dump_file = open("out.py", "w")

        headers = f"""
        # All headers
        \"\"\"
        {all_headers}
        \"\"\"
        # Headers
        common_headers = {json.dumps(dict(headers_print), indent=12)}
        """
        dump_file.write(headers)

        CURRENT_INDENT_LEVEL = 12
        for method_blueprint in method_blueprint_list:
            method_text = (
                f"""
            \"\"\"
            """

                f"""{
                "Expected Request:"
                f"{textwrap.indent(method_blueprint.expected_request, ' ' * CURRENT_INDENT_LEVEL)}"
                if skip_hints != "all" and skip_hints != "request" else ""}
            """

                f"""{
                "Expected response:" +
                f"{textwrap.indent(method_blueprint.expected_response, ' ' * CURRENT_INDENT_LEVEL)}"
                if skip_hints != "all" and skip_hints != "response" else ""} 
            """

                f"""
            \"\"\"
            """

                f"""
            def {method_blueprint.function_name}():
                self._{method_blueprint.rest_type.lower()}"""
                f"""("{method_blueprint.endpoint}"{f", add_header={method_blueprint.extra_headers}" if method_blueprint.extra_headers else ''} """
                f"""{f", remove_header={method_blueprint.unused_headers}" if method_blueprint.unused_headers else ''}) """
            )

            method_text = textwrap.dedent(method_text)
            dump_file.write(method_text)
        dump_file.close()

    def apply_request_transformer(self, mine_type=None):
        self._apply_transformer(self.request_transformer, "request", mine_type)

    def apply_response_transformer(self, mine_type=None):
        self._apply_transformer(self.response_transformer, "response", mine_type)

    def write_changes_to_session_file(self, path_to_session: str):
        data = json.dumps(self.charles_session)
        with open(path_to_session, "w") as session_file:
            session_file.write(data)