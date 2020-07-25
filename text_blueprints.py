all_headers_blueprint = """
\"\"\"
{all_headers}
\"\"\"
"""

request_description_blueprint = """
    Expected Request:
    {expected_request}
"""

response_description_blueprint = """
    Expected Response:
    {expected_response}
"""

method_description_blueprint = """
\"\"\"{request_description}{response_description}\"\"\"
"""

method_definition_blueprint = """
def {function_name}():
    payload = {payload}
    response = self._{endpoint_type}("{endpoint}", payload, add_header={add_headers}, remove_header={remove_headers})
"""

empty_payload_format = "payload = None\n"
empty_payload_param_format = ", payload"
empty_add_header_format = """, add_header=set()"""
empty_remove_header_format = """, remove_header=set()"""