import errno
import logging
import subprocess
import threading
import time

from haproxy.config import HAPROXY_RUN_COMMAND, RELOAD_TIMEOUT, HAPROXY_CONFIG_CHECK_COMMAND

logger = logging.getLogger("haproxy")


# RELOAD_TIMEOUT has the following values and effect:
# -1 : Reload haproxy with "-st" which will immediately kill the previous process
# 0 : Reload haproxy with "-sf" and no timeout.  This can potentially leave 
#     "broken" processes (where the backends have changed) hanging around 
#     with existing connections.
# > 0 : Reload haproxy with "-sf" but if it takes longer than RELOAD_TIMEOUT then kill it
#       This gives existing connections a chance to finish.  RELOAD_TIMEOUT should be set to 
#       the approximate time it takes docker to finish updating services.  By this point the
#       existing configuration will be invalid, and any connections still using it will 
#       have invalid backends.
#
def run_reload(timeout=int(RELOAD_TIMEOUT)):
    p = subprocess.Popen("/reload.sh", shell=True, executable="/bin/sh")
    output, err = p.communicate()

    if p.returncode != 0:
        logger.error("Reload fails: %s - %s" % (err, output))
    else:
        logger.info("Reload complete!")


def wait_pid(process, timeout):
    start = time.time()

    timer = None

    if timeout > 0:
        timer = threading.Timer(timeout, timeout_handler, [process])
        timer.start()

    process.wait()

    if timer is not None:
        timer.cancel();

    duration = time.time() - start
    logger.info("Old HAProxy(PID: %s) ended after %s sec", str(process.pid), str(duration))


def timeout_handler(processs):
    if processs.poll() is None:
        try:
            processs.terminate()
            logger.info("Old HAProxy process taking too long to complete - terminating")
        except OSError as e:
            if e.errno != errno.ESRCH:
                raise
