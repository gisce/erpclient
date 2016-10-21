import simple_gtk
import service


def test_plugin(datas):
    parent = service.LocalService('gui.main').window

    resource = {
        'model': datas['model'],
        'res_id': datas['id']
    }

    app = simple_gtk.ApplicationWindow(resource, parent)
    return True