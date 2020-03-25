from django.contrib.auth.decorators import login_required
class LoginRequiredMixin(object):
    '''登录验证装饰器累'''
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin,cls).as_view(**initkwargs)
        return login_required(view)
