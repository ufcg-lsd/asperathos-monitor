import traceback
import flask
from werkzeug import datastructures

from logger import *
from utils import *


LOG = Log("Monitor_UtilsAPI", "Monitor_utilsapi.log")


class Rest(flask.Blueprint):
    def get(self, rule, status_code=200):
        return self._mroute('GET', rule, status_code)

    def post(self, rule, status_code=202):
        return self._mroute('POST', rule, status_code)

    def post_file(self, rule, status_code=202):
        return self._mroute('POST', rule, status_code, file_upload=True)

    def put(self, rule, status_code=202):
        return self._mroute('PUT', rule, status_code)

    def put_file(self, rule, status_code=202):
        return self._mroute('PUT', rule, status_code, file_upload=True)

    def delete(self, rule, status_code=204):
        return self._mroute('DELETE', rule, status_code)

    def patch(self, rule, status_code=202):
        return self._mroute('PATCH', rule, status_code)

    def _mroute(self, methods, rule, status_code=None, **kw):
        if type(methods) is str:
            methods = [methods]
        return self.route(rule, methods=methods, status_code=status_code, **kw)

    def route(self, rule, **options):
        status = options.pop('status_code', None)
        file_upload = options.pop('file_upload', False)

        def decorator(func):
            endpoint = options.pop('endpoint', func.__name__)

            def handler(**kwargs):
                LOG.log("Rest.route.decorator.handler, kwargs={kwargs}".format(
                    kwargs=kwargs))

                _init_resp_type(file_upload)

                # update status code
                if status:
                    flask.request.status_code = status

                try:
                    if flask.request.method in ['POST', 'PUT', 'PATCH']:
                        kwargs['data'] = request_data()
                    return func(**kwargs)
                except Exception as e:
                    return internal_error(500, 'Internal Server Error', e)

            self.add_url_rule(rule, endpoint, handler, **options)
            self.add_url_rule(rule + '.json', endpoint, handler, **options)

            return func

        return decorator


RT_JSON = datastructures.MIMEAccept([("application/json", 1)])


def _init_resp_type(file_upload):
    """Extracts response content type."""

    # get content type from Accept header
    resp_type = flask.request.accept_mimetypes

    # url /foo.json
    if flask.request.path.endswith('.json'):
        resp_type = RT_JSON

    flask.request.resp_type = resp_type

    # set file upload flag
    flask.request.file_upload = file_upload


def render(res=None, resp_type=None, status=None, **kwargs):
    if not res:
        res = {}
    if type(res) is dict:
        res.update(kwargs)
    elif kwargs:
        # can't merge kwargs into the non-dict res
        abort_and_log(500,
                      "Non-dict and non-empty kwargs passed to render")

    status_code = getattr(flask.request, 'status_code', None)
    if status:
        status_code = status
    if not status_code:
        status_code = 200

    if not resp_type:
        resp_type = getattr(flask.request, 'resp_type', RT_JSON)

    if not resp_type:
        resp_type = RT_JSON

    serializer = None
    if "application/json" in resp_type:
        resp_type = RT_JSON
        serializer = JSONDictSerializer()
    else:
        abort_and_log(400, "Content type '%s' isn't supported" % resp_type)

    body = serializer.serialize(res)
    resp_type = str(resp_type)

    return flask.Response(response=body, status=status_code,
                          mimetype=resp_type)


def request_data():
    if hasattr(flask.request, 'parsed_data'):
        return flask.request.parsed_data

    if not flask.request.content_length > 0:
        LOG.log("Empty body provided in request")
        return dict()

    if flask.request.file_upload:
        return flask.request.data

    deserializer = None
    content_type = flask.request.mimetype
    if not content_type or content_type in RT_JSON:
        deserializer = JSONDeserializer()
    else:
        abort_and_log(400,
                      "Content type '%s' isn't supported" % content_type)

    # parsed request data to avoid unwanted re-parsings
    parsed_data = deserializer.deserialize(flask.request.data)['body']
    flask.request.parsed_data = parsed_data


def get_request_args():
    return flask.request.args


def abort_and_log(status_code, descr, exc=None):
    LOG.log("Request aborted with status code {code} and "
            "message '{message}'").format(code=status_code, message=descr)

    if exc is not None:
        LOG.log(traceback.format_exc())

    flask.abort(status_code, description=descr)


def render_error_message(error_code, error_message, error_name):
    message = {
        "error_code": error_code,
        "error_message": error_message,
        "error_name": error_name
    }

    resp = render(message)
    resp.status_code = error_code

    return resp


def internal_error(status_code, descr, exc=None):
    LOG.log(descr)
# .format(code=status_code, message=descr)

    if exc is not None:
        LOG.log(traceback.format_exc())

    error_code = "INTERNAL_SERVER_ERROR"
    if status_code == 501:
        error_code = "NOT_IMPLEMENTED_ERROR"

    return render_error_message(status_code, descr, error_code)


def bad_request(error):
    error_code = 400

    LOG.log("Validation Error occurred: "
            "error_code={code}, error_message={message}, "
            "error_name={name}").format(code=error_code,
                                        message=error.message,
                                        name=error.code)

    return render_error_message(error_code, error.message, error.code)


def access_denied(error):
    error_code = 403

    LOG.log("Access Denied: "
            "error_code={code}, error_message={message}, "
            "error_name={name}").format(code=error_code,
                                        message=error.message,
                                        name=error.code)

    return render_error_message(error_code, error.message, error.code)


def not_found(error):
    error_code = 404

    LOG.log("Not Found exception occurred: "
            "error_code={code}, error_message={message}, "
            "error_name={name}").format(code=error_code,
                                        message=error.message,
                                        name=error.code)

    return render_error_message(error_code, error.message, error.code)