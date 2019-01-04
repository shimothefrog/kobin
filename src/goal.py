from app import App, Response, JSONResponse
from wsgiref.simple_server import make_server

app = App()

@app.route('^/$')
def index(request):
    return Response('Hello World')


@app.route('^/users/(?P<user_id>\d+)/$')
def user_detail(request, user_id):
    data = {'user': user_id}
    return JSONResponse(data, indent=4)

if __name__ == '__main__':
    httpd = make_server('', 8000, app)
    httpd.serve_forever()
