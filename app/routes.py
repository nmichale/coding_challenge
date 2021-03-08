import logging

import flask
from flask import Response, request, jsonify

from . import get_data

app = flask.Flask("user_profiles_api")
logger = flask.logging.create_logger(app)
logger.setLevel(logging.INFO)

REQUIRED_ARGS = ['github_org', 'bitbucket_org']


@app.route('/profile', methods=['GET'])
def profile() -> Response:
    """
    Rest API endpoint for code challenge. Merges Github and Bitbucket profile metadata.

    @return: Flask response.
    """
    kwargs = request.args.to_dict()

    for req_args in REQUIRED_ARGS:
        if req_args not in kwargs:
            return Response(f"{req_args} is a required argument that was not detected.", status=400)

    try:
        out = get_data.run_profile(**kwargs)
        return jsonify(out)
    except get_data.APIError as e:
        return Response(str(e), status=e.status_code)
    except Exception as e:
        return Response(f"Unexpected error: {str(e)}", response=500)


@app.route("/health-check", methods=["GET"])
def health_check() -> Response:
    """
    Endpoint to health check API
    """
    app.logger.info("Health Check!")
    return Response("All Good!", status=200)
