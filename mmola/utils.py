import functools


def audit(audit_code, **params):
    def decorator_audit(func):
        @functools.wraps(func)
        def wrapper_audit(*args, **kwargs):
            # Audit
            return func(*args, **kwargs)
        return wrapper_audit
    return decorator_audit
