from flask import jsonify

def make_response_dict(status, message, data=None, errors=None, error=None, status_code=None): # Add status_code
    resp = {"status": status, "message": message}
    if data is not None:
        resp["data"] = data
    if errors is not None:
        resp["errors"] = errors
    if error is not None:
        resp["error"] = error
    if status_code is not None: # Add this
        resp["status_code"] = status_code # Add this
    return resp

def success_response(message, data=None, status_code=200): # Add status_code, default 200
    return make_response_dict("success", message, data=data, status_code=status_code)

def error_response(message, errors=None, error=None, status_code=400): # Add status_code, default 400
    return make_response_dict("error", message, errors=errors, error=error, status_code=status_code)

def create_response(status, message, data=None, errors=None, error=None, status_code=None): # Add status_code
    # Note: The status_code from the dict is used by the route handler,
    # this parameter here is less critical but added for consistency if needed directly.
    return jsonify(make_response_dict(status, message, data, errors, error, status_code))
