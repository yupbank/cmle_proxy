from __future__ import print_function
import argparse
from itertools import repeat

from grpc.beta import implementations
import tensorflow as tf

from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2


from tornado import gen
import tornado.web
from tornado.gen import Future
from tornado.ioloop import IOLoop
from tornado.options import define, options, parse_command_line

define("port", default=8888, help="run on the given port", type=int)
define("server_port", default=9000, help="serving on the given port", type=int)
define("server_address", default='localhost', help="serving on the given address", type=str)
define("debug", default=False, help="run in debug mode")

#### START code took from https://github.com/grpc/grpc/wiki/Integration-with-tornado-(python)

def _fwrap(f, gf):
    try:
        f.set_result(gf.result())
    except Exception as e:
        f.set_exception(e)


def fwrap(gf, ioloop=None):
    '''
        Wraps a GRPC result in a future that can be yielded by tornado
        
        Usage::
        
            @coroutine
            def my_fn(param):
                result = yield fwrap(stub.function_name.future(param, timeout))
        
    '''
    f = Future()

    if ioloop is None:
        ioloop = IOLoop.current()

    gf.add_done_callback(lambda _: ioloop.add_callback(_fwrap, f, gf))
    return f

#### END code took from https://github.com/grpc/grpc/wiki/Integration-with-tornado-(python)



class PredictHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def post(self, model, version=None):
        request_data = tornado.escape.json_decode(self.request.body)
        instances = request_data['instances']
        input_columns = instances[0].keys()
        stub = self.settings['settings']['stub']

        request = predict_pb2.PredictRequest()
        request.model_spec.name = model
        if version is not None:
            request.model_spec.version = version
        
        for input_column in input_columns:
            values = [instance[input_column] for instance in instances]
            request.inputs[input_column].CopyFrom(tf.make_tensor_proto(values, shape=[len(values)]))

        result = yield fwrap(stub.Predict.future(request, self.settings['settings']['grpc_timeout']))
        output_keys = result.outputs.keys()
        predictions = zip(*[tf.make_ndarray(result.outputs[output_key]).tolist() for output_key in output_keys])
        predictions = [dict(zip(*t)) for t in zip(repeat(output_keys), predictions)]
        self.write(dict(predictions=predictions))

    get = post

class IndexHanlder(tornado.web.RequestHandler):
    def get(self):
        self.write('Hello World')


class StatusHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('ok')


def main():
    parse_command_line()

    channel = implementations.insecure_channel(options.server_address, options.server_port)
    stub = prediction_service_pb2.beta_create_PredictionService_stub(channel)

    app = tornado.web.Application(
        [
            (r"/model/(.*):predict", PredictHandler),
            (r"/model/(.*)/version/(.*):predict", PredictHandler),
            (r"/", IndexHanlder),
            (r"/status", StatusHandler),
            ],
        cookie_secret="sadaswqds89sa9daasdasdadasd9",
        xsrf_cookies=False,
        debug=options.debug,
        settings = dict(
		stub = stub,
        grpc_timeout = 1.0
		)
        )
    app.listen(options.port)
    print('running at http://localhost:%s'%options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
