
# Charles-Extractor
Script for automatically extracting python methods for all endpoints of a [charles](https://www.charlesproxy.com/) *json* session.
For the request and response body functions can be specified which are then applied to them e.g. if they are encrypted.

Can provide the expected request and response body as comment.
Identifies which headers are set most often and sets special headers when needed.

    def POST_v10_migration_password_register():  
	    payload = {  
			"migration_password": "XYZ"  
		}
	    response = self._POST("/v1.0/migration/password/register", payload, add_header={'Header-to-add'}, remove_header={'Header-to-remove'}

Creates the sequence of the called endpoints (todo)

More my own project, but useful if one reverse engineer an app which use many different endpoints.
