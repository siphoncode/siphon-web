import os
import subprocess
import atexit
import signal

from django.conf import settings
from django.contrib.staticfiles.management.commands.runserver import Command as RunserverCommand


def kill_grunt_process(pid):
    print('>>> Closing grunt process')
    os.kill(pid, signal.SIGTERM)

class Command(RunserverCommand):
    def inner_run(self, *args, **options):
        self.start_grunt()
        return super(Command, self).inner_run(*args, **options)

    def start_grunt(self):
        print('>>> Starting grunt')
        fil = os.path.join(settings.BASE_DIR, '../Gruntfile.js')
        self._proc = subprocess.Popen(
            ['./node_modules/grunt-cli/bin/grunt --gruntfile %s' % fil],
            shell=True,
            stdin=subprocess.PIPE,
            stdout=self.stdout,
            stderr=self.stderr,
        )
        try:
            out, errs = self._proc.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            pass

        if self._proc.poll() is not None:
            print('>>> Grunt failed to run!')
            os._exit(1)

        print('>>> Grunt process on pid %s' % self._proc.pid)
        atexit.register(kill_grunt_process, self._proc.pid)
