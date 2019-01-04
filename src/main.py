from apps import App, Response, TemplateResponse, JSONResponse
from wsgiref.simple_server import make_server


app = App()


@app.route('^/$', 'GET')
def hello(request):
    return Response('Hello World')


@app.route('^/user/$', 'POST')
def create_user(request):
    return Response('User created', status=201)


@app.route('^/user/(?P<name>\w+)/$', 'GET')
def user_detail(request, name):
    return Response('Hello {name}'.format(name=name))


@app.route('^/user/(?P<name>\w+)/follow/$', 'POST')
def create_user(name):
    return JSONResponse({'message': 'User Created.'}, status=201)


@app.route('^/user/$', 'GET')
def users(request):
    users_list = ['user%s' % i for i in range(10)]
    return TemplateResponse('users.html', titile='User List', users=users_list)


if __name__ == '__main__':
    httpd = make_server('', 8000, app)
    httpd.serve_forever()
