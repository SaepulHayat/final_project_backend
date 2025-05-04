from flask import jsonify

def make_response_dict(status, message, data=None, errors=None, error=None):
    resp = {"status": status, "message": message}
    if data is not None:
        resp["data"] = data
    if errors is not None:
        resp["errors"] = errors
    if error is not None:
        resp["error"] = error
    return resp

def success_response(message, data=None):
    return make_response_dict("success", message, data=data)

def error_response(message, errors=None, error=None):
    return make_response_dict("error", message, errors=errors, error=error)

def create_response(status, message, data=None, errors=None, error=None):
    return jsonify(make_response_dict(status, message, data, errors, error))
