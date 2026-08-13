# Flag global de enforcement do Kernel
KERNEL_ENFORCEMENT = True

def enforce_kernel():
    if not KERNEL_ENFORCEMENT:
        return
    import inspect
    stack = inspect.stack()
    # Permite execução apenas se chamada pelo Kernel
    for frame in stack:
        if 'runtime_kernel' in frame.filename:
            return
    raise Exception('Execution outside Kernel is forbidden')
