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
    response = self._{endpoint_type}("{endpoint}", add_header={add_headers}, remove_header={remove_headers})
"""