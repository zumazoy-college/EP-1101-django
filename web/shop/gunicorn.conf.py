from prometheus_client import multiprocess


def child_exit(server, worker):
    # Убираем live-gauge завершившегося воркера, счётчики остаются в PROMETHEUS_MULTIPROC_DIR
    multiprocess.mark_process_dead(worker.pid)
