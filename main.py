import web

urls = (
    '/', 'Index'
)

class Index:
    def GET(self):
        render = web.template.render('templates')
        return render.index()

if __name__ == '__main__':
    app = web.application(urls, globals())
    app.run()