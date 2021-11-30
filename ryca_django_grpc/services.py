from functools import update_wrapper

import grpc
from django.db.models.query import QuerySet
from rest_framework.settings import api_settings

from ryca_django_grpc.signals import grpc_request_started, grpc_request_finished


class Service:
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def as_servicer(cls, **initkwargs):
        """
        Returns a gRPC servicer instance::
            servicer = PostService.as_servicer()
            add_PostControllerServicer_to_server(servicer, server)
        """
        for key in initkwargs:
            if not hasattr(cls, key):
                raise TypeError(
                    "%s() received an invalid keyword %r. as_servicer only "
                    "accepts arguments that are already attributes of the "
                    "class." % (cls.__name__, key)
                )
        if isinstance(getattr(cls, 'queryset', None), QuerySet):
            def force_evaluation():
                raise RuntimeError(
                    'Do not evaluate the `.queryset` attribute directly, '
                    'as the result will be cached and reused between requests.'
                    ' Use `.all()` or call `.get_queryset()` instead.'
                )

            cls.queryset._fetch_all = force_evaluation

        class Servicer:
            def __getattr__(self, action):
                if not hasattr(cls, action):
                    return not_implemented

                def handler(request, context):
                    grpc_request_started.send(sender=handler, request=request, context=context)
                    try:
                        self = cls(**initkwargs)
                        self.request = request
                        self.context = context
                        self.action = action
                        return getattr(self, action)(request, context)
                    finally:
                        self.dispatch(request, context)
                        grpc_request_finished.send(sender=handler)

                update_wrapper(handler, getattr(cls, action))
                return handler

        update_wrapper(Servicer, cls, updated=())
        return Servicer()

    def initial(self, request, context):
        """
        Runs anything that needs to occur prior to calling the method handler.
        """

        if hasattr(self, 'permission_classes'):
            self.check_permissions(request, context)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        return [permission() for permission in self.permission_classes]

    def check_permissions(self, request, context):
        """
        Check if the request should be permitted.
        Raises an appropriate exception if the request is not permitted.
        """
        for permission in self.get_permissions():
            if not permission.has_permission(request, context):
                raise ValueError(grpc.StatusCode.UNAUTHENTICATED)

    def dispatch(self, request, context):
        """
        `.dispatch()` is pretty much the same as Django's regular dispatch,
        but with extra hooks for startup, finalize, and exception handling.
        """
        self.initial(request, context)


def not_implemented(request, context):
    """Method not implemented"""
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')
